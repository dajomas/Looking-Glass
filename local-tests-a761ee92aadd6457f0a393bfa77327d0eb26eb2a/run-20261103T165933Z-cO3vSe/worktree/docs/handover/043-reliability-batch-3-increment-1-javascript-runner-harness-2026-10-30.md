## Reliability batch 3 increment 1: JavaScript runner harness (2026-10-30)

Added `python/tests/test_javascript_runner.py` with nine cases (eight functions,
including two nonpositive-timeout parameters). Each invokes the actual runner CLI
in a separate subprocess. Synthetic Python scripts use .js names and the current
Python executable is supplied through --node, so this tests orchestration without
requiring Node or pretending to validate JavaScript language/runtime behaviour.
All inputs and reports use temporary directories, including paths with spaces;
runner child cwd must still be the repository root. No real project JS scripts,
accounts, application config, database or existing evidence are modified.

Cases cover sorted top-level discovery and exclusion, stdout/stderr capture,
nonzero exit with continuation, timeout with retained partial output/continuation,
missing executable across multiple scripts, failing empty discovery, zero and
negative timeout rejection, and XML special-character round trips. Shared report
checks compare JUnit counts/failures and inventory exit codes, case identity,
finite nonnegative durations and log paths. A timed-out case must be 124, missing
execution 127, and argument rejection 2. An outer 20-second timeout bounds each
runner subprocess; the slow fixture sleeps without spawning descendants.

The unchanged live runner blob was verified as
b21ab142dbf545cfb370b5aa7db1ea90d8026d78. All nine tests passed in 1.52 seconds in
an isolated temporary repository layout using that exact runner and candidate
module. This executed real subprocess/timeouts and XML/TSV parsing, not mocked
subprocess returns. It did not load the real checkout's conftest or run the full
application suites, Node scripts or Python 3.14 CI. Hosted acceptance remains
pending, as does any unreviewed CI acceptance of the preceding wall-width fix.

README.md was reviewed and left unchanged; its test overview and the CI guide's
runner invocation remain valid. This module docstring provides the focused local
command: python -m pytest -q python/tests/test_javascript_runner.py. Existing
Python / HTTP top-level discovery includes the new module; workflow, collector,
runner implementation and requirements are unchanged. Nested Node skip semantics,
process-tree cancellation, arbitrary/nonfinite timeout values, damaged-output/
permission failures and unusual tab/newline filenames are not newly covered.
Collector cleanup/publication harnesses and broader property/live/fault coverage
remain separate backlog items; this does not mark all tooling work complete.

