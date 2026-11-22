# Claude working rules: branch and file-size rule (2026-11-22)

## Decision and scope

The user issued these directives on 2026-11-22. They apply to Claude
(Anthropic) assistant sessions only and supersede any conflicting earlier
handover rules for those sessions. Other assistants and contributors remain
bound by the existing records unless the user says otherwise.

## Working branch

- Claude's working branch is `features/claude`.
- This supersedes the `features/perplexity` working-branch instructions in
  [Repository and agreed working branch](003-repository-and-agreed-working-branch.md)
  and [Assistant workflow and user preferences](009-assistant-workflow-and-user-preferences.md)
  for Claude sessions.
- The other safeguards in record 003 still apply: do not merge to main,
  force-push, reset branches or change other branches without explicit user
  approval.

## File-size rule withdrawn

- The 25,000-byte behavior-preserving split requirement in
  [File-size rule: behavior-preserving splits (2026-11-03)](077-file-size-rule-2026-11-03.md)
  no longer applies to Claude sessions and can be omitted.
- Claude changes are not required to split files because they grow beyond
  25,000 bytes. Ordinary judgment about coherent file structure still applies.
- Record 077 is left unchanged as a historical record.

## Branch reference update (2026-11-22, follow-up commit)

At the user's request, current branch references were changed from
`features/perplexity` to `features/claude`:

- CI: `.github/workflows/integration-tests.yml` push trigger.
- Scripts: `runlocaltests.sh` (publication branch check and push target) and
  `getworkflow.sh` (required checkout branch).
- Test: `python/tests/test_local_runner_publication.py` fixture branch.
- Current guidance: records 003 (working branch line), 007, 009 and 011,
  `docs/todo/001-workflow-and-scope.md` target, `docs/release-notes.md`,
  `docs/ci-tests.md`, `docs/testing.md` and
  `docs/testing/042-github-actions-integration-validation.md`.

Historical records that state where earlier work was audited, delivered or
tested (for example "delivered on `features/perplexity`" with a commit SHA)
are intentionally unchanged, because those statements remain true. Record 003
also keeps its historical notes about how features/perplexity was created.
Split manifests are unchanged, so edited split files no longer match their
split-time hashes; Git history retains the snapshots.

Validation: `bash -n` on both scripts, a YAML parse of the workflow, and
`test_local_runner_publication.py` (7 passed, Python 3.13 in a workspace
without FastAPI/bleach). No other suites, CI runs or real publication were
executed for this change.

## Documentation change and evidence limits

This documentation-only change adds this record and updates the Current
repository directives in HANDOVER.md. No application code, tests, CI
configuration or existing handover records were changed, and no tests or CI
were run.
