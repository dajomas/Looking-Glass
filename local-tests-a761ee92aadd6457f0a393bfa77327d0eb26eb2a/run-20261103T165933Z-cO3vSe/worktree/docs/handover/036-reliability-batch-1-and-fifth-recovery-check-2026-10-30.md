## Reliability batch 1 and fifth Recovery check (2026-10-30)

Added 14 regression cases: nine CI-evidence chunking cases in Python / HTTP,
three live reconnect/tab/session cases, and two real CLI subprocess restart
cases in a new Recovery matrix job. The workflow excludes recovery from the
Python job to avoid duplicate CI execution. Existing check names and strict
JUnit audit/artifact retention remain; the fifth artifact is integration-recovery.
The collector already handles every artifact for a run and needs no modification.

Recovery uses explicit temporary configuration/data, sanitized LG_* environment,
test-only credentials, ephemeral loopback ports and bounded startup/shutdown.
Normal restart and forced termination after committed requests must preserve
existing viewer access, active map version, saved fog snapshot and fogged image
pixels; both listeners, integrity/foreign-key checks and anonymous refusal are
checked. This is not an in-flight write interruption or power-failure guarantee.
Port reservation is released for the CLI listener, so a race fails startup.
Child-server logs are retained under test-results/recovery, not temporary DBs.

Live additions cover offline reconnect after a missed reveal and continued hide/
undo delivery when one of two tabs closes, both with a shared session and with
independent sessions for the same account. The new secondary context has page
error reporting but no separate trace capture. Distinct-account permissions,
revocation and delayed responses remain separate follow-up scenarios.

The live job now uses a dedicated ci-live-tmp basetemp and always copies existing
fixture traces, DM/player screenshots and page-errors.json into uploaded
 test-results/live-diagnostics paths while preserving test-relative locations.
No fixture or runtime application code changes are needed. Binary trace copies
remain available through the collector's lossless base64 chunk format.

Chunk tests cover Unicode/CRLF, single-line XML, binary/empty files, exact
reconstruction and size bounds, altered/missing parts, changed originals,
no-overwrite and complete paginated inventory. They use only temporary data.
The three new Python modules passed local syntax parsing; no full checkout,
actual application process, Chromium, hosted workflow or actionlint run was
performed by the assistant for this batch. All new-case execution remains pending
CI. The prior four-suite run 41017872020 was reviewed green at e6f932b688682328177dc7ef0063400bb75514be;
that result does not establish this first five-suite batch passes.

Explicit remaining backlog: built-container startup/health/volume persistence;
controlled interruption during migration, restore and duplication; disk-full,
permission and locking fault injection; bounded Hypothesis state-machine checks;
live delayed-response, revocation and checkpoint/backup-restore propagation;
committed collector-cleanup and JavaScript-runner harness regressions. These
were proposed but are not implemented in batch 1. README and docs/ci-tests.md
now document five-suite scope, commands, evidence and these limitations.

