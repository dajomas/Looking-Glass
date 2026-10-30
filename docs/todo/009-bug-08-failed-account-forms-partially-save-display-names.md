### 8. Failed account forms partially save display names
- [x] Implementation delivered on `features/perplexity`; HTTP/deployment acceptance pending.
- Fix commit: `35f749192272bdc3028b08a5f9493ba90160438f`.
- Documentation commit: `704419d7a669fc55ae407090b4b7b79105b7a7d0`.
- Baseline: `960a142d0ce8e55ff661c1a5a9fa8fb5e28efe14`. The user separately
  approved documentation-first, two-commit delivery for bug 8.
- Validation during preparation on Python 3.12.8 / pytest 8.3.5, plugin autoload
  disabled: new isolated regressions produced 18 failures and 14 passes on the
  baseline; all 32 passed on the candidate. Final focused run: 32 passed, one
  skipped module containing 26 HTTP cases; FastAPI is unavailable. All three
  changed/new Python files compiled. SQLite, user/session repositories and scrypt
  verification were real in the isolated tests; a small transaction wrapper
  modeled commit-on-return/rollback-on-error. Route/request/response boundaries
  were isolated; this is not HTTP/dependency-injection execution. No broader suite,
  browser, live-server or Python 3.14 acceptance ran. No tests were rerun during
  GitHub delivery or this TODO-only update; see HANDOVER.md for measured scope.
- Problem: display_name was persisted before password validation, and ordinary
  validation error responses allowed that earlier write to commit.
- Solution: validate all password-change fields before any writes, then update
  password/flag, revoke other sessions and save display_name together in the
  existing transaction. A failure leaves all account/session fields unchanged;
  profile-only updates and current-session retention are preserved. Both portals
  share this handler. No schema, dependency, setting or API change is introduced.
- Test: failures for incorrect current password, too-short, mismatched or unchanged
  new passwords and required-change with an empty new password are read-only.
  Valid profile/password updates preserve the current session, revoke other sessions
  only on password change, clear the required-change flag and retain other users.
  Injected repository write and commit-boundary failures roll back all changes.
- Remaining acceptance: run both new modules with normal dependencies; perform
  HTTP account-form checks on admin and viewer portals, including CSRF, profile-only
  save, failed validation and valid password recovery, then verify on Python 3.14.
  Skipped HTTP cases are not passing integration acceptance.

