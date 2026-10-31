"""Native engine-adapter contracts; fake executables are not real Podman/Docker runs."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('lg_engine_adapter', ROOT / 'python/looking_glass_test_container.py')
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


@pytest.fixture
def engines(tmp_path, monkeypatch):
    binaries = tmp_path / 'engine bin'
    binaries.mkdir()
    calls = tmp_path / 'calls.jsonl'
    program = f"""#!{sys.executable}
import json,os,sys
from pathlib import Path
with Path(os.environ['ENGINE_CALLS']).open('a') as stream:
    stream.write(json.dumps(dict(argv=sys.argv,cwd=os.getcwd(),stdin=sys.stdin.read()))+'\\n')
print('fake engine output')
print('fake engine stderr',file=sys.stderr)
raise SystemExit(7 if os.environ.get('ENGINE_FAIL') == sys.argv[1] else 0)
"""
    for name in ('podman', 'docker'):
        path = binaries / name
        path.write_text(program)
        path.chmod(0o700)
    monkeypatch.setenv('PATH', str(binaries))
    monkeypatch.setenv('ENGINE_CALLS', str(calls))
    monkeypatch.delenv('ENGINE_FAIL', raising=False)
    monkeypatch.delenv('LG_CONTAINER_ENGINE', raising=False)
    return binaries, calls


def test_auto_prefers_podman_and_runs_native_executable_without_shell(engines, tmp_path):
    binaries, calls = engines
    engine = adapter.select_engine()
    assert engine.name == 'podman' and engine.executable == str(binaries / 'podman')
    result = engine.run(tmp_path / 'evidence', 'run', 'value with spaces;$(not-a-shell)')
    assert result.returncode == 0 and result.stdout == 'fake engine output\n'
    payload = json.loads(calls.read_text())
    assert payload['argv'] == [str(binaries / 'podman'), 'run', 'value with spaces;$(not-a-shell)']
    assert payload['cwd'] == str(adapter.ROOT) and payload['stdin'] == ''
    log = (tmp_path / 'evidence/podman.log').read_text()
    assert 'exit=0' in log and 'fake engine stderr' in log


@pytest.mark.parametrize('name', ['podman', 'docker'])
def test_explicit_engine_preflight_records_selection_version_and_info(engines, tmp_path, monkeypatch, name):
    binaries, calls = engines
    monkeypatch.setenv('LG_CONTAINER_ENGINE', name)
    engine = adapter.select_engine()
    evidence = tmp_path / 'evidence'
    engine.preflight(evidence)
    selection = json.loads((evidence / 'engine.json').read_text())
    assert selection == dict(engine=name, executable=str(binaries / name))
    assert [json.loads(line)['argv'][1:] for line in calls.read_text().splitlines()] == [['version'], ['info']]
    assert (evidence / (name + '.log')).is_file()


def test_auto_uses_docker_only_when_podman_binary_is_missing(engines):
    binaries, _ = engines
    (binaries / 'podman').unlink()
    assert adapter.select_engine().name == 'docker'


@pytest.mark.parametrize('selection', ['podman', 'docker', 'auto'])
def test_missing_engine_is_failure(engines, selection):
    binaries, _ = engines
    for path in binaries.iterdir():
        path.unlink()
    with pytest.raises(RuntimeError, match='No selected container engine'):
        adapter.select_engine(selection)


def test_explicit_missing_podman_does_not_fall_back_to_docker(engines):
    binaries, _ = engines
    (binaries / 'podman').unlink()
    with pytest.raises(RuntimeError, match='podman'):
        adapter.select_engine('podman')


@pytest.mark.parametrize('selection', ['', 'podman --remote', '/usr/bin/podman', 'shell', 1])
def test_invalid_selection_is_rejected(selection):
    with pytest.raises(ValueError, match='LG_CONTAINER_ENGINE'):
        adapter.select_engine(selection)


@pytest.mark.parametrize('operation', ['version', 'info'])
def test_unusable_podman_fails_without_docker_fallback(engines, tmp_path, monkeypatch, operation):
    _, calls = engines
    monkeypatch.setenv('ENGINE_FAIL', operation)
    engine = adapter.select_engine()
    with pytest.raises(AssertionError, match='podman command failed'):
        engine.preflight(tmp_path / 'evidence')
    assert all(Path(json.loads(line)['argv'][0]).name == 'podman' for line in calls.read_text().splitlines())
    assert 'exit=7' in (tmp_path / 'evidence/podman.log').read_text()


def test_nonzero_cleanup_is_logged_when_check_false(engines, tmp_path, monkeypatch):
    monkeypatch.setenv('ENGINE_FAIL', 'rm')
    result = adapter.select_engine('docker').run(tmp_path, 'rm', 'owned-name', check=False)
    assert result.returncode == 7 and 'exit=7' in (tmp_path / 'docker.log').read_text()


@pytest.mark.parametrize('error', [OSError('injected exec failure'), subprocess.TimeoutExpired(['podman'], 1)])
def test_execution_errors_are_logged_and_propagated(tmp_path, monkeypatch, error):
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(adapter.subprocess, 'run', fail)
    with pytest.raises(type(error)):
        adapter.Engine('podman', '/nonexistent/podman').run(tmp_path, 'info')
    assert 'info' in (tmp_path / 'podman.log').read_text()


@pytest.mark.parametrize('name', ['podman', 'docker'])
def test_private_config_mount_is_readonly_and_podman_relabels_only_file(tmp_path, name):
    config = tmp_path / 'config with spaces.json'
    config.write_text('{}')
    args = adapter.Engine(name, '/bin/' + name).config_mount(config)
    if name == 'podman':
        assert args == ['--volume', f'{config}:/app/ci-config.json:ro,Z']
    else:
        assert args == ['--mount', f'type=bind,source={config},target=/app/ci-config.json,readonly']
    assert 'label=disable' not in str(args) and ':U' not in str(args)
    assert config.read_text() == '{}'
    alias = tmp_path / 'alias'
    alias.symlink_to(config)
    with pytest.raises(ValueError, match='private regular file'):
        adapter.Engine(name, '/bin/' + name).config_mount(alias)


def valid_info():
    return {'NetworkSettings': {'Ports': {
        '5000/tcp': [{'HostIp':'127.0.0.1','HostPort':'34567'}],
        '5100/tcp': [{'HostIp':'127.0.0.1','HostPort':34568}],
    }}}


def test_published_urls_keep_two_distinct_loopback_listeners():
    assert adapter.published_urls(valid_info()) == ['http://127.0.0.1:34567','http://127.0.0.1:34568']


@pytest.mark.parametrize('bindings', [None, [], [{}, {}], [{}],
    [{'HostIp':'0.0.0.0','HostPort':'1234'}],
    [{'HostIp':'127.0.0.1','HostPort':'bad'}],
    [{'HostIp':'127.0.0.1','HostPort':'0'}],
    [{'HostIp':'127.0.0.1','HostPort':'65536'}],
    [{'HostIp':'127.0.0.1','HostPort':True}]])
def test_invalid_or_nonloopback_bindings_are_not_tolerated(bindings):
    info = copy.deepcopy(valid_info())
    info['NetworkSettings']['Ports']['5000/tcp'] = bindings
    with pytest.raises(ValueError):
        adapter.published_urls(info)


def test_missing_inspect_structure_is_not_success():
    for info in ({}, None, {'NetworkSettings': {}}):
        with pytest.raises(ValueError):
            adapter.published_urls(info)


def test_listener_port_collision_is_rejected():
    info = valid_info()
    info['NetworkSettings']['Ports']['5100/tcp'][0]['HostPort'] = '34567'
    with pytest.raises(ValueError, match='distinct'):
        adapter.published_urls(info)


@pytest.mark.parametrize('name,expected', [('podman',['--pull=always']),('docker',['--pull'])])
def test_build_pull_flags_use_native_engine_syntax(name, expected):
    assert adapter.Engine(name, '/bin/' + name).build_pull_args() == expected


def test_podman_only_installation_preflight_does_not_require_docker(engines, tmp_path):
    binaries, calls = engines
    (binaries / 'docker').unlink()
    engine = adapter.select_engine()
    assert engine.name == 'podman'
    engine.preflight(tmp_path / 'evidence')
    assert [json.loads(line)['argv'][1] for line in calls.read_text().splitlines()] == ['version','info']
