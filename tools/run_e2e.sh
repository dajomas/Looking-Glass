#!/usr/bin/env bash
# Run the Playwright end-to-end suite (Chromium and Firefox) against a real local
# Looking Glass server, store the results in e2e-results/<timestamp>/, keep only that
# latest results folder, then commit and push it with [skip ci].
# Adapted from the Scrying Glass tools/run_e2e.sh.
#
# Usage: tools/run_e2e.sh [--no-push] [extra pytest arguments]
# Environment: E2E_BRANCH (default features/claude), E2E_REMOTE (default origin),
#              E2E_PYTHON (default python3.14), E2E_VENV (default .venv-e2e),
#              E2E_HEADED=1 to show the browsers,
#              E2E_SKIP_DEPS_CHECK=1 to skip the system package check.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BRANCH="${E2E_BRANCH:-features/claude}"
REMOTE="${E2E_REMOTE:-origin}"
PYTHON="${E2E_PYTHON:-python3.14}"
VENV="${E2E_VENV:-.venv-e2e}"
PUSH=1
if [[ "${1:-}" == "--no-push" ]]
then
    PUSH=0
    shift
fi
EXTRA=()
[[ "${E2E_HEADED:-0}" == "1" ]] && EXTRA+=(--headed)

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

if (( PUSH ))
then
    [[ "$(git rev-parse --abbrev-ref HEAD)" == "$BRANCH" ]] || fail "check out $BRANCH first (or use --no-push)"
    git diff --cached --quiet || fail "the index already has staged changes; commit or unstage them first"
    git fetch --quiet "$REMOTE" "$BRANCH"
    behind="$(git rev-list --count "HEAD..$REMOTE/$BRANCH")"
    [[ "$behind" == "0" ]] || fail "local $BRANCH is $behind commit(s) behind $REMOTE/$BRANCH; pull first"
fi

# System packages: Playwright only knows apt (Debian/Ubuntu) package names. On dnf-based
# systems (Rocky, AlmaLinux, RHEL, CentOS, Fedora) check the equivalent rpm packages that
# Firefox needs and print the matching dnf command when any are missing.
DNF_PACKAGES=(libXcursor gtk3 pango cairo cairo-gobject gdk-pixbuf2)
os_like=""
if [[ -r /etc/os-release ]]
then
    os_like="$(. /etc/os-release; echo " ${ID:-} ${ID_LIKE:-} ")"
