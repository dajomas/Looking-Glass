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

## Documentation change and evidence limits

This documentation-only change adds this record and updates the Current
repository directives in HANDOVER.md. No application code, tests, CI
configuration or existing handover records were changed, and no tests or CI
were run.
