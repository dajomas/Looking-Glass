"""Real Bash/Git publication regressions with stubbed application test commands."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / "checkout with spaces"
    root.mkdir()
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    git(root, "init", "-q", "-b", "features/perplexity")
    git(root, "config", "user.name", "Runner harness")
    git(root, "config", "user.email", "runner@example.invalid")
    git(root, "config", "commit.gpgsign", "false")
    (root / "runlocaltests.sh").write_bytes((ROOT / "runlocaltests.sh").read_bytes())
    (root / "tools").mkdir()
    (root / ".gitignore").write_text("/local-tests-*/\n")
    helper = root / "tools/local_test_workspace.py"
    helper.write_text("""import json,os,pathlib,subprocess,sys,tempfile,shutil
command=sys.argv[1]
if command=='prepare':
 source,commit,output=sys.argv[2:]
 assert commit==subprocess.check_output(['git','-C',source,'rev-parse','HEAD'],text=True).strip()
 assert len(commit)==40
 if os.environ.get('STUB_SETUP_FAIL')=='1': raise SystemExit(9)
 work=pathlib.Path(tempfile.mkdtemp(dir=output,prefix='stub-work-'))
 (pathlib.Path(output)/'workspace.json').write_text(json.dumps({'worktree':str(work),'commit':commit}))
 print(work)
else:
 output=pathlib.Path(sys.argv[2]);record=output/'workspace.json'
 if record.exists():
  shutil.rmtree(json.loads(record.read_text())['worktree'])
  (output/'finalized.txt').write_text('complete')
""")
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture")
    git(root, "remote", "add", "origin", str(remote))
    git(root, "push", "-q", "-u", "origin", "HEAD")
    commit = git(root, "rev-parse", "HEAD")
    fake = tmp_path / "stub-python"
    fake.write_text(f"""#!{sys.executable}
import os,pathlib,sys
if sys.argv[1:]==['--version'] or sys.argv[1]=='-' or sys.argv[1].endswith('local_test_workspace.py'):
 os.execv({sys.executable!r},[{sys.executable!r},*sys.argv[1:]])
report=pathlib.Path(next(a.split('=',1)[1] for a in sys.argv if a.startswith('--junitxml=')))
child='<failure message="stub failure"/>' if os.environ.get('STUB_TEST_FAIL')=='1' else ''
report.write_text('<testsuite><testcase name="stub">'+child+'</testcase></testsuite>')
print('stub application test output')
raise SystemExit(3 if child else 0)
""")
    fake.chmod(0o700)
    return root, remote, commit, fake


def run(fixture, *args, **changes):
    root, _, _, fake = fixture
    env = dict(os.environ, **changes)
    env.pop("STUB_SETUP_FAIL", None) if "STUB_SETUP_FAIL" not in changes else None
    env.pop("STUB_TEST_FAIL", None) if "STUB_TEST_FAIL" not in changes else None
    result = subprocess.run(["bash", str(root / "runlocaltests.sh"), "--suite", "python",
                             "--python", str(fake), *args], cwd=root.parent,
                            env=env, text=True, capture_output=True, timeout=30)
    runs = list(root.glob("local-tests-*/run-*"))
    assert len(runs) == 1, (result.stdout, result.stderr)
    return result, runs[0]


def remote_head(remote):
    return git(remote, "rev-parse", "refs/heads/features/perplexity")


def test_full_commit_identity_short_folder_and_no_publish(fixture):
    root, remote, commit, _ = fixture
    result, output = run(fixture, "--no-publish")
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert output.parent.name == "local-tests-" + git(root, "rev-parse", "--short=7", commit)
    assert json.loads((output / "workspace.json").read_text())["commit"] == commit
    assert f"commit={commit}\n" in (output / "environment.txt").read_text()
    assert (output / "finalized.txt").is_file()
    assert git(root, "rev-parse", "HEAD") == remote_head(remote) == commit
    assert git(root, "diff", "--cached", "--name-only") == ""


@pytest.mark.parametrize("failed", [False, True])
def test_publication_contains_finalized_evidence_and_preserves_test_status(fixture, failed):
    root, remote, commit, _ = fixture
    result, output = run(fixture, STUB_TEST_FAIL="1" if failed else "0")
    assert result.returncode == int(failed), (result.stdout, result.stderr)
    published = git(root, "rev-parse", "HEAD")
    assert published != commit and remote_head(remote) == published
    relative = output.relative_to(root).as_posix()
    names = git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", published).splitlines()
    assert names and all(name.startswith(relative + "/") for name in names)
    assert git(remote, "show", f"{published}:{relative}/finalized.txt") == "complete"
    assert git(remote, "show", f"{published}:{relative}/exit-code.txt") == str(int(failed))
    assert "finished_utc=" in git(remote, "show", f"{published}:{relative}/environment.txt")
    assert "[skip ci]" in git(root, "log", "-1", "--format=%s")
    assert not git(root, "diff", "--name-only"), "No evidence is changed after its commit"


def test_staged_changes_are_not_committed_or_pushed(fixture):
    root, remote, commit, _ = fixture
    (root / "unrelated.txt").write_text("do not commit")
    git(root, "add", "unrelated.txt")
    result, _ = run(fixture)
    assert result.returncode == 1
    assert git(root, "rev-parse", "HEAD") == remote_head(remote) == commit
    assert git(root, "diff", "--cached", "--name-only") == "unrelated.txt"


def test_other_branch_is_never_published(fixture):
    root, remote, commit, _ = fixture
    git(root, "checkout", "-qb", "other")
    result, _ = run(fixture)
    assert result.returncode == 1
    assert git(root, "symbolic-ref", "--short", "HEAD") == "other"
    assert remote_head(remote) == commit


def test_push_failure_is_nonzero_and_keeps_local_evidence_commit(fixture):
    root, remote, commit, _ = fixture
    hook = remote / "hooks/pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o700)
    result, output = run(fixture)
    assert result.returncode == 1
    assert git(root, "rev-parse", "HEAD") != commit and remote_head(remote) == commit
    assert (output / "finalized.txt").is_file()
    logs = list(output.parent.glob("publication-*.log"))
    assert len(logs) == 1 and "publication_exit=1" in logs[0].read_text()


def test_setup_failure_is_retained_but_not_published(fixture):
    root, remote, commit, _ = fixture
    result, output = run(fixture, STUB_SETUP_FAIL="1")
    assert result.returncode != 0
    assert git(root, "rev-parse", "HEAD") == remote_head(remote) == commit
    assert int((output / "exit-code.txt").read_text()) != 0
