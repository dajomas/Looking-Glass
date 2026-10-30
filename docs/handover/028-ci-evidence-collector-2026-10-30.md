## CI evidence collector (2026-10-30)

`bash getworkflow.sh [RUN_ID] [--publish]` collects the latest completed
integration workflow run, or an explicit run, from `features/perplexity`.
It preserves metadata, tested SHA, attempt-specific logs, run-scoped artifacts,
download diagnostics and a collection report in a new run/attempt directory.
Missing logs/artifacts are recorded as warnings, not proof of successful tests.
Default operation is local collection only. Publishing requires a clean,
up-to-date working branch, the expected origin push URL and typed confirmation;
only the evidence directory is staged. Evidence commits use `[skip ci]` to
avoid push-triggered runs; skipped required checks can affect PR merge gates.
Review evidence for secrets before publishing. Failed pushes leave the local
commit intact; there is no automatic rebase or force-push. Alternate origin URL
forms are rejected conservatively. Artifact downloads are not attempt-filtered;
verify contained environment SHAs and provenance after reruns. Existing output
directories are never overwritten. Runtime, GitHub CLI integration and shell
syntax validation have not been executed by the assistant for this change.
README.md was reviewed; its existing CI overview remains accurate and unchanged.

