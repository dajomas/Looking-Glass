# Bugs 30, 31 and improvement I1: implementation (2026-11-23)

The user asked on 2026-11-23 for bugs 31 and 30 and improvement I1 to be done
together. All three are delivered on `features/claude` in one commit; each
has its own regression tests. Acceptance is pending.

## Bug 31: invalid fog colour

- `config.py`: new `ConfigError(ValueError)`. After all merging (file, environment,
  overrides) `_validate_values()` requires `fog.fog_color` to be a string matching
  `#?rgb` or `#?rrggbb` (the `#` stays optional, as `_hex_to_rgb()` accepted). The
  message names the source file, `'fog.fog_color'` and the value; for `None` it
  explains YAML comments and shows the quoted form. Bug 24 shape errors now also
  raise `ConfigError`.
- `cli.py`: `main()` catches `ConfigError`, prints `Configuration error: ...` to
  stderr and returns 2 without a traceback. Loading still precedes any storage,
  migration or bootstrap write.
- `config.example.yaml` reminds users to keep the quotes.
- Tests: `test_config_values.py` (unit: invalid forms, quoting hint, valid forms,
  defaults and overrides) and `test_config_values_cli.py` (subprocess: `serve`
  and `list-users` exit 2, no traceback, nothing written).
- Not changed: other typed leaves (ports, numbers, booleans) remain outside
  loader validation, as for bug 24.

## Bug 30: doorway sliver

- Cause confirmed: `FogEngine.mask()` grew revealed interiors by
  `wall_thickness` steps into wall pixels, so the full width of each bounding
  stroke was shown, and the stroke straddles its line.
- Fix: stroke pixels are shown only when at least one pixel nearer revealed
  interiors than hidden ones (`_nearer_revealed`). Distances are chamfer
  transforms in a box around the candidates: city-block to revealed pixels
  (never under-counts Euclidean distance) and chessboard to hidden pixels (never
  over-counts it), so uncertain pixels stay fogged. The one-pixel margin covers
  a work pixel spanning several map pixels, and the wider round caps at wall
  ends. Walls between two revealed rooms are unchanged.
- Visible effect: the room-side edge of a wall bordering a hidden room is about
  1–2 map px narrower; the line and the hidden side stay fogged.
- Tests: new `test_fog_doorway_privacy.py`. It reproduced the bug first (54/54
  parameter cases leaked) and covers door and wall lines, PNG/JPEG/WebP,
  feather 0/2/8 and work-to-map scales 1, 0.683 and 0.323. Two existing
  assertions encoded the old behaviour and were updated with bug 30 comments:
  `test_fog.py::test_click_reveals_only_that_room` (now the room-side wall pixel
  is shown and the line is fogged) and
  `test_fog_privacy.py::test_dilation_never_reveals_another_open_component`
  (a one-pixel wall equidistant from a hidden room stays fogged; both-revealed
  shows everything).
- Real-map check (`docs/examples/demo-crypt.png` with its Foundry walls, the
  room revealed in the 2026-11-22 runbook): before the fix the door pixels were
  75/84 and 72/97/97, matching the user's screenshots; after it they are fog.
- Cost: mask build for that room went from about 28 ms to 45–70 ms, and for
  the large outside area to about 80 ms. The full player-image render was
  about 350 ms per reveal both before and after.

## I1: continue after a forced password change

- `auth_routes.py`: `account_url()` builds `/account?next=<encoded>` from a
  `_safe_next()`-validated destination (plain `/account` for `/`). A forced
  login uses it. The `/account` page takes `next` and the form posts it back as a
  hidden field only while a change is required (also after a failed submit).
  A successful forced change redirects to `_safe_next(next)`, so `/` by default;
  voluntary changes still go to `/account?ok=Account+updated`.
- `errors.py`: the forced-change redirect for GET pages carries the requested
  path and query as `next`; other methods go to `/account`.
- The viewer start page already forwards a one-campaign player to the map.
- Tests: new `test_forced_change_continue_web.py` (login destination, direct
  link, no destination, unsafe destinations including `//`, backslash,
  absolute, encoded and `javascript:`, failed submit keeps the destination,
  voluntary changes unchanged on both portals, admin portal). Updated
  assertions: `test_web.py`, `test_account_atomicity_web.py`,
  `test_viewer_password_gate_web.py`, and the `test_account_atomicity.py`
  harness, which now also compiles `_safe_next`.

## Validation in this session

The workspace has Python 3.13 without FastAPI or bleach. With a local `bleach`
stub (not committed), the non-web suite showed no new failures against a
baseline of the previous commit: 1,498 passed, all remaining failures the
known environment gaps. Fog tests 80/80, config tests 211/211 and account
atomicity unit tests 32/32 passed. The CLI path was checked by calling
`cli.main()` directly. Web, browser, live and recovery suites, and the CLI
subprocess tests (which require Python 3.14), were not run here; the
integration workflow on this push is the evidence for them.
