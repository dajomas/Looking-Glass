"""Audit tracked executable dependencies without rewriting historical evidence."""
import ast
from pathlib import Path
import re
import subprocess

import httpx2
import pytest

ROOT = Path(__file__).resolve().parents[2]
OLD = 'http' + 'x'
IMPORT = re.compile(r'(?m)^\s*(?:import\s+' + OLD + r'(?:[.\s,]|$)|from\s+' + OLD + r'(?:[.\s]|$))')


def legacy_reference(path, text):
    if path.suffix == '.py':
        for node in ast.walk(ast.parse(text, filename=str(path))):
            if isinstance(node, ast.Import) and any(n.name.split('.')[0] == OLD for n in node.names):
                return True
            if isinstance(node, ast.ImportFrom) and (node.module or '').split('.')[0] == OLD:
                return True
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value == OLD or node.value.startswith(OLD + '.') or IMPORT.search(node.value):
                    return True
        return False
    if path.name.startswith('requirements'):
        return re.search(r'(?mi)^\s*' + OLD + r'\b', text) is not None
    return re.search(r'[\"\x27]' + OLD + r'[\"\x27]', text) is not None or re.search(r'(?m)\bpip(?:3)?\s+install[^\n]*\b' + OLD + r'\b', text) is not None


def test_no_legacy_http_client_dependency_in_tracked_active_files():
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True)
    findings = []
    checked = 0
    for name in result.stdout.decode().split('\0'):
        if not name:
            continue
        relative = Path(name)
        if relative.parts[0].startswith('ci-results-') or relative.parts[:2] in (('docs', 'handover'), ('docs', 'todo')):
            continue
        if relative.suffix not in ('.py', '.yml', '.yaml', '.toml', '.md', '.sh', '.ps1', '.bat') and not relative.name.startswith('requirements') and relative.name != 'Containerfile':
            continue
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            continue
        checked += 1
        if legacy_reference(relative, path.read_text(encoding='utf-8')):
            findings.append(name)
    assert checked > 0
    assert not findings, 'Legacy HTTP client dependencies remain: ' + ', '.join(findings)


@pytest.mark.parametrize('source', [
    f'import {OLD}',
    f'from {OLD} import Client',
    f'def delayed():\n    import {OLD}',
    f'import importlib\nclient = importlib.import_module({OLD!r})',
    f'CHILD = "import {OLD}\\nprint(1)"',
])
def test_audit_detects_direct_deferred_and_embedded_imports(source):
    assert legacy_reference(Path('example.py'), source)


def test_audit_allows_new_client_and_compatibility_alias():
    assert not legacy_reference(Path('example.py'), 'import httpx2 as ' + OLD)
    assert legacy_reference(Path('requirements-dev.txt'), OLD + '>=0.27\n')
    assert not legacy_reference(Path('requirements-dev.txt'), 'httpx2>=2.16.0\n')
    assert legacy_reference(Path('workflow.yml'), f'"{OLD}": "{OLD}"')
    assert not legacy_reference(Path('workflow.yml'), '"httpx2": "httpx2"')


def test_httpx2_surface_used_by_live_and_recovery_clients():
    cookies = httpx2.Cookies()
    with httpx2.Client(base_url='http://127.0.0.1', timeout=1, trust_env=False,
                       cookies=cookies, headers={'X-Test': 'client-surface'}) as client:
        assert callable(client.get) and callable(client.post)
        assert client.headers['X-Test'] == 'client-surface'
    assert issubclass(httpx2.HTTPError, Exception)
