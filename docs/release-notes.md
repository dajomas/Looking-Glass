# Release notes

This file records user-visible changes on `features/perplexity` for a future
release. Detailed decisions and evidence limits live in
[the handover records](../HANDOVER.md); earlier changes are recorded there and
are not summarized here.

## Unreleased

### Fixed

- **Explicit configuration selections fail safely (bug 23, accepted).**
  --config and LG_CONFIG require a readable file and reject empty selectors.
  A missing explicit file no longer silently starts with default settings.
  Missing paths, broken links, directories and permission failures stop settings
  loading before CLI storage creation or database migration. Optional default
  discovery and normal setting precedence are retained. Broader configuration
  structure validation (bug 24) remains separate and is not included.
- **Manual map calibration rejects non-finite geometry (bug 16, accepted).**
  NaN/infinite offsets or scales are rejected. Individually finite inputs whose
  wall-coordinate transform overflows are rejected before mutation, cache
  invalidation or notification. Negative finite offsets remain supported.
  The calibration endpoint was extracted into a focused module without changing
  its public URL. No migration or historical data repair is required.
- **Administrator password resets now revoke the target user's sessions
  consistently.** A superadmin who resets their own password keeps only the
  admin session that made the request. Their other admin sessions and all viewer
  sessions are revoked, and their viewer sockets are disconnected after the
  password change is committed. Resetting another user's password continues to
  revoke all of that user's sessions. Rejected resets (invalid CSRF token, too
  short a password or an unknown user) change nothing and do not disconnect
  sockets.

### Upgrade notes

- No database migration is required for these changes.
- Ensure an explicitly configured file is present and readable; remove empty
  LG_CONFIG assignments instead of using them to request defaults.
- After a self-reset, sign in again on other browsers and on the viewer portal.
- Socket disconnect notifications are process-local; other processes observe
  the revocation through their normal session checks. Data already in flight
  cannot be recalled.

### Verification

Bug 23 is accepted using successful GitHub Actions run 41723122486, attempt 1,
on fix commit `5232cc70fbc6816858f4d1b7eedf78a577976e2b` (all five jobs report
success), plus local source `dad8972c40aecfc38147f027c8ff454b7ef31e8c`, evidence
commit `4b06c21ece6644dc46d4043fa72f5358857a79cc`: Python 1,473 cases, JavaScript
28 scripts, browser 172, live 18, recovery 6, with no reported failures/errors
or skips. See [bug 23 accepted closure and evidence limits](handover/082-bug-16-closure-and-bug-23-config-2026-11-03.md#bug-23-accepted-closure-2026-11-04).

Bug 16 was accepted using local source commit
`de227d408e5f143520e38293f2d336dd07dc1a8a`, evidence commit
`66902ef76a88b010aaa5aae768625c461d7b9733`: all five groups passed with no
reported failures/errors or skips (Python 1,445, JavaScript 28 scripts, browser
172, live 18, recovery 6). This is local WSL2/Podman evidence, not a new CI run.
See [the bug 16 closure record](handover/082-bug-16-closure-and-bug-23-config-2026-11-03.md#bug-16-accepted-and-closed).

Bug 19 was verified by GitHub Actions run 41672983791 (Python / HTTP:
1,392 passed, 29 subtests passed; JavaScript, browser, live and recovery jobs
succeeded). See [the accepted closure](handover/079-bug-19-accepted-closure-2026-11-03.md).
