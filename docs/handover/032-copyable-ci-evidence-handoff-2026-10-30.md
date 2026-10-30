## Copyable CI evidence handoff (2026-10-30)

After a successful `getworkflow.sh --publish` push, the script prints the
user-requested message with the selected run's databaseId, its tested headSha,
and the current evidence commit SHA from `git rev-parse HEAD`. The output has a
blank line between the run/tested-commit sentence and current-commit sentence.
It is terminal output only: no self-referential commit hash is written into the
evidence. Local-only collection, cancelled publication and failed pushes do not
print this published-evidence handoff. Existing collection and publishing logic
is unchanged. README.md was reviewed; its workflow overview remains accurate.
No script execution, shell syntax check or live publication test was performed
by the assistant for this output-only change.

