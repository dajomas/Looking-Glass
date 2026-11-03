"""Run every top-level JavaScript regression, retaining per-script evidence."""
import argparse
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test-dir", type=Path, default=ROOT / "python/tests")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "test-results")
    parser.add_argument("--node", default="node")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    tests = sorted(args.test_dir.resolve().glob("test_*.js"))
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    suite = ET.Element("testsuite", name="javascript-script-regressions")
    failures = 0
    started = time.monotonic()
    with (out / "javascript-inventory.tsv").open("w", encoding="utf-8") as inventory:
        inventory.write("script\texit_code\tseconds\tlog\n")
        for test in tests:
            log = out / (test.stem + ".log")
            begin = time.monotonic()
            reason = ""
            with log.open("wb") as stream:
                try:
                    result = subprocess.run(
                        [args.node, str(test)], cwd=ROOT,
                        stdout=stream, stderr=subprocess.STDOUT,
                        timeout=args.timeout, check=False,
                    )
                    code = result.returncode
                    if code:
                        reason = f"Node exited with status {code}; see {log.name}"
                except subprocess.TimeoutExpired:
                    code = 124
                    reason = f"Timed out after {args.timeout}s; see {log.name}"
                except OSError as exc:
                    code = 127
                    reason = f"Could not execute Node: {exc}"
                if reason:
                    stream.write(("\nRUNNER FAILURE: " + reason + "\n").encode("utf-8"))
            elapsed = time.monotonic() - begin
            case = ET.SubElement(suite, "testcase", classname="javascript.scripts", name=test.name, time=f"{elapsed:.6f}")
            if code:
                failures += 1
                ET.SubElement(case, "failure", message=reason).text = reason
            inventory.write(f"{test.name}\t{code}\t{elapsed:.6f}\t{log.name}\n")
            inventory.flush()
            print(f"{test.name}: exit={code}, seconds={elapsed:.3f}, log={log.name}", flush=True)
    if not tests:
        failures = 1
        case = ET.SubElement(suite, "testcase", classname="javascript.scripts", name="discovery")
        ET.SubElement(case, "failure", message="No JavaScript regression scripts discovered")
    suite.set("tests", str(len(suite.findall("testcase"))))
    suite.set("failures", str(failures))
    suite.set("errors", "0")
    suite.set("skipped", "0")
    suite.set("time", f"{time.monotonic() - started:.6f}")
    ET.ElementTree(suite).write(out / "results.xml", encoding="utf-8", xml_declaration=True)
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
