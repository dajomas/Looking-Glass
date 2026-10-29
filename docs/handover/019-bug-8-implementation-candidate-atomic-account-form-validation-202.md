## Bug 8 implementation candidate: atomic account form validation (2026-10-29)

Baseline: features/perplexity at 960a142d0ce8e55ff661c1a5a9fa8fb5e28efe14.
Bug 7 is delivered in 07c5e8b9debad7c2fa7a3362e804c76d2cc30746, documented in
3c770fd4b90f375e5dac4c177cb85e674f7ce58a and recorded in TODO at this baseline.
Earlier candidate/open wording above is historical; HTTP/ASGI acceptance is still pending.

Re-read live auth_routes.py, db.py, users/sessions repositories, security/RBAC,
README and HANDOVER. Auth baseline blob: 7993723ffec510e819989ad21c0c35129c53dfb5.
Complete documentation recovered from the supplied bug 7 draft matched current
live blobs a71319556b61a170f8cf14780b701c7aa285b6dd and
144ca4717ead0c7e96c65905f9b0a96243193d89 respectively; preserve those exact prefixes.

Root cause: account_submit wrote display_name before password validation; returning
an error response normally caused Database.connect to commit that earlier write.
The sole runtime change moves users_repo.update(display_name=...) to the end of
the existing connection block. All existing password validations now precede every
write. Valid password/flag updates, other-session revocation and the profile write
remain in the same transaction, so write exceptions roll back the whole update.
Profile-only behavior, validation messages/order, current-session retention,
HTTP dependencies/CSRF, logout and bugs 5-7 are unchanged. No new API, migration,
configuration, dependency or frontend change is introduced. Deleted-user races
and unrelated account/session policy are not redesigned in this scoped fix.

Validation executed on Python 3.12.8 / pytest 8.3.5, plugin autoload disabled:
- New isolated tests on verified baseline: 18 failed, 14 passed (4.24 seconds).
- Candidate isolated tests: all 32 passed (4.27 seconds).
- Final focused modules: 32 passed, 1 module skipped (4.30 seconds).
  The skipped module contains 26 HTTP cases; FastAPI is unavailable.
- The changed runtime file and both new test files compiled successfully.

The isolated loader preserves the actual account_submit function body, removes its
routing decorator and postpones annotations. SQLite, user/session repository logic
and scrypt hashing/verification are real; the SQLite context wrapper models the
observed commit-on-return/rollback-on-error contract. Request/settings/render and
redirect boundaries are doubles. Tests use a minimal auth schema, not application
migrations or the actual Database wrapper. Verified live support modules are not
part of the proposed repository write. This is not HTTP/dependency-injection execution.

Both portal cookie identities are covered: four password validation errors with
required-change on/off, forced-change empty-password failure, valid profile-only
save, valid password/flag update, current-session retention, same/cross-portal
session revocation and unrelated-user isolation. Failure tests compare all user
and session rows; the four validation-error cases also assert no INSERT/UPDATE/DELETE.
Injected post-write errors in set_password, delete_for_user and profile update,
and an injected commit-boundary failure, verify rollback of all fields and sessions.

The 26 included HTTP cases remain unexecuted: failed password forms with/without
required-change, empty forced-change password, profile-only success, valid password
success and invalid CSRF behavior across both real application portals.
Run with normal runtime/development dependencies:
`PYTHONPATH=python python -m pytest -q python/tests/test_account_atomicity.py python/tests/test_account_atomicity_web.py`
No broader suite, browser, live-server or Python 3.14 acceptance was run. Execute
the HTTP module without skips and verify both portal workflows on deployment before
calling the change integration-validated. Existing bug 7 tests were not rerun here;
its viewer API, tests and runtime gate are excluded from all proposed replacements.

Implementation/documentation are prepared only; no bug 8 repository write has
occurred at preparation. TODO item 8 remains open until approved delivery; then
record the delivered SHA and pending HTTP/deployment acceptance. Earlier split-
delivery exceptions do not apply to bug 8. No archive or Patch/ material is proposed.


