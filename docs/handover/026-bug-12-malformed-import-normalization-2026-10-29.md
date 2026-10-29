## Bug 12: malformed import normalization (2026-10-29)

Delivery baseline: features/perplexity at
69376ea3ed6fe53a487f3b14529dd6db41e1ee63. The split handover, existing CI
workflow and live-login helper changes are preserved. README was reviewed
and needs no edit. Historical split sections and manifest.json are unchanged.

Only services/foundry_import.py changes runtime behavior. Local door conversion
handling and explicit checks before unsafe container, metadata and endpoint
operations normalize expected malformed input to WallImportError. No blanket
parser catch is added. NeDB identity/replay from bug 10 and numeric/calibration
rules from bug 11 are unchanged. Existing falsy defaults, iterable filtering,
nonnumeric/zero-length wall omission, UVTT point filtering and short bounds
remain. ZIP per-entry skipping, invalid-only rejection, ordering and safety
limits are unchanged. Map-upload partial success and source retention after
a later target-calibration rejection are not redesigned. No routes, migrations,
dependencies, settings, image lifecycle or other backlog implementations change.

The runtime candidate matches previously tested blob
67ab34b31af2c77a3da6c27009bcaa5480fabc9c; its 90-case parser regression module
matches c3482a4994c8fafdacc04542d967c329348b9628. At the delivery baseline, the
importer baseline, relevant support modules, existing service tests and import
route modules retain their previously verified blobs. This compatibility check
is not a fresh application or integration test run.

Actual earlier validation on Python 3.12.8 in fresh focused subprocesses:
- Combined unchanged baseline: 48 failed, 268 passed; no errors/skips.
- Exact candidate: 316 passed in 0.31 seconds; no errors/skips.
- Counts: new shape/error cases 90; numeric/parser 154; Foundry 8; NeDB 24;
  UVTT 30; pack-image 10. Complete runtime/support modules and test files were
  hash-verified. Empty initializers and a minimal helper-only conftest bypassed
  application initialization. Parser/calibration, passage validation, ZIP I/O
  and temporary image normalization were real.
- All 14 Python sources in that focused tree compiled.
- A separate earlier policy run passed 30 isolated cases, not part of the 316.
  Parser, DB/repository, permissions, images and responses were doubles; local
  campaign/API execution used pinned function excerpts. It is not HTTP/DB proof.
- The prepared real-app HTTP/DB module has 29 intended cases. It compiled only,
  without collection or execution. FastAPI, Starlette, Uvicorn and multipart
  were absent in the execution environment. No HTTP case is counted as passed.

No tests are claimed rerun for this delivery preparation. The current GitHub
Actions workflow runs Python/HTTP and live Uvicorn checks after branch pushes;
its presence is not a successful run. Record actual run evidence for the
delivered revision before upgrading acceptance status. Full application imports,
normal-checkout route execution, persistent DB state/rollback, auth/CSRF, full
suite, browser/live-server and target Python 3.14 acceptance remain pending.
Bug 11's historical 202 focused passes remain separate from that acceptance.

The user explicitly authorized three commits for bug 12 only, without a signature
guarantee. Each write requires its own exact-content approval:
1. Importer, 90-case parser regression, import guide and split handover/index.
2. HTTP/DB and isolated policy regression modules plus handover status.
3. TODO completion and final delivery-status documentation.
This record is prepared for step 1, not proof that any write succeeded. TODO
item 12 remains open until the final delivery step. Do not describe intermediate
steps as the complete three-commit delivery. Record actual returned SHAs after
successful writes. No generated Patch/ content, archive or other-branch write
is included.

### Step 1 delivered; step 2 regression coverage prepared

Step 1 is delivered in 0b8b3189487d373b5fd3613c16c6fa7f694b1136 on
features/perplexity. Post-write reads verified the importer and 90-case parser
regression blobs recorded above. No tests were rerun during that write, and
no Actions result has been verified. Earlier preparation wording is historical.

Step 2 is prepared against that commit and adds only:
- python/tests/test_import_policy_routes.py: 30 isolated route/ZIP-policy cases;
  candidate blob 590710a25139a340cadb3e7df9abf4f80e574251.
- python/tests/test_import_shapes_web.py: 29 intended real-app HTTP/DB cases;
  candidate blob 1e906c3ec298db4dedb6d69deca140b7db2defbc.
Both complete files were reconstructed, checked against those candidate hashes
and compiled successfully during step 2 preparation. No tests were collected or
executed during this preparation. The earlier 30 isolated passes are not a new
normal-checkout run; the 29 HTTP/DB cases remain unexecuted, not passing/skipped.

The HTTP module exercises real existing application/login/CSRF/DB fixtures,
including persistent geometry/calibration/source comparisons, malformed legacy
sources, map-upload partial success, mixed/invalid-only ZIPs and source retention
after target rejection. The isolated module deliberately doubles parser/apply,
DB/repositories, permissions, images and responses and strips route decorators
and annotations by AST; it does not prove persistent rollback or HTTP behavior.

Normal-checkout command after step 2 delivery:
PYTHONPATH=python python -m pytest -q python/tests/test_import_policy_routes.py python/tests/test_import_shapes_web.py
The existing Python/HTTP workflow selects these files through python/tests;
verify its exact delivered-SHA results and artifacts rather than inferring a pass
from workflow existence or commit delivery. Runtime code, the guide, index and
TODO are unchanged in step 2. TODO completion and final delivery-status records
remain step 3; this preparation entry is not proof of step 2 delivery.
