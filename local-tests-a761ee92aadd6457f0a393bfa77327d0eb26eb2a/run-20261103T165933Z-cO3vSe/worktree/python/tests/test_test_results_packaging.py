"""Evidence round trips and real Bash runner status tests with doubled test commands."""
import base64
import gzip
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('lg_test_packager', ROOT / 'tools/package_test_results.py')
packager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packager)


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def bundle_files(path):
    with tarfile.open(path, 'r:gz') as archive:
        return {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}


def test_nested_binary_spaces_hidden_files_and_empty_directories_roundtrip(tmp_path):
    results = tmp_path / 'test-results'
    (results / 'recovery/deep').mkdir(parents=True)
    (results / 'empty').mkdir()
    (results / 'python.log').write_bytes(b'pytest output\n')
    (results / '.environment').write_bytes(b'environment\n')
    (results / 'recovery/deep/server log.txt').write_bytes(b'nested output\n')
    (results / 'recovery/trace.zip').write_bytes(bytes(range(256)))
    before = tree(results)
    legacy, bundle = packager.package_results(results, tmp_path / 'test-results.abcdef0')
    assert gzip.decompress(base64.b64decode(legacy.read_bytes())) == b'pytest output\n'
    assert bundle_files(bundle) == {'test-results/' + name: value for name, value in before.items()}
    with tarfile.open(bundle, 'r:gz') as archive:
        assert archive.getmember('test-results/empty').isdir()
        assert all(not m.name.startswith('/') and '..' not in Path(m.name).parts for m in archive.getmembers())
    assert tree(results) == before
    assert not list(tmp_path.glob('.lg-test-package-*'))


def test_existing_legacy_decoding_contract_is_preserved(tmp_path):
    results = tmp_path / 'test-results'
    results.mkdir()
    for name, value in [('a.log', b'A\n'), ('b.log', b'B\n')]:
        (results / name).write_bytes(value)
    (results / '.hidden').write_bytes(b'hidden diagnostics')
    old = subprocess.run(['bash', '-c', 'set -o pipefail; gzip -c test-results/* | base64'],
                         cwd=tmp_path, capture_output=True, timeout=10)
    assert old.returncode == 0, old.stderr
    legacy, _ = packager.package_results(results, tmp_path / 'result')
    assert gzip.decompress(base64.b64decode(legacy.read_bytes())) == gzip.decompress(base64.b64decode(old.stdout))


def test_empty_tree_is_valid(tmp_path):
    results = tmp_path / 'test-results'
    results.mkdir()
    legacy, bundle = packager.package_results(results, tmp_path / 'result')
    assert gzip.decompress(base64.b64decode(legacy.read_bytes())) == b''
    assert bundle_files(bundle) == {}
    with tarfile.open(bundle, 'r:gz') as archive:
        assert archive.getmember('test-results').isdir()


@pytest.mark.parametrize('kind', ['file-link', 'directory-link', 'dangling-link', 'fifo'])
def test_unsupported_entries_fail_without_reading_external_data(tmp_path, kind):
    results = tmp_path / 'test-results'
    results.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (outside / 'secret').write_bytes(b'not evidence')
    link = results / 'unsafe'
    if kind == 'file-link':
        link.symlink_to(outside / 'secret')
    elif kind == 'directory-link':
        link.symlink_to(outside, target_is_directory=True)
    elif kind == 'dangling-link':
        link.symlink_to(outside / 'missing')
    else:
        os.mkfifo(link)
    assert packager.main([str(results), str(tmp_path / 'result')]) == 1
    assert not (tmp_path / 'result.txt').exists()
    assert not (tmp_path / 'result.diagnostics.tar.gz').exists()
    assert (outside / 'secret').read_bytes() == b'not evidence'


def test_output_inside_source_and_symlink_source_are_rejected(tmp_path):
    results = tmp_path / 'test-results'
    results.mkdir()
    with pytest.raises(ValueError, match='outside'):
        packager.package_results(results, results / 'result')
    alias = tmp_path / 'alias'
    alias.symlink_to(results, target_is_directory=True)
    with pytest.raises(ValueError, match='non-symlink'):
        packager.package_results(alias, tmp_path / 'result')


