"""Subprocess regressions for the JS runner; Python stands in for Node.

Run: python -m pytest -q python/tests/test_javascript_runner.py
These cases test runner orchestration/reporting, not JavaScript semantics.
"""
import csv
import math
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/run_javascript_tests.py"


class Sandbox:
    def __init__(self, temporary):
        self.root = temporary
        self.tests = temporary / "scripts with spaces"
        self.output = temporary / "reports with spaces"
        self.tests.mkdir()

    def script(self, name, source):
        path = self.tests / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    def run(self, *, node=None, timeout="3"):
        env = {key:value for key,value in os.environ.items()
               if key not in {"PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT"}}
        env.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        return subprocess.run(
            [sys.executable, str(RUNNER), "--test-dir", str(self.tests),
             "--output-dir", str(self.output), "--node", str(node or sys.executable),
             "--timeout", str(timeout)],
            cwd=self.root, env=env, capture_output=True, text=True, encoding="utf-8",
            timeout=20, check=False,
        )

    def reports(self):
        suite = ET.parse(self.output / "results.xml").getroot()
        assert suite.tag == "testsuite"
        assert suite.get("name") == "javascript-script-regressions"
        cases = suite.findall("testcase")
        assert int(suite.get("tests")) == len(cases)
        assert int(suite.get("failures")) == sum(case.find("failure") is not None for case in cases)
        assert suite.get("errors") == suite.get("skipped") == "0"
        assert not suite.findall(".//error") and not suite.findall(".//skipped")
        assert math.isfinite(float(suite.get("time"))) and float(suite.get("time")) >= 0
        by_name = {case.get("name"):case for case in cases}
        assert len(by_name) == len(cases)
        with (self.output / "javascript-inventory.tsv").open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            assert reader.fieldnames == ["script", "exit_code", "seconds", "log"]
            rows = list(reader)
        assert len(rows) == (0 if list(by_name) == ["discovery"] else len(cases))
        for row in rows:
            case = by_name[row["script"]]
            assert case.get("classname") == "javascript.scripts"
            assert (int(row["exit_code"]) != 0) == (case.find("failure") is not None)
            elapsed = float(row["seconds"])
            assert math.isfinite(elapsed) and elapsed >= 0
            assert elapsed == float(case.get("time"))
            assert row["log"] == Path(row["script"]).stem + ".log"
            assert (self.output / row["log"]).is_file()
        return suite, by_name, rows

    def log(self, name):
        return (self.output / (Path(name).stem + ".log")).read_text(encoding="utf-8")


@pytest.fixture
def sandbox(tmp_path):
    return Sandbox(tmp_path)


def test_discovery_is_sorted_top_level_and_excludes_unrelated_files(sandbox):
    order = sandbox.root / "execution-order.txt"
    for name in ("test_z.js", "test_a.js"):
        sandbox.script(name, f"from pathlib import Path\nwith Path({str(order)!r}).open('a') as stream: stream.write({name!r} + '\\n')\n")
    for name in ("helper.js", "test_ignore.py", "nested/test_nested.js"):
        sandbox.script(name, "raise AssertionError('must not execute')\n")
    result = sandbox.run()
    assert result.returncode == 0, result.stdout + result.stderr
    suite, cases, rows = sandbox.reports()
    expected = ["test_a.js", "test_z.js"]
    assert list(cases) == [row["script"] for row in rows] == expected
    assert order.read_text().splitlines() == expected
    assert [line.split(": exit=")[0] for line in result.stdout.splitlines()] == expected
    assert suite.get("failures") == "0"
    assert {int(row["exit_code"]) for row in rows} == {0}


def test_success_retains_stdout_stderr_and_uses_repository_cwd(sandbox):
    sandbox.script("test_output.js", "import sys\nfrom pathlib import Path\nprint('stdout marker')\nprint('stderr marker', file=sys.stderr)\nprint('cwd=' + str(Path.cwd()))\n")
    result = sandbox.run()
    assert result.returncode == 0, result.stdout + result.stderr
    suite, cases, rows = sandbox.reports()
    assert list(cases) == ["test_output.js"]
    assert suite.get("failures") == "0" and rows[0]["exit_code"] == "0"
    text = sandbox.log("test_output.js")
    assert "stdout marker" in text and "stderr marker" in text
    assert "cwd=" + str(ROOT) in text
    assert "RUNNER FAILURE:" not in text