fi
if [[ "${E2E_SKIP_DEPS_CHECK:-0}" != "1" && "$os_like" =~ \ (rhel|fedora|centos|rocky|almalinux)\  ]] && command -v rpm >/dev/null 2>&1
then
    missing=()
    for package in "${DNF_PACKAGES[@]}"
    do
        rpm -q "$package" >/dev/null 2>&1 || missing+=("$package")
    done
    if (( ${#missing[@]} ))
    then
        fail "missing system packages for the Playwright browsers: ${missing[*]}
Install them with:
    sudo dnf install -y ${missing[*]}
then run this script again (E2E_SKIP_DEPS_CHECK=1 skips this check). Nothing was committed."
    fi
    echo "System package check (dnf): ${DNF_PACKAGES[*]} ... OK"
fi

# The server refuses Python older than 3.14, and it runs on the venv's interpreter.
if [[ ! -x "$VENV/bin/python" ]]
then
    command -v "$PYTHON" >/dev/null 2>&1 || fail "$PYTHON not found; install Python 3.14 or set E2E_PYTHON"
    "$PYTHON" -m venv "$VENV"
fi
PY="$VENV/bin/python"
"$PY" -c 'import sys; sys.exit(sys.version_info < (3, 14))' \
    || fail "$VENV uses $("$PY" -V 2>&1); Looking Glass needs Python 3.14. Remove $VENV and run again (E2E_PYTHON selects the interpreter)."
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet -r e2e/requirements.txt
"$PY" -m playwright install chromium firefox

# Preflight: both browsers must start before any test runs or anything is committed.
if ! "$PY" - <<'PY'
import sys
from playwright.sync_api import sync_playwright
failed = []
with sync_playwright() as playwright:
    for name in ("chromium", "firefox"):
        try:
            args = ["--no-sandbox"] if name == "chromium" else []
            getattr(playwright, name).launch(headless=True, args=args).close()
            print(f"Browser check: {name} ... OK")
        except Exception as error:
            print(f"Browser check: {name} ... FAILED\n{str(error).splitlines()[0]}")
            failed.append(name)
sys.exit(1 if failed else 0)
PY
then
    if [[ "$os_like" =~ \ (rhel|fedora|centos|rocky|almalinux)\  ]]
    then
        fail "a browser could not start. Playwright's install-deps and apt package names do not apply here.
Install the dnf equivalents of the libraries named above (for example: sudo dnf install -y ${DNF_PACKAGES[*]}),
then run this script again. Nothing was committed."
    fi
    fail "a browser could not start; install its system libraries with:
    sudo $VENV/bin/python -m playwright install-deps chromium firefox
then run this script again. Nothing was committed."
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="e2e-results/$STAMP"
mkdir -p "$OUT"
SHA="$(git rev-parse HEAD)"
DIRTY="$(git status --porcelain --untracked-files=no -- . ':!e2e-results' | head -20)"

set +e
E2E_ARTIFACTS="$ROOT/$OUT" "$PY" -m pytest -c e2e/pytest.ini e2e -q -rfE \
    --junitxml="$OUT/junit.xml" --html="$OUT/report.html" --self-contained-html ${EXTRA[@]+"${EXTRA[@]}"} "$@" \
    2>&1 | tee "$OUT/pytest.log"
STATUS="${PIPESTATUS[0]}"
set -e

DIRTY="$DIRTY" "$PY" - "$OUT" "$SHA" "$STATUS" <<'PY'
import os, sys, xml.etree.ElementTree as ET
from pathlib import Path
out, sha, status = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
counts = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
per_browser = {}
junit = out / "junit.xml"
if junit.exists():
    for case in ET.parse(junit).iter("testcase"):
        name = case.get("name", "")
        browser = name[name.rfind("[") + 1:-1] if name.endswith("]") else "server-only"
        result = "passed"
        for tag in ("failure", "error", "skipped"):
            if case.find(tag) is not None:
                result = tag
        counts["tests"] += 1
        if result != "passed":
            counts[{"failure": "failures", "error": "errors", "skipped": "skipped"}[result]] += 1
        per_browser.setdefault(browser, {}).setdefault(result, 0)
        per_browser[browser][result] += 1
passed = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
lines = [f"# E2E results {out.name}", "", f"- Commit tested: `{sha}`"]
dirty = os.environ.get("DIRTY", "").strip()
if dirty:
    lines.append("- Working tree had uncommitted changes to tracked files (tested as they were):")
    lines += [f"    - `{line.strip()}`" for line in dirty.splitlines()]
lines += [f"- pytest exit status: {status}",
          f"- Total: {counts['tests']}; passed {passed}, failed {counts['failures']}, errors {counts['errors']}, skipped {counts['skipped']}"]
lines += [f"- {browser}: " + ", ".join(f"{k} {v}" for k, v in sorted(r.items())) for browser, r in sorted(per_browser.items())]
lines += ["", "Files: `junit.xml`, `report.html`, `pytest.log`, `server.log` (and `webp-server.log`); screenshots, "
          "traces, console and server-log extracts for failed tests under `failures/`."]
(out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
(out / "subject.txt").write_text(f"{passed} passed, {counts['failures'] + counts['errors']} failed", encoding="utf-8")
PY
cat "$OUT/summary.md"
RESULT="$(cat "$OUT/subject.txt")"
rm -f "$OUT/subject.txt"

if (( ! PUSH ))
then
    echo "Results in $OUT (not committed; older results folders left in place)."
    exit "$STATUS"
fi

# Keep only the latest results folder.
for old in e2e-results/*/
do
    [[ "${old%/}" == "$OUT" ]] || rm -rf "$old"
done

git add -A e2e-results
outside="$(git diff --cached --name-only | grep -v '^e2e-results/' || true)"
[[ -z "$outside" ]] || fail "refusing to commit files outside e2e-results/: $outside"
git diff --cached --quiet && fail "no result changes to commit"
git commit --quiet -F - <<MSG
E2E results $STAMP: $RESULT (chromium, firefox) [skip ci]

Playwright end-to-end suite run against $SHA.
MSG
# Push. A commit can reach the branch while the suite runs (CI publishes its results with
# a [skip ci] commit), so a refused push fetches, checks that the new remote commits leave
# e2e-results/ alone, rebases the results commit onto them and tries again.
attempt=1
until git push --quiet "$REMOTE" "HEAD:refs/heads/$BRANCH"
do
    (( attempt < 3 )) || fail "push refused $attempt times; the results commit $(git rev-parse --short HEAD) is kept locally"
    git fetch --quiet "$REMOTE" "$BRANCH"
    incoming="$(git diff --name-only "HEAD~1...$REMOTE/$BRANCH" -- e2e-results/)"
    [[ -z "$incoming" ]] || fail "$REMOTE/$BRANCH changed e2e-results/ meanwhile; resolve by hand (results commit kept locally)"
    if ! git rebase --quiet "$REMOTE/$BRANCH"
    then
        git rebase --abort || true
        fail "could not rebase the results commit onto $REMOTE/$BRANCH; it is kept locally"
    fi
    echo "Rebased the results commit onto $(git rev-parse --short "$REMOTE/$BRANCH"); pushing again."
    attempt=$((attempt + 1))
done
echo "Pushed $(git rev-parse HEAD) to $REMOTE/$BRANCH."
exit "$STATUS"