def test_preparation_failure_keeps_previous_products_and_cleans_temporaries(tmp_path, monkeypatch):
    results = tmp_path / 'test-results'
    results.mkdir()
    (results / 'python.log').write_bytes(b'new logs')
    legacy = tmp_path / 'result.txt'
    bundle = tmp_path / 'result.diagnostics.tar.gz'
    legacy.write_bytes(b'old legacy')
    bundle.write_bytes(b'old bundle')
    def fail(*args, **kwargs):
        raise OSError('injected archive preparation failure')
    monkeypatch.setattr(packager.tarfile, 'open', fail)
    assert packager.main([str(results), str(tmp_path / 'result')]) == 1
    assert legacy.read_bytes() == b'old legacy' and bundle.read_bytes() == b'old bundle'
    assert not list(tmp_path.glob('.lg-test-package-*'))


def run_fixture(tmp_path, failing=''):
    checkout = tmp_path / 'checkout'
    (checkout / 'tools').mkdir(parents=True)
    (checkout / 'python/tests').mkdir(parents=True)
    (checkout / 'runtests.sh').write_bytes((ROOT / 'runtests.sh').read_bytes())
    (checkout / 'tools/package_test_results.py').write_bytes((ROOT / 'tools/package_test_results.py').read_bytes())
    (checkout / 'python/tests/test_fixture.js').write_text('// runner fixture')
    binaries = tmp_path / 'bin'
    binaries.mkdir()
    python = binaries / 'python'
    python.write_text("""#!/usr/bin/env bash
if [[ "$1" == tools/package_test_results.py ]]; then
  [[ "${FAKE_FAIL:-}" == packaging ]] && exit 9
  exec "$REAL_PYTHON" "$@"
fi
if [[ "$1" == -u ]]; then
  echo preflight
  [[ "${FAKE_FAIL:-}" == preflight ]] && exit 9
  exit 0
fi
suite=python
[[ " $* " == *' python/tests/browser '* ]] && suite=browser
[[ " $* " == *' python/tests/live_e2e '* ]] && suite=live
mkdir -p test-results/recovery
printf 'nested diagnostics\\n' > 'test-results/recovery/server log.txt'
echo "suite=$suite"
[[ "${FAKE_FAIL:-}" == "$suite" ]] && exit 9
exit 0
""")
    node = binaries / 'node'
    node.write_text('#!/usr/bin/env bash\necho javascript\n[[ "${FAKE_FAIL:-}" == node ]] && exit 9\nexit 0\n')
    git = binaries / 'git'
    git.write_text('#!/usr/bin/env bash\nprintf "abcdef0\\n"\n')
    for executable in (python, node, git):
        executable.chmod(0o700)
    env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ['PATH'],
               REAL_PYTHON=sys.executable, VIRTUAL_ENV=str(tmp_path / 'active-environment'),
               LG_RUN_LIVE_E2E='1', FAKE_FAIL=failing)
    run = subprocess.run(['bash', str(checkout / 'runtests.sh')], cwd=tmp_path,
                         env=env, capture_output=True, text=True, timeout=15)
    return checkout, run


def test_runner_success_packages_nested_diagnostics_without_gzip_warnings(tmp_path):
    checkout, run = run_fixture(tmp_path)
    assert run.returncode == 0, (run.stdout, run.stderr)
    assert 'is a directory' not in run.stderr and 'gzip:' not in run.stderr
    bundle = checkout / 'test-results.abcdef0.diagnostics.tar.gz'
    assert bundle_files(bundle)['test-results/recovery/server log.txt'] == b'nested diagnostics\n'
    decoded = gzip.decompress(base64.b64decode((checkout / 'test-results.abcdef0.txt').read_bytes()))
    assert b'suite=python' in decoded and b'javascript' in decoded and b'suite=live' in decoded


@pytest.mark.parametrize('stage', ['python', 'node', 'preflight', 'browser', 'live'])
def test_runner_preserves_each_test_stage_failure_after_packaging(tmp_path, stage):
    checkout, run = run_fixture(tmp_path, stage)
    assert run.returncode == 1, (stage, run.stdout, run.stderr)
    assert (checkout / 'test-results.abcdef0.txt').is_file()
    assert (checkout / 'test-results.abcdef0.diagnostics.tar.gz').is_file()


def test_runner_packaging_failure_is_not_success(tmp_path):
    checkout, run = run_fixture(tmp_path, 'packaging')
    assert run.returncode == 1, (run.stdout, run.stderr)
    assert not (checkout / 'test-results.abcdef0.diagnostics.tar.gz').exists()
