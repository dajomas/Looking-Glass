# Release notes

This file records user-visible changes on `features/perplexity` for a future
release. Detailed decisions and evidence limits live in
[the handover records](../HANDOVER.md); earlier changes are recorded there and
are not summarized here.

## Unreleased

### Fixed

- **Malformed multipart CSRF tokens are rejected safely (bug 22, accepted).**
  File-valued csrf_token fields are rejected through the existing Forbidden
  response before token comparison, rather than causing a server error. Valid
  string tokens, header precedence and empty-header form fallback are retained.
  No migration is required.
- **Admin editor state refreshes reject obsolete responses (bug 25, accepted).**
  Map-state reads share request-generation guards with action/state installation.
  Starting an editor action invalidates earlier reads, polling waits while busy,
  and a changed map cache-token identity triggers refresh even with equal fog
  and wall revisions. Tokens identify map incarnations and are not sorted.
- **Admin fog and arrow masks reject obsolete decodes and errors (bug 26, accepted).**
  Returning to an already installed mask invalidates pending loads of another
  mask. Both images must decode and still match the current generation and
  state identity before installation. Superseded errors cannot replace current
  feedback; current failures retain Retry loading map guidance. Wall rendering
  was extracted into a focused module without changing its controls.
- **Login return URLs stay local (bug 20, accepted).** Both successful login
  and already-authenticated login-page visits reject unsafe return targets,
  including slash/backslash and encoded path variants. Accepted local URLs keep
  their original query/fragment representation; excessive or invalid path
  encoding falls back conservatively to /.
- **Login submissions require a same-origin source (bug 21, accepted).** Origin
  must match the receiving portal's scheme, hostname and effective port; Referer
  is a fallback only when Origin is absent. Missing, opaque/null, malformed,
  duplicate and cross-origin source headers are rejected. Existing authenticated
  mutation CSRF protection is unchanged. Test clients were aligned without
  weakening password/session/socket or security rejection assertions.
- **Original-image replacement retains superseded artwork safely (bugs 17/18, accepted).**
  The old original is registered for retirement in the replacement transaction
  instead of being deleted online after commit. Previously selected reader
  paths remain available until coordinated offline collection, and old-file
  unlink failures no longer interrupt post-commit fog invalidation and viewer
  notification. Compatibility checks and failed-new-file cleanup are retained.
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
- Login automation must supply the exact receiving portal Origin. Reverse
  proxies must preserve the external Host/port and trusted external scheme and
  must not strip or manufacture browser source headers. Both source headers
  absent means login is rejected. See [networking and login-origin deployment](deployment/004-3-networking.md#login-origin-protection-and-proxy-trust).
- Superseded original images now consume disk until explicit offline collection.
  Stop all readers and use the installation's configuration before maintenance;
  see [retired artwork maintenance](image-retirement.md).
- Ensure an explicitly configured file is present and readable; remove empty
  LG_CONFIG assignments instead of using them to request defaults.
- After a self-reset, sign in again on other browsers and on the viewer portal.
- Socket disconnect notifications are process-local; other processes observe
  the revocation through their normal session checks. Data already in flight
  cannot be recalled.

### Verification

Bug 22 is accepted and closed by user request on 2026-11-06. CI run
42177604548 attempt 1 passed all five jobs on
`2e9894386d49310d994cb1ce0b40632e12d5e2f1`, with all 20 multipart CSRF HTTP
cases explicitly passing. The published local all-suite summary for
`54625531e5f469d7c871f80f5ed06333cbdc31ee` records zero test/report exit codes
for all five groups; the user also reported a targeted 20-case local pass.
These are distinct tested revisions. See [accepted closure, evidence locations
and review limits](handover/098-bug-22-multipart-csrf-2026-11-06.md#accepted-closure-2026-11-06).
Parser-level malformed bodies and duplicate-token policy are outside this fix.

Bugs 25/26 are accepted and closed after CI run 42055860962 attempt 1 passed
all five jobs and their report-validation steps on
`2a4a9f9175936b3a01002c84732ba31716a0c2df`. Reviewed report totals: Python/HTTP
1,635 tests, JavaScript 31 scripts, browser 172 tests, live 18 tests and recovery
6 tests, each with zero failures/errors/skipped tests. Evidence is stored at
`8b0a747dc79af96c04f103246817bd5bd35433ae` under
`ci-results-42055860962-attempt-1/`. The JavaScript-only local rerun also passed
31 scripts on that tested source; it is not an all-suite local run of that SHA.
Passing integration coverage does not establish every admin response interleaving
or add server-side stale-context protection to ordinary coordinate actions. See
[accepted closure and evidence limits](handover/091-bugs-25-26-accepted-closure-2026-11-05.md).

Bugs 20/21 are accepted after CI run 42003087572 attempt 1 passed all five jobs
and their report-validation steps on c734226657ee556ff86f42883decc15c8499f389.
The clean local run tested e17fbae2696eda27bed26daebc29a8a8f06747ce; evidence
commit ca93d96f6ecfda0683fc816631def211d2929d13 reports Python 1,593 cases,
JavaScript 28 scripts, browser 172, live 18 and recovery 6, all with zero
reported failures/errors/skips. CI/local tested revisions are distinct. These
results do not assert real nginx/TLS deployment or every browser/proxy topology
was tested. See [accepted closure and historical evidence links](handover/086-bugs-20-21-accepted-closure-2026-11-05.md).

Bugs 17 and 18 are accepted using GitHub Actions run 41906927331, attempt 1,
on tested source `d0375c3cf72058268f79b9fc9fcae28ce8a51818`: overall success and
all five jobs successful, including their report-validation steps. CI evidence
is stored at `240c557b8e77eeabf37128fcd02f4558c08857f0` under
`ci-results-41906927331-attempt-1/`. The full local run tested the same source;
evidence commit `432264823456a9cded97cc633c271765343db1fb` reports Python 1,476
cases, JavaScript 28 scripts, browser 172, live 18 and recovery 6, with zero
reported failures/errors/skips in every group. These counts are from the local
reports, not a separate recount of CI JUnit cases. See
[accepted closure and evidence limits](handover/085-bugs-17-18-accepted-closure-2026-11-04.md).

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
