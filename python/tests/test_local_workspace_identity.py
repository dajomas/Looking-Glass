"""Real-helper revision identity regressions; no stub workspace implementation."""
import importlib.util
import json
import os
import sys
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("workspace_identity", ROOT / "tools/local_test_workspace.py")
workspace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workspace)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Workspace regression")
    git(root, "config", "user.email", "workspace@example.invalid")
    git(root, "config", "commit.gpgsign", "false")
    (root / "source.txt").write_text("committed")
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture")
    return root, git(root, "rev-parse", "HEAD")


@pytest.mark.parametrize("abbreviated", [False, True])
def test_real_prepare_accepts_full_and_short_identity(source, tmp_path, abbreviated):
    root, full = source
    requested = git(root, "rev-parse", "--short=7", full) if abbreviated else full
    evidence = tmp_path / "evidence"
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    work = workspace.prepare(root, requested, evidence, scratch_root)
    try:
        assert git(work, "rev-parse", "HEAD") == full
        assert Path(git(work, "rev-parse", "--show-toplevel")) == work
        assert (work / "source.txt").read_text() == "committed"
        assert json.loads((evidence / "workspace.json").read_text())["commit"] == full
        identity = json.loads((evidence / "workspace-identity.json").read_text())
        assert identity["requested"] == requested
        assert identity["expected"] == identity["actual"] == full
    finally:
        workspace.finalize(evidence)
    assert list(scratch_root.iterdir()) == []


def test_invalid_revision_never_allocates_scratch(source, tmp_path):
    root, _ = source
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    with pytest.raises(subprocess.CalledProcessError):
        workspace.prepare(root, "0" * 40, tmp_path / "evidence", scratch_root)
    assert list(scratch_root.iterdir()) == []


def test_genuine_mismatch_is_rejected_and_records_both_ids(source, tmp_path, monkeypatch):
    root, full = source
    requested = git(root, "rev-parse", "--short=7", full)
    wrong = full[:-1] + ("1" if full[-1] == "0" else "0")
    original = workspace.subprocess.check_output
    def read(command, *args, **kwargs):
        if command[-2:] == ["rev-parse", "HEAD"] and Path(command[2]) != root:
            return wrong + "\n"
        return original(command, *args, **kwargs)
    monkeypatch.setattr(workspace.subprocess, "check_output", read)
    evidence = tmp_path / "evidence"
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    with pytest.raises(RuntimeError, match="Workspace commit") as caught:
        workspace.prepare(root, requested, evidence, scratch_root)
    assert full in str(caught.value) and wrong in str(caught.value)
    identity = json.loads((evidence / "workspace-identity.json").read_text())
    assert (identity["requested"], identity["expected"], identity["actual"]) == (requested, full, wrong)
    assert not (evidence / "workspace.json").exists()
    assert list(scratch_root.iterdir()) == []


def test_real_cli_accepts_short_revision_and_records_full_commit(source, tmp_path):
    root, full = source
    requested = git(root, "rev-parse", "--short=7", full)
    evidence = tmp_path / "evidence"
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    helper = ROOT / "tools/local_test_workspace.py"
    env = dict(os.environ, LG_LOCAL_TEST_TMPDIR=str(scratch_root))
    result = subprocess.run([sys.executable, str(helper), "prepare", str(root), requested, str(evidence)],
                            env=env, capture_output=True, text=True, timeout=20)
    try:
        assert result.returncode == 0, result.stderr
        assert Path(result.stdout.strip()).is_dir()
        assert json.loads((evidence / "workspace.json").read_text())["commit"] == full
    finally:
        subprocess.run([sys.executable, str(helper), "finalize", str(evidence)],
                       env=env, capture_output=True, text=True, timeout=20, check=True)
    assert list(scratch_root.iterdir()) == []
