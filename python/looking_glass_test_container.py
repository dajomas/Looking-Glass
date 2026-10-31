"""Test-only native container-engine adapter; no application imports or daemon fallback."""
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


class Engine:
    def __init__(self, name, executable):
        if name not in ('podman', 'docker'):
            raise ValueError('Engine must be podman or docker')
        self.name = name
        self.executable = str(Path(executable).resolve())

    def run(self, evidence, *arguments, timeout=60, check=True):
        evidence = Path(evidence)
        evidence.mkdir(parents=True, exist_ok=True)
        log = evidence / (self.name + '.log')
        command = [self.executable, *arguments]
        try:
            result = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                capture_output=True, text=True, timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            with log.open('a', encoding='utf-8') as stream:
                stream.write(f'{command!r}\n{exc!r}\n')
            raise
        with log.open('a', encoding='utf-8') as stream:
            stream.write(f'{command!r}\nexit={result.returncode}\n{result.stdout}\n{result.stderr}\n')
        if check and result.returncode:
            raise AssertionError(f'{self.name} command failed: {arguments[0] if arguments else "(none)"}; see {log}')
        return result

    def preflight(self, evidence):
        evidence = Path(evidence)
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / 'engine.json').write_text(json.dumps(
            dict(engine=self.name, executable=self.executable), indent=2) + '\n', encoding='utf-8')
        self.run(evidence, 'version')
        self.run(evidence, 'info')

    def build_pull_args(self):
        return ['--pull=always'] if self.name == 'podman' else ['--pull']

    def config_mount(self, config):
        config = Path(config)
        if config.is_symlink() or not config.is_file():
            raise ValueError('Config must be a private regular file, not a symlink')
        config = config.resolve()
        if self.name == 'podman':
            # Relabel only the disposable file; do not disable SELinux or chown host trees.
            return ['--volume', f'{config}:/app/ci-config.json:ro,Z']
        return ['--mount', f'type=bind,source={config},target=/app/ci-config.json,readonly']


def select_engine(selection=None):
    if selection is None:
        selection = os.environ.get('LG_CONTAINER_ENGINE', 'auto')
    if not isinstance(selection, str) or selection not in ('auto', 'podman', 'docker'):
        raise ValueError('LG_CONTAINER_ENGINE must be auto, podman or docker')
    choices = ('podman', 'docker') if selection == 'auto' else (selection,)
    for name in choices:
        executable = shutil.which(name)
        if executable:
            return Engine(name, executable)
    raise RuntimeError(f'No selected container engine available ({selection}); install/configure Podman or Docker')


def published_urls(info):
    try:
        ports = info['NetworkSettings']['Ports']
        urls = []
        for key in ('5000/tcp', '5100/tcp'):
            bindings = ports[key]
            if not isinstance(bindings, list) or len(bindings) != 1:
                raise ValueError('Expected one loopback binding per listener')
            binding = bindings[0]
            raw = binding['HostPort']
            if binding['HostIp'] != '127.0.0.1' or type(raw) not in (str, int):
                raise ValueError('Expected explicit IPv4 loopback binding')
            port = str(raw)
            if not port.isascii() or not port.isdecimal() or not 1 <= int(port) <= 65535:
                raise ValueError('Invalid published port')
            urls.append('http://127.0.0.1:' + str(int(port)))
        if len(set(urls)) != 2:
            raise ValueError('Listener ports must be distinct')
        return urls
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError('Missing or invalid published listener bindings') from exc
