# Bug 16 closure and bug 23 configuration candidate (2026-11-03)

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
