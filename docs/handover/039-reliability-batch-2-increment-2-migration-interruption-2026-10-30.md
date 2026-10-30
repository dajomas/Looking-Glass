## Reliability batch 2 increment 2: migration interruption (2026-10-30)

Added `python/tests/recovery/test_migration_interruption.py` with two cases at
known migration-3 boundaries: before ordered initialization, and after it but
before version recording/commit. Only a temporary child process monkeypatches
the existing initialization hook. It asserts an active transaction and recorded
version 2, atomically writes a phase/PID/snapshot handshake, then blocks on its
private stdin pipe. The parent validates the handshake and independent-reader
visibility before killing precisely that child. Random sleeps do not select the
interruption boundary; polling merely waits for the explicit barrier marker.

The fixture uses actual migration 1/2 scripts and committed synthetic data only.
After the child is killed, version, schema and every legacy table's data must
match the committed baseline; integrity and foreign keys must pass. A fresh
unmodified child retries all pending migrations. It must preserve legacy column
values, reach the current version and create correctly ordered per-map snapshots
without an empty-map snapshot. Repeated migration must preserve tokens and full
snapshot rows. Handshake/kill/retry waits are bounded, and child cleanup runs on
failures. Logs, marker and success summary are written to
 test-results/migration-interruption/<phase> for existing artifact collection.
Temporary database files/configuration are not uploaded or taken from real data.

No workflow or collector edits are necessary: Recovery already discovers these
files and uploads all test-results. Production migration SQL, hooks and runtime
behaviour remain unchanged. README was reviewed and left unchanged: these two
selected process-kill boundaries do not introduce a general in-flight crash,
power-loss or cross-filesystem atomicity guarantee. Detailed scope and a focused
local command are in docs/ci-tests.md.

Preparation validation: new module parsed successfully and two isolated synthetic
SQLite child-process handshake/kill/rollback/retry experiments passed on Python
3.12.8 / SQLite 3.46.1. Those experiments tested the process/barrier method, not
the full application migration scripts. The new repository cases/full suites and
Python 3.14 CI were not executed by the assistant; CI acceptance remains pending.
Increment 1 was subsequently reviewed green in run 41022509451 at
9397eaf499235c98cad271b5e4b9e91f67e3714a, with four Recovery cases including
both Docker tests. That prior result does not validate increment 2.

Remaining batch-2 work: permission/disk/locking fault injection and live access
revocation. Broader migration-statement coverage, restore/duplication interruption,
property-based state machines, delayed-response/restore propagation and collector/
runner harnesses remain follow-up work. These tests do not simulate power loss
or prove atomicity across database and image files.

