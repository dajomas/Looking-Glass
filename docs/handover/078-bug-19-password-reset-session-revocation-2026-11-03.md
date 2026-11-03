# Bug 19: password-reset session revocation (2026-11-03)

## Decision and change

Bug 19 from the second bug hunt is implemented on `features/perplexity`; acceptance
is pending. `reset_password` in `python/looking_glass/web/admin/users.py` now
deletes every session of the reset user. When a superadmin resets their own
password, only the requesting admin session token is retained; the user's viewer
sessions and every other session are revoked. The route then disconnects that
user's viewer sockets after the database transaction has committed.

Resetting another user's password still revokes all of that user's sessions and
disconnects their sockets. Validation failures, unknown users, CSRF failures and
transaction failures must not write or disconnect. `sessions.delete_for_user`
already supported `keep_token`; the existing account-page password change keeps
its behavior.

## Files

- `python/looking_glass/web/admin/users.py`
- `python/tests/test_password_reset_revocation.py` (isolated tests)
- `python/tests/test_password_reset_revocation_web.py` (HTTP/WebSocket tests)

README.md was reviewed and needs no change. The historical audit record
`docs/todo/018-bugs-16-29-audit-2026-10-31.md` still describes the audited
commit and was not edited; this record is the status record for bug 19. All files
in this change are below 25,000 bytes.

## Validation performed

The live `users.py` blob `ec2b7d66bbd6db24da8ab43e72849bd47188da37` was verified
against a reconstruction of the unchanged file. In an isolated sandbox using
Python 3.12.8, pytest and `--noconftest`, the final isolated regression tests gave
3 behavioral failures and 4 passes against the unchanged route, then all 7
passed against the fixed route. An earlier test-harness attempt failed because
it passed a request argument unsupported by the old signature; the final helper
handles both signatures, so the baseline failures demonstrate behavior rather
than that signature mismatch. The tests use real SQLite plus AST-loaded route
and session-deletion bodies, with user, password and hub doubles.

## Not validated

The HTTP/WebSocket test file was written from the existing test helpers but was
not executed. The complete Python suite, normal repository checkout, Python 3.14,
browser/live suites and CI were not run. This record does not claim acceptance.
The web tests need an initial run and possible fixture adjustment in a normal
environment. No other second-bug-hunt finding was changed.
