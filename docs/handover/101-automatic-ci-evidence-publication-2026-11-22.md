# Automatic CI evidence publication (2026-11-22)

## Change

The user copied `.github/workflows/publish-ci-results.yml` and
`tools/publish_ci_results.sh` from the Scrying Glass repository (commit
38edef0). Claude adapted them to Looking Glass:

- Trigger workflow name `Branch tests` → `Looking Glass integration tests`;
  required run path `.github/workflows/tests.yml` →
  `.github/workflows/integration-tests.yml`.
- Allowed branches reduced from the Scrying Glass list
  (perplexity/claude and their `-statblock` variants) to `features/claude`,
  the only branch whose pushes trigger the integration workflow.
- After the symlink check, the collector now creates and verifies lossless
  `reader-chunks/` with the trusted collector's `tools/chunk_ci_evidence.py`,
  so automatic evidence matches the layout `getworkflow.sh` produces and
  earlier handover records cite.

`docs/ci-tests.md` documents the behavior and prerequisites.

## Prerequisites and limits

- GitHub only runs `workflow_run` workflows from the default branch, and the
  job checks out `main` for the collector and chunker. Nothing is published
  until the workflow and both tools are on `main`; the user will push to main.
- `features/claude` must allow `GITHUB_TOKEN` pushes (no blocking protection).
- Pull-request and manual-dispatch runs are not published.
- Each publication removes older root `ci-results-*` directories in the
  evidence commit; history keeps them.
- `collection.txt` contains a timestamp, so a re-run of the same attempt
  commits again instead of reporting identical evidence.

## Validation

- `bash -n` on the script and YAML parse of the workflow.
- Local end-to-end run of the script with a stubbed `gh` and a local bare
  remote: published a new `ci-results-42-attempt-1` with verified reader
  chunks and removed an older collection; rejected a disallowed branch and a
  SHA mismatch (exit 1); left the remote unchanged when newer evidence was
  already published.
- Not executed: a real GitHub Actions run, real `gh` API responses, artifact
  downloads or `GITHUB_TOKEN` push permissions.

## Update 2026-11-23: chunking removed

At the user's request, `tools/publish_ci_results.sh` no longer creates or
verifies `reader-chunks/`; published evidence contains the raw files only. The
chunker is no longer needed on `main` for publication. `getworkflow.sh` and
`tools/chunk_ci_evidence.py` are unchanged. Validation: `bash -n` and a local end-to-end run with a stubbed `gh` and a local remote (evidence published, no `reader-chunks/`); the
user will push the change to `main`, which is where the collector runs from.