def test_nonzero_exit_is_reported_and_later_scripts_still_run(sandbox):
    sandbox.script("test_a_fail.js", "import sys\nprint('before failure', flush=True)\nprint('failure stderr', file=sys.stderr)\nsys.exit(7)\n")
    sandbox.script("test_b_pass.js", "print('later success')\n")
    result = sandbox.run()
    assert result.returncode == 1, result.stdout + result.stderr
    suite, cases, rows = sandbox.reports()
    assert suite.get("failures") == "1"
    assert [row["exit_code"] for row in rows] == ["7", "0"]
    failure = cases["test_a_fail.js"].find("failure")
    assert "status 7" in failure.get("message") and failure.text == failure.get("message")
    assert cases["test_b_pass.js"].find("failure") is None
    assert "before failure" in sandbox.log("test_a_fail.js")
    assert "failure stderr" in sandbox.log("test_a_fail.js")
    assert "RUNNER FAILURE:" in sandbox.log("test_a_fail.js")
    assert "later success" in sandbox.log("test_b_pass.js")


def test_timeout_retains_partial_output_and_continues(sandbox):
    sandbox.script("test_a_slow.js", "import time\nprint('started slow child', flush=True)\ntime.sleep(30)\n")
    sandbox.script("test_b_pass.js", "print('ran after timeout')\n")
    result = sandbox.run(timeout="1")
    assert result.returncode == 1, result.stdout + result.stderr
    suite, cases, rows = sandbox.reports()
    assert suite.get("failures") == "1"
    assert [row["exit_code"] for row in rows] == ["124", "0"]
    assert "Timed out after 1.0s" in cases["test_a_slow.js"].find("failure").get("message")
    assert cases["test_b_pass.js"].find("failure") is None
    assert "started slow child" in sandbox.log("test_a_slow.js")
    assert "RUNNER FAILURE: Timed out" in sandbox.log("test_a_slow.js")
    assert "ran after timeout" in sandbox.log("test_b_pass.js")


def test_missing_executable_reports_each_script_without_aborting(sandbox):
    for name in ("test_a.js", "test_b.js"):
        sandbox.script(name, "print('must not run')\n")
    missing = sandbox.root / "nonexistent-node"
    assert not missing.exists()
    result = sandbox.run(node=missing)
    assert result.returncode == 1, result.stdout + result.stderr
    suite, cases, rows = sandbox.reports()
    assert suite.get("failures") == "2"
    assert [row["exit_code"] for row in rows] == ["127", "127"]
    for name, case in cases.items():
        assert "Could not execute Node:" in case.find("failure").get("message")
        text = sandbox.log(name)
        assert "RUNNER FAILURE: Could not execute Node:" in text
        assert str(missing) in text and "must not run" not in text


def test_empty_discovery_emits_failing_case_and_header_only_inventory(sandbox):
    sandbox.script("helper.js", "raise AssertionError('must not execute')\n")
    result = sandbox.run()
    assert result.returncode == 1, result.stdout + result.stderr
    suite, cases, rows = sandbox.reports()
    assert suite.get("tests") == suite.get("failures") == "1"
    assert list(cases) == ["discovery"] and rows == []
    assert cases["discovery"].find("failure").get("message") == "No JavaScript regression scripts discovered"
    assert list(sandbox.output.glob("*.log")) == []


@pytest.mark.parametrize("timeout", ["0", "-1"])
def test_nonpositive_timeout_is_rejected_before_execution(sandbox, timeout):
    sandbox.script("test_never.js", "raise AssertionError('must not execute')\n")
    result = sandbox.run(timeout=timeout)
    assert result.returncode == 2, result.stdout + result.stderr
    assert "--timeout must be positive" in result.stderr
    assert not sandbox.output.exists()


def test_xml_round_trips_special_script_names_and_failure_messages(sandbox):
    name = "test_a&'quoted.js"
    sandbox.script(name, "import sys\nprint(\"<output>&'quoted\", flush=True)\nsys.exit(9)\n")
    result = sandbox.run()
    assert result.returncode == 1, result.stdout + result.stderr
    suite, cases, rows = sandbox.reports()
    assert suite.get("failures") == "1" and list(cases) == [name]
    assert rows[0]["script"] == name and rows[0]["exit_code"] == "9"
    log_name = Path(name).stem + ".log"
    expected = f"Node exited with status 9; see {log_name}"
    failure = cases[name].find("failure")
    assert failure.get("message") == failure.text == expected
    assert "&amp;" in (sandbox.output / "results.xml").read_text(encoding="utf-8")
    assert "<output>&'quoted" in sandbox.log(name)
