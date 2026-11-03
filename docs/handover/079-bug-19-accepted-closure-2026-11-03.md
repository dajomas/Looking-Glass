# Bug 19: accepted closure and evidence limits (2026-11-03)

## Decision

Bug 19, "Superadmin self-reset leaves other sessions valid", is closed on
`features/perplexity`. The fix, its history and the intermediate CI failures are
recorded in [the implementation record](078-bug-19-password-reset-session-revocation-2026-11-03.md),
which remains an accurate historical account and was not rewritten.

Behavior now accepted: an administrator password reset deletes every session of
the reset user and disconnects that user's viewer sockets after the database
transaction commits. When a superadmin resets their own password, only the
requesting admin session token is retained. Resetting another user's password
still revokes all of that user's sessions. Rejected resets and transaction
failures neither write nor disconnect. Production changes are limited to
`python/looking_glass/web/admin/users.py`.

## Acceptance evidence

GitHub Actions run 41672983791, attempt 1, tested commit
`b5317f4c54f48f83dbd252cf71e056bb64bdd51f`. Its evidence was committed at
`52163fb9b276e6c2f1206e24519301bfb84653a0` under
`ci-results-41672983791-attempt-1/`.

- Run conclusion: success. Python / HTTP, JavaScript regressions, Browser /
  mocked HTTP, Live Uvicorn and Recovery all report success.
- Python / HTTP: 1,392 passed and 29 subtests passed, with no reported failure.
- All 7 isolated regressions in `test_password_reset_revocation.py` passed.
- All 7 HTTP/WebSocket regressions in `test_password_reset_revocation_web.py`
  passed, including all four self-reset / forced-password-change combinations
  that failed in earlier runs.

Earlier runs 41669728699 and 41671623697 failed only at test-fixture assertions
(mounted-path JSON handling and the forced-change account path). Those causes
and corrections are documented in the implementation record; no production
authentication behavior was changed to accommodate them.

## Evidence limits

The evidence is the repository's GitHub Actions workflow. This closure does not
claim local execution, a deployed installation, multi-process behavior, other
operating systems or browser engines. As documented in the README, immediate
disconnect notifications are process-local, other processes observe revocation
through their checks, and in-flight network data cannot be recalled. Job-level
results for the non-Python suites were verified from run metadata rather than
per-test inventories.

## Documentation scope

README.md now states the administrator reset behavior. New
[release notes](../release-notes.md) summarize the user-visible change. TODO.md
records bug 19 as closed. The audit record
`docs/todo/018-bugs-16-29-audit-2026-10-31.md` still states the audited commit's
findings and is intentionally unedited. Bugs 16-18 and 20-29 remain open and
unchanged. No file in this change exceeds 25,000 bytes, so no split is required.
