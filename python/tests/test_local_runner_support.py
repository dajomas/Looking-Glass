"""Git-aware workspace and native recovery wiring; no real container execution."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("local_workspace", ROOT / "tools/local_test_workspace.py")
workspace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workspace)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.name", "Harness")
    git(root, "config", "user.email", "harness@example.invalid")
    (root / "tracked.txt").write_text("committed")
    for name in ("ci-results-old", "local-tests-old"):
        (root / name).mkdir()
        (root / name / "artifact.txt").write_text("historical")
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture")
    commit = git(root, "rev-parse", "HEAD")
    (root / "tracked.txt").write_text("dirty")
    (root / "untracked.txt").write_text("not committed")
    return root, commit


def test_workspace_has_exact_commit_and_independent_git_root(source, tmp_path):
    root, commit = source
    evidence = tmp_path / "evidence"
    work = workspace.prepare(root, commit, evidence)
    scratch = work.parent
    try:
        assert git(work, "rev-parse", "HEAD") == commit
        assert Path(git(work, "rev-parse", "--show-toplevel")) == work
        assert "tracked.txt" in git(work, "ls-files")
        assert (work / "tracked.txt").read_text() == "committed"
        assert not (work / "untracked.txt").exists()
        assert not (work / "ci-results-old").exists()
        assert not (work / "local-tests-old").exists()
        workspace.probe(scratch)
    finally:
        workspace.finalize(evidence)
    assert not scratch.exists()
    assert (root / "tracked.txt").read_text() == "dirty"


def test_finalize_retains_diagnostics_without_following_links_or_reading_fifo(source, tmp_path):
    root, commit = source
    evidence = tmp_path / "evidence"
    work = workspace.prepare(root, commit, evidence)
    diagnostics = work / "test-results"
    diagnostics.mkdir()
    (diagnostics / "server.log").write_text("evidence")
    (diagnostics / "external-link").symlink_to(root / "untracked.txt")
    os.mkfifo(diagnostics / "pipe")
    temporary = work.parent / "tmp/case"
    temporary.mkdir()
    (temporary / "player-0.png").write_bytes(b"image")
    (temporary / "private.db").write_bytes(b"omit")
    workspace.finalize(evidence)
    assert (evidence / "diagnostics/server.log").read_text() == "evidence"
    assert not (evidence / "diagnostics/external-link").exists()
    assert not (evidence / "diagnostics/pipe").exists()
    assert len(json.loads((evidence / "omitted-special-files.json").read_text())) == 2
    assert (evidence / "browser-diagnostics/case/player-0.png").read_bytes() == b"image"
    assert not (evidence / "browser-diagnostics/case/private.db").exists()


def test_bad_commit_fails_prepare_without_leaving_owned_workspace(source, tmp_path):
    root, _ = source
    scratch_root = tmp_path / "scratch"
    scratch_root.mkdir()
    with pytest.raises(subprocess.CalledProcessError):
        workspace.prepare(root, "0" * 40, tmp_path / "evidence", scratch_root)
    assert list(scratch_root.iterdir()) == []


def load_engine_functions(selection):
    path = ROOT / "python/tests/recovery/test_container.py"
    names = {"selected_engine", "docker", "built_image"}
    nodes = [n for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(nodes) == 3
    for node in nodes:
        node.decorator_list = []
    ns = dict(os=os, select_engine=selection, ROOT=ROOT, uuid=uuid)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), "exec"), ns)
    return ns


@pytest.mark.parametrize("ci,explicit,expected", [("", None, "auto"), ("true", None, "docker"),
                                                  ("true", "podman", "podman")])
def test_recovery_engine_selection_preserves_ci_default(monkeypatch, ci, explicit, expected):
    monkeypatch.setenv("CI", ci)
    if explicit is None:
        monkeypatch.delenv("LG_CONTAINER_ENGINE", raising=False)
    else:
        monkeypatch.setenv("LG_CONTAINER_ENGINE", explicit)
    selection = Mock()
    load_engine_functions(selection)["selected_engine"]()
    selection.assert_called_once_with(expected)


def test_recovery_build_uses_native_flags_and_keeps_owned_image_cleanup():
    engine = SimpleNamespace(preflight=Mock(), run=Mock(), build_pull_args=lambda: ["--pull=always"])
    ns = load_engine_functions(Mock(return_value=engine))
    build = ns["built_image"]()
    image = next(build)
    build.close()
    commands = [call.args[1:] for call in engine.run.call_args_list]
    assert commands[0][:2] == ("build", "--pull=always")
    assert commands[-1] == ("image", "rm", image)
    assert engine.run.call_args_list[-1].kwargs["check"] is False


def test_missing_engine_is_not_converted_to_skip_or_success():
    ns = load_engine_functions(Mock(side_effect=RuntimeError("No selected container engine")))
    with pytest.raises(RuntimeError, match="No selected"):
        next(ns["built_image"]())
