## Bug 2: dedicated recovery management UI (2026-10-30)

Prepared against features/perplexity HEAD
86b653a03eb4d6844237bf036e448ad6f836395f. A management-only, no-store HTML
workspace is added at /maps/{map_id}/room-note-recovery, mounted only on the
admin app. A map-aware top-nav link opens it in a new tab, preserving the original
editor page and draft. This intentionally uses a dedicated workspace rather than
embedding another modal into the editor. Other-tab drafts are not auto-refreshed
or applied; recovery may invalidate their old save context.

The workspace shows paginated retained choices, exact Markdown source and full
provenance using textContent. Targets are inspected by artwork click or labeled
coordinate form; controls do not issue fog or travel operations. Captured target
context is submitted unchanged. Every recovery has native confirmation; nonempty
targets also require a replacement checkbox, reset after each target inspection
or successful recovery. Coordinate edits invalidate the inspected target.
Delayed target responses use generations; recovery blocks duplicate writes and
warns before leaving while pending. Errors retain source/target previews, disable
recovery until explicit reinspection, and do not automatically rebase/retry.
Map incarnation/wall-version changes relative to page load require reload so
recovery cannot use a newly inspected context against an obsolete workspace.

The existing CSRF-aware LGApi wrapper is reused, including its normal expired-
session login navigation. No automatic reattachment, archive purge, viewer
publication or portability change is included. The backend recovery service
and ordinary editor are unchanged. Listing retains its existing read-time
reconciliation behavior.

HTTP page tests cover access, no-store, nonmutation and the new-tab editor link.
Three Chromium tests use real templates/scripts/API handlers/SQLite through a
Playwright intercepted transport proxy to the authenticated DM TestClient. They
cover cancel then recovery, raw-text safety and viewer invariance, replacement
consent and stale rejection/reinspection, and pagination with source selection
retained. The HTML fixture sets page size to one for cheap paging coverage.
This is not real browser-cookie login, live listeners, multi-tab convergence or
deployment acceptance. The existing browser fixture supplies Chromium.

Validation: current HEAD, live map editor, library manager, navigation, template
renderer/base, app factory, API wrapper, browser fixture, README.md and HANDOVER.md
were read. No application imports, pytest/Node/browser tests or workflow results
were executed/verified for this increment. All tests are supplied, not claimed
passed. Run the new HTTP/browser modules, existing recovery/archive and editor
regressions, then full workflows and review exact tested SHAs/results.

The existing recovery guide is updated with UI instructions and development
limitations. README.md was reviewed; established editor workflows remain intact,
and no complete bug-2/deployment claim is added. Final README/API/usage integration
remains part of closure after archive portability is implemented. The workspace
itself prominently warns that ZIP backup/restore/duplication do not yet preserve
archives. Do not deploy against valuable campaign data. Keep bug 2 open.
Remaining work includes portability/legacy normalization, migration/reconciliation
and strict-save test expansion/execution, broader UI/browser acceptance, exact CI
evidence review and final documentation. Existing historical records/manifests
are unchanged; HANDOVER.md adds a short link only. No Patch/ material is included.
