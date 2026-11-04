# Bug 16 and bug 23: accepted closures

## Current status (2026-11-04)

Bugs 16 and 23 are accepted and closed. The initial implementation and validation
sections below retain their 2026-11-03 context, including historical pending
statements. The dated bug 23 acceptance section at the end supersedes those
pending statements; it does not rewrite the original evidence limits.

## Bug 16: accepted and closed

The user accepted closure on 2026-11-03 after the clean local test run. This
record supersedes acceptance-pending statements in the historical
[implementation record](080-bug-16-manual-calibration-2026-11-03.md).
The finite-field and transformed-wall validation, transaction sequencing,
calibration module extraction and unchanged public endpoint are accepted within
that documented scope. No new implementation change for bug 16 is included here.

Evidence: tested source `de227d408e5f143520e38293f2d336dd07dc1a8a`, stored at
commit `66902ef76a88b010aaa5aae768625c461d7b9733`, directory
`local-tests-de227d4/run-20261103T180051Z-UkyaPD/`. Summary and validation reports
show Python / HTTP 1,445 cases, JavaScript 28 scripts, browser 172, live 18 and
recovery 6, with zero reported failures/errors/skips. Recovery includes the two
real container cases and selected /usr/bin/podman. Environment: Python 3.14.7,
Node 22.23.2, WSL2; execution used native /tmp scratch and an independent Git root.
This is local evidence, not a new GitHub Actions run or deployed-production,
other-platform, multi-process or exhaustive numerical validation claim.

## Bug 23: implementation; acceptance pending

`config.load_settings` now distinguishes no explicit selector from an explicit
argument or LG_CONFIG. An argument has precedence even if empty (empty is now
an error, not an implicit request for environment/default fallback). Explicit
files are opened without a prior exists-based fallback. Missing paths, broken
symlinks, directories and permission failures propagate standard file-open
exceptions with the OS reason and failing path. Environment overrides and
in-memory overrides cannot rescue invalid explicit selections.

No explicit selector still optionally discovers REPO_ROOT/config.yaml; an absent
default uses defaults/environment as before. Valid empty YAML files remain valid.
Relative path semantics and setting precedence are otherwise unchanged. No
schema/range validation, YAML-structure repair, migration, launcher change or
bug 24 implementation is included. CLI load_settings precedes ensure_dirs,
storage-use locking and DB migration, so a load failure cannot reach those steps.
Existing CLI exception presentation is retained; no new clean-error UI is claimed.

## Validation performed for bug 23

The reconstructed original config.py matched live Git blob
`6ed4407741c3707ba5372bdb95dbe92a6ea3d007`. In an isolated Python 3.12.8 sandbox,
14 loader pytest cases gave 7 failures/7 passes on baseline and 14 passes on the
candidate. The complete actual loader, real PyYAML/filesystem and pytest were
used, with the disabled Scrying Glass options hook doubled to avoid importing
the rest of the application. Permission denial was injected via Path.open;
this does not claim OS account-permission enforcement was tested. Model/default
path selection, file errors, precedence and absence of loader writes were checked.
The candidate and test files were parsed for syntax.

Two CLI subprocess no-storage-creation cases were prepared but not executed.
The normal Python 3.14 runtime, serve/bootstrap integration, existing suites,
browser/live/recovery jobs and CI have not been rerun for bug 23. It remains
acceptance pending until those results are reviewed. The local success used for
bug 16 predates this config change and is not evidence for bug 23.

## Documentation and delivery scope

TODO.md closes 16 and records 23 pending; 19 remains closed. All other bug statuses
are unchanged. Release notes distinguish accepted fixes from candidates. The
native-installation guide documents required explicit config files. README.md
was reviewed; its optional quick-start config and deployment link remain valid,
so it needs no edit. HANDOVER.md indexes this record. All proposed files are below
25,000 bytes. Existing historical records/manifests and prior evidence are not
modified. No CI-skip marker is requested.

## Bug 23: accepted closure (2026-11-04)

The user accepted closure following successful CI and local evidence. Bug 23,
"Explicit missing configuration silently falls back to defaults", is closed on
features/perplexity. The accepted fix was delivered in
`5232cc70fbc6816858f4d1b7eedf78a577976e2b`. Acceptance covers explicit argument /
LG_CONFIG selection, missing/unreadable/directory/broken-link failures, empty
selector rejection, retained optional default discovery and retained setting
precedence. It does not close bug 24 or broaden configuration-shape validation.
No migration or further implementation change accompanies this closure.

CI: GitHub Actions run 41723122486, attempt 1, tested
`5232cc70fbc6816858f4d1b7eedf78a577976e2b`. run.json at evidence commit
`63c47bacb747af8d47b168fd95e3dd9661c167cc`, directory
`ci-results-41723122486-attempt-1/`, reports overall success and all five jobs
successful: Python / HTTP, JavaScript regressions, Browser / mocked HTTP,
Live Uvicorn and Recovery. CI job metadata was reviewed, not each JUnit case.

Local confirmation: tested source `dad8972c40aecfc38147f027c8ff454b7ef31e8c`,
evidence commit `4b06c21ece6644dc46d4043fa72f5358857a79cc`, directory
`local-tests-dad8972/run-20261104T192351Z-LncxLZ/`. Summary and per-suite validation
reports show Python / HTTP 1,473 cases, JavaScript 28 script cases, browser 172,
live 18 and recovery 6, with zero reported failures/errors/skips in every group.
The workspace identity record confirms requested, expected and actual source IDs
all match the full tested commit. The finalized evidence includes finish time
and scratch-cleanup confirmation. Environment: Python 3.14.7, Node 22.23.2, WSL2;
19:23:51 to 19:31:36 UTC on 2026-11-04. This local run is distinct from the CI run.

Evidence was reviewed, not re-executed for this documentation commit. No new
production deployment, other-platform, every-filesystem permission semantics,
serve-path fault injection or exhaustive configuration validation is claimed.
The original permission-denial regression uses an injected Path.open failure.
The accepted no-fallback behavior and supplied loader/CLI regressions remain
bounded by those evidence limits.

TODO.md now closes 23; release notes classify it as an accepted fix; HANDOVER.md
labels this entry as accepted closures. README.md and the deployment guide were
reviewed and already describe compatible configuration usage, so need no edit.
Only these four documentation files change. Other bugs, historical audit text,
original split manifests and test evidence are unchanged. All changed files are
below 25,000 bytes. No tests were run for this documentation-only closure.
