# Bugs 1 and 3–12: accepted closure and acceptance findings (2026-11-22)

## Decision

On 2026-11-22 the user explicitly accepted and closed bugs 1 and 3–12. A
doorway sliver found while checking bug 1 is logged as new bug 30 instead of
keeping bug 1 open. Bug 31 and improvement I1 were also agreed. All are recorded
in `docs/todo/019-acceptance-findings-2026-11-22.md` and `TODO.md`.

## Automated evidence

GitHub Actions run 45063111967, attempt 1, tested `fdcd1af` on
`features/claude` (Python 3.14.10). The only difference from `03b07f6` is the
user's `testingtest.txt` trigger file. Evidence was published automatically to
`ci-results-45063111967-attempt-1/` in `e33f1eb`, with verified reader chunks.

| Suite | Result |
| --- | --- |
| Python / HTTP | 1,907 passed, 29 subtests passed |
| Browser / mocked HTTP (Chromium) | 172 passed |
| JavaScript | 35 passed |
| Live Uvicorn | 18 passed |
| Recovery (CLI and Docker container) | 6 passed |

No failures, errors or skips; the CI audit fails on any skip. Per-bug cases,
all passed: bug 1 fog privacy/fog 25 plus live adjacent-room pixel check; bug 3
JavaScript refresh, 7 browser delayed-response cases and live reconnect; bug 4
14; bug 5 18 plus live logout revocation; bug 6 24 plus live assignment,
deactivation and role-change revocation; bug 7 26 including the WebSocket/ASGI
module that was previously unexecuted; bug 8 58; bug 9 17; bug 10 32; bug 11
170; bug 12 192.

## Manual acceptance

The user ran the Manual Acceptance Runbook (a Claude doc, outside the
repository) on a disposable Python 3.14 instance of `features/claude` with
Firefox 160. Screenshots and notes are in `Runbook results/` (commit 925769b).

- **Runbook A, bug 1 (PNG, JPEG, WebP; feather 2 and 8).** Claude compared the
  saved player images with `docs/examples/demo-crypt.png`. Revealed-room pixels
  match the source exactly; every pixel more than 30 px outside the room is
  exact fog in all three formats; Undo left no ghost. A 2–3 px sliver of the
  hidden corridor's door-edge artwork shows beyond door openings at about
  60–75 % brightness, identical in PNG. Logged as bug 30. The grey-fog step
  failed because the runbook omitted YAML quotes; the resulting startup crash is
  logged as bug 31.
- **Runbook B, bug 7.** B1: a forced-change account is redirected to `/account`
  and kept there from `/c/<id>`; a new socket is refused at the handshake with
  HTTP 403 (browser close code 1006) and never opens; after the change the probe
  opens and live updates resume. The user marked two B1 checks failed against
  runbook expectations that were wrong (expected code 4403 for a pre-accept
  refusal; expected a redirect to the map). The runbook was corrected and the
  redirect is logged as improvement I1. B2: an open socket closed with 4403
  after the flag was set directly in the database, with no updates while
  flagged. B3: admin reset with forced change revoked the socket; logout from
  `/account` worked.
- **Runbook C, deployment behind a reverse proxy (bugs 3, 5–9, 20, 21).** All
  checks passed on both portals: backend ports closed and unknown hosts
  rejected; login with Secure/HttpOnly cookies; foreign, null and missing Origin
  rejected with 403; login return target kept local; live reveal/hide through
  the proxy, 10-minute idle and app restart; socket closed on logout,
  unassignment and deactivation; login lockout applied per client IP.

## Limits

- Manual checks covered one map, one browser family per runbook and the user's
  own proxy topology; other proxies, multi-hop TLS and browser engines remain
  unverified.
- B2's measured close delay was not recorded.
- Bug 30 is open; until it is fixed, a door opening can show 2–3 px of the
  hidden side's door-edge artwork.
- This closure changes documentation and status only. No code, tests or CI
  configuration changed and no tests were rerun for this commit.
