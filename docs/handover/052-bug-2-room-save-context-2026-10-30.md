## Bug 2: ordinary-save payload context prerequisite (2026-10-30)

Prepared against features/perplexity HEAD
be847759d3428a165bbd86d6275f3e84d6e1fb9c. This is step 1 of the drafted
revision-safe ordinary-save increment, not activation of strict save validation.

payload() now requires an active transaction and an existing map. It returns
cache_token, walls_version and room_notes_version alongside the existing area
key, note revision, exact stored content, sanitized HTML and revealed flag.
The existing _room_at path establishes a transaction through reconciliation
before obtaining geometry and payload. Direct callers must now begin a
transaction explicitly. Missing-map payloads raise rather than manufacturing
an empty room without map context. No new schema change is required.

The existing room-note unit module is adapted to the missing-map contract and
adds checks for the transaction precondition, empty/saved/updated payload
context, map isolation, unchanged fog/archive state and rollback of content,
revision and generation. These are real migrated SQLite unit tests, not HTTP
or image/browser tests. Their fixture image filenames are placeholders; no
image-loading acceptance is claimed.

Validation: live HEAD, README.md, HANDOVER.md and the existing payload test
module were reviewed. No application tests, imports, pytest collection or
workflow results were executed/verified for this proposed increment. Tests
are supplied for CI execution; they are not recorded as passed.

Delivery order is payload context, then editor submission/delayed-response
protection, then required server context validation and affected test adapters.
The ordinary-save route and editor are unchanged in this commit. They still
use the old request contract, so stale-save protection is NOT complete. The
existing integration cases requiring missing-field rejection remain red until
strict validation is installed. No skips/exclusions are introduced.

Remaining bug-2 work includes those save steps, management-only archive listing
and explicit recovery/UI, legacy-compatible archive backup/restore/duplication,
migration/service regressions and full acceptance. The intermediate branch is
not deployable against valuable campaign data; portability limitations in
records 050/051 still apply. Keep bug 2 open. README.md was reviewed and needs
no edit for additive internal response context; no new user-facing capability
is advertised. HANDOVER.md links this focused record. Historical records and
reconstruction manifests remain unchanged; no Patch/ material is included.
