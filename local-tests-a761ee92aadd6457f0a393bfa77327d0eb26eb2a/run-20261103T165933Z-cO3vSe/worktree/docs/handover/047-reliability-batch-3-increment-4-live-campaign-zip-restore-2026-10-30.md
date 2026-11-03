## Reliability batch 3 increment 4: live campaign ZIP restore (2026-10-30)

The user ran the checkpoint module in .venv-test: three cases passed in 31.11s,
and reported a green GitHub workflow. This validates those local checkpoint
scenarios and supplies a user-confirmed workflow result; no independent run ID,
tested SHA or complete suite counts were supplied. It does not validate the new
ZIP cases below.

Added `python/tests/live_e2e/test_live_zip_restore.py` with four cases: an actual
campaign backup/restore/downloaded-recovery round trip and three rejected restores
(wrong campaign confirmation, different uploaded ZIP, stale target preview).
Authenticated exports and multipart inspection/restore use the actual application
routes. The success case changes the active map and revealed region, restores the
saved red-map scene, downloads the automatic pre-restore recovery ZIP, compares
its manifest/member contents to a pre-restore backup, then inspects and restores
that recovery ZIP to reinstall the changed green-map scene. It checks normal
hide/undo delivery afterward. Imported map IDs are rediscovered from current
exports rather than assumed to survive restore; new display tokens must replace
old installed image versions.

The module subclasses the existing Checkpoints observer/helper from
.test_live_checkpoints instead of duplicating native WS recording. It preserves
the player document, single native connection and existing viewer cookie; it
checks actual campaign refresh messages, current ready reports and installed
server-rendered image pixels/URLs. Successful real owner operations and continued
viewer access exercise the original authenticated identities, not a full account/
permission audit. Export and inspection must not change viewer state. Negative
cases preserve current viewer state, installed image and exported campaign member
content, observe no additional campaign-restore notice at the assertion boundary,
and prove subsequent fog/undo delivery still works.

ZIP checks verify CRCs, unique member names, expected format/version and absence
of account/session/assignment/checkpoint tables and campaign owner_id. Comparing
member bytes avoids timestamp/compression-container differences; it is not general
ZIP-bomb or malicious-archive coverage. Small synthetic archives stay in memory.
A standard HTMLParser extracts the real escaped preview token and recovery link;
no fake tokens, direct database writes, HTTP interception or synthetic WS transport.
Rejection checks do not inventory the recovery directory or every private database
row; existing storage-gate tests cover separate lower-level failure boundaries.

Candidate validation: Python syntax parsing and a focused escaped preview-token
HTML round trip passed. None of the four live cases, full suites or Python 3.14
hosted CI was executed by the assistant. Execution and possible harness corrections
remain pending; this candidate supplies no new runtime-defect or passing-run claim.
The existing isolated Live Uvicorn fixture and discovery collect these cases;
shared fixtures, workflow, requirements, collector and application are unchanged.
README was reviewed and remains accurate. Focused command:
LG_RUN_LIVE_E2E=1 python -m pytest -q python/tests/live_e2e/test_live_zip_restore.py.
Broader artwork/runtime-state/permission and multi-viewer restore, interruption,
fault injection, property-based coverage and the post-image-store transaction gap
remain follow-up work. No existing CI evidence or other branches are modified.

