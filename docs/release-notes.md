# Release notes

No tagged GitHub release exists for this repository yet. This file records
user-visible changes on `features/perplexity` that are ready to be carried into a
future release. Detailed decisions and validation limits live in
[the handover records](../HANDOVER.md); earlier changes are recorded there and
are not summarized here.

## Unreleased

### Fixed

- **Administrator password resets now revoke the target user's sessions
  consistently.** A superadmin who resets their own password keeps only the
  admin session that made the request. Their other admin sessions and all viewer
  sessions are revoked, and their viewer sockets are disconnected after the
  password change is committed. Resetting another user's password continues to
  revoke all of that user's sessions. Rejected resets (invalid CSRF token, too
  short a password or an unknown user) change nothing and do not disconnect
  sockets.

### Upgrade notes

- No database migration or configuration change is required.
- After a self-reset, sign in again on other browsers and on the viewer portal.
- Socket disconnect notifications are process-local; other processes observe
  the revocation through their normal session checks. Data already in flight
  cannot be recalled.

### Verification

The change was verified by GitHub Actions run 41672983791 (Python / HTTP:
1,392 passed, 29 subtests passed; JavaScript, browser, live and recovery jobs
succeeded). See [the accepted closure](handover/079-bug-19-accepted-closure-2026-11-03.md).
