## Reliability batch 2 increment 3: storage-failure safety (2026-10-30)

Added 11 top-level Python / HTTP cases: eight service cases (two image-write
faults, collision preservation, four recovery-ZIP write/durability faults, real
SQLite contention/retry) and three HTTP recovery-gate failures (EACCES, ENOSPC,
EIO). They compare prior bytes and committed rows, require the injected boundary
to be reached, reject premature live restoration/success notification, and test
successful retry after service-level faults/locking are removed. Test-local
faults avoid actual disk exhaustion or permission changes. The directory-fsync
case targets Linux CI, not Windows. Existing workflow discovery and artifact
collection already include all cases; no workflow/getworkflow.sh changes needed.

A focused image experiment reproduced a real defect in the live store helper:
partial PNG bytes remained when encoding raised ENOSPC. The helper now creates
its destination exclusively, then closes and attempts unlink on encoding/close
failure. A preexisting UUID collision raises without overwriting or deleting its
file. Cleanup failures log a warning while retaining the original exception.
This is the only runtime code change, limited to images.py. It is best effort,
not crash-safe/atomic/fsync-backed publication; empty directories can remain.
Existing storage exception types/HTTP upload error mapping are not redesigned.

The HTTP cases prepare valid preview tokens, distinguish inspection-clone work
from live-database replacement and verify an error redirect with no changes to
any main DB rows/map files/recovery files and no awaited success notification.
The SQLite case uses a real competing write lock and a short busy timeout only
on the contender connection, then verifies retry after release. These are not
real-browser delivery or broad concurrent-load tests; those remain separate.

Validation: the live images.py blob matched 243817c79253daa7cb478f20f2630ec86cb5ce5e
before modification. The original partial-file leak was reproduced. Candidate
partial-write cleanup, denied-open preservation, collision preservation, valid
image retry and actual SQLite contention/retry checks passed on Python 3.12.8 /
SQLite 3.46.1. Candidate source/new test modules parsed. Full repository pytest,
HTTP/recovery-backup checks and Python 3.14 CI were not executed for this change;
CI acceptance is pending. Prior increment 2 was reviewed green in run 41025509410
at 183a4787001597095a4ba26303ca57b04557b3ed; that does not validate this increment.

Explicit remaining gap: upload/replace can fail at a database boundary after a
fully successful image store; post-store transaction/orphan cleanup is not
covered or fixed here. Sudden termination, unlink failure, genuine exhausted
filesystems and other operating systems also remain outside these guarantees.
Increment 4 (live access revocation), broader property/race/fault coverage and
collector/runner regressions remain follow-up work. README was reviewed and its
high-level scope stays unchanged; docs/ci-tests.md documents the precise cases,
minimal image fix, local command and limits.

