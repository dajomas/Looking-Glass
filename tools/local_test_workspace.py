"""Prepare a native, Git-aware local-test workspace and retain diagnostics safely."""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import uuid


def probe(directory):
    private = directory / "permission-probe"
    private.write_text("probe")
    private.chmod(0o600)
    try:
        if stat.S_IMODE(private.stat().st_mode) != 0o600:
            raise RuntimeError("Test scratch filesystem does not enforce POSIX permissions")
        fifo = directory / "fifo-probe"
        os.mkfifo(fifo)
        if not stat.S_ISFIFO(fifo.lstat().st_mode):
            raise RuntimeError("Test scratch filesystem does not support FIFOs")
        link = directory / "link-probe"
        link.symlink_to(private.name)
        if not link.is_symlink():
            raise RuntimeError("Test scratch filesystem does not support symlinks")
    finally:
        for name in ("permission-probe", "fifo-probe", "link-probe"):
            (directory / name).unlink(missing_ok=True)


def prepare(source, commit, evidence, scratch_root=None):
    source, evidence = Path(source).resolve(), Path(evidence).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    record = evidence / "workspace.json"
    if record.exists():
        raise ValueError("Workspace record already exists")
    requested = str(commit)
    commit = subprocess.check_output([
        "git", "-C", str(source), "rev-parse", "--verify", "--end-of-options",
        f"{requested}^{{commit}}",
    ], text=True).strip()
    scratch = Path(tempfile.mkdtemp(prefix="looking-glass-local-",
        dir=scratch_root or os.environ.get("LG_LOCAL_TEST_TMPDIR", "/tmp"))).resolve()
    token = uuid.uuid4().hex
    (scratch / ".owner-token").write_text(token)
    work = scratch / "worktree"
    try:
        probe(scratch)
        with (evidence / "workspace-setup.log").open("w") as stream:
            def git(*args, input=None):
                subprocess.run(["git", *map(str, args)], input=input, text=True,
                    stdout=stream, stderr=subprocess.STDOUT, check=True)
            git("clone", "--shared", "--no-checkout", "--no-tags", "--", source, work)
            git("-C", work, "config", "core.autocrlf", "false")
            git("-C", work, "sparse-checkout", "set", "--no-cone", "--stdin",
                input="/*\n!/ci-results-*/\n!/local-tests-*/\n")
            git("-C", work, "checkout", "--detach", commit)
        actual = subprocess.check_output(["git", "-C", str(work), "rev-parse", "HEAD"], text=True).strip()
        identity = evidence / "workspace-identity.json"
        identity.write_text(json.dumps(dict(requested=requested, expected=commit, actual=actual,
            source=str(source), worktree=str(work)), indent=2) + "\n")
        if actual != commit:
            raise RuntimeError(
                f"Workspace commit mismatch: requested={requested!r}, expected={commit!r}, "
                f"actual={actual!r}; see {identity}")
        (scratch / "tmp").mkdir()
        record.write_text(json.dumps(dict(scratch=str(scratch), worktree=str(work),
            token=token, commit=commit), indent=2) + "\n")
        return work
    except BaseException:
        shutil.rmtree(scratch)
        raise


def copy_tree(source, destination, omitted, selected=False):
    if source.is_symlink():
        omitted.append(str(source))
        return
    if not source.exists():
        return
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.iterdir()):
        mode = path.lstat().st_mode
        target = destination / path.name
        if stat.S_ISDIR(mode):
            copy_tree(path, target, omitted, selected)
        elif stat.S_ISREG(mode):
            if not selected or path.name == "page-errors.json" or path.name.endswith("-trace.zip") or (
                    path.suffix == ".png" and path.name.startswith(("dm-", "player-"))):
                shutil.copy2(path, target)
        else:
            omitted.append(str(path))


def finalize(evidence):
    evidence = Path(evidence).resolve()
    record = evidence / "workspace.json"
    if not record.exists():
        return
    data = json.loads(record.read_text())
    scratch, work = Path(data["scratch"]), Path(data["worktree"])
    if (not scratch.is_absolute() or scratch.is_symlink() or
            not scratch.name.startswith("looking-glass-local-") or work != scratch / "worktree" or
            (scratch / ".owner-token").read_text() != data["token"]):
        raise ValueError("Unsafe or foreign workspace; refusing cleanup")
    omitted = []
    copy_tree(work / "test-results", evidence / "diagnostics", omitted)
    copy_tree(scratch / "tmp", evidence / "browser-diagnostics", omitted, selected=True)
    (evidence / "omitted-special-files.json").write_text(json.dumps(omitted, indent=2) + "\n")
    shutil.rmtree(scratch)
    (evidence / "workspace-cleaned.txt").write_text("Temporary workspace removed after diagnostic collection.\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("source")
    p.add_argument("commit")
    p.add_argument("evidence")
    p = commands.add_parser("finalize")
    p.add_argument("evidence")
    args = parser.parse_args()
    if args.command == "prepare":
        print(prepare(args.source, args.commit, args.evidence))
    else:
        finalize(args.evidence)


if __name__ == "__main__":
    main()
