## Replace prior CI collections (2026-10-30)

The collector now cleans prior root collection directories before downloading a
new run, after validating run metadata and refusing an existing new output path.
Names must exactly match `ci-results-<digits>` or the attempt-suffixed form.
Every invocation requires a clean working tree/index on features/perplexity;
publishing additionally retains the up-to-date-origin safeguards. The script
lists exact cleanup targets and starting HEAD and requires typing `remove`.
Symlink/non-directory matches and ignored files inside a collection block
cleanup. A second safety check runs after confirmation. Unrelated names and
noncollection files are not cleanup targets. The removed directory list is
recorded in the new collection report before reader chunks are generated.

Local-only collection leaves old tracked deletions unstaged and does not change
GitHub. With --publish, a separate publish prompt explicitly includes prior
removals; a guard permits only those expected tracked deletions before staging.
`git add -A` is limited to the new evidence path and the listed old paths, so
old tracked files are deleted in the same commit that adds the new collection.
The existing copyable run/tested-SHA/current-SHA handoff remains unchanged.
No force push, history rewrite, Actions artifact removal or automatic rollback
is performed. Failure/cancellation after cleanup leaves local deletions for
review; recover tracked old contents from the printed starting commit as needed.
A partial run is dirty and must be reviewed before retrying. Current-branch
cleanup does not shrink historical Git storage or erase old evidence commits.

Five isolated temporary-Git scenarios passed: clean matching removal plus staged
and committed deletion/history recovery, dirty-tree refusal, symlink refusal,
ignored-file refusal and no matching collections; nonmatching similarly named
data was preserved. These checks exercised the cleanup/staging logic rather
than the complete collector. Full collector execution, network download,
chunking integration, interactive prompts and remote publishing were not tested
by the assistant. README.md was reviewed and remains accurate; docs/ci-tests.md
now documents retention, destructive prompts, local-only effects and recovery.
This implementation commit itself removes no existing evidence files; deletion
occurs only when the updated script is run and its cleanup is confirmed.

