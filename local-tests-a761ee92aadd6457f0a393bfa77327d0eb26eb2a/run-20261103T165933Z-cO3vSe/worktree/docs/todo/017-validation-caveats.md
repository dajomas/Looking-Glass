## Validation caveats

Uncommitted candidate results are not evidence of branch fixes. Re-run relevant
tests per delivered item; skipped HTTP/browser checks are not acceptance.
The stale scrying-auto-2 template assertion was reproduced on the untouched
baseline; track it separately rather than silently skipping it or bundling an
unrelated repair merely to make these tests green.
