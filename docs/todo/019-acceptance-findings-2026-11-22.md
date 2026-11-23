# Acceptance findings: bugs 30–31 and improvement I1 (2026-11-22)

Found during manual acceptance of bugs 1 and 3–12 on `features/claude` at
`fdcd1af` (Python 3.14, Firefox 160, demo-crypt map). Evidence is in
`Runbook results/` and handover record 102. Status: open; reproduce against live
code, agree a minimal solution and add a regression first, as for bugs 16–29.

Suggested order: **31 → 30 → I1**. 31 is a small loader change. 30 touches fog
rendering and needs pixel regressions across formats. I1 is a UX change.

## 30. Doorway sliver of hidden-side artwork on the player image

- [x] Implementation delivered on `features/claude` on 2026-11-23; see handover record 103. Acceptance pending.
- Status (original): open. Split from bug 1, which is closed.
- Evidence: `Runbook results/Runbook A - Point 4.{png,jpg,webp}` (3000×2100).
  With one room revealed, 2–3 px of the hidden corridor's door-edge artwork show
  beyond the top and left door openings (source values 126/109, player 72–97, so
  about 60–75 % brightness). Identical in PNG, so not a compression artefact.
  Solid walls show at most a 1 px transition; hidden interiors are exact fog.
- Probable cause (unconfirmed): the revealed mask includes the full width of its
  bounding wall/door strokes (`fog.wall_thickness` at work resolution, then a
  nearest-neighbour resize to the map size). On a door line the stroke straddles
  the opening, so its outer half covers hidden-side artwork.
- Proposed solution: clip revealed wall/door support to the revealed room's side,
  or exclude door-opening stroke pixels outside the room, without dropping the
  bounding walls bug 1 deliberately keeps.
- Regression: one revealed room with doors on several sides; every pixel beyond
  the door line on the hidden side equals the fog colour, for PNG, JPEG and WebP,
  at default and large `feather_px`, and at a non-integer work-to-map scale.

## 31. Invalid fog colour crashes startup with a raw traceback

- [x] Implementation delivered on `features/claude` on 2026-11-23; see handover record 103. Acceptance pending.
- Status (original): open. Follows bug 24, whose shape validation does not check leaf values.
- Evidence: `Runbook results/Runbook A - Point 6.txt`. Unquoted
  `fog_color: #808080` is a YAML comment, so the value is null. `_hex_to_rgb()`
  in `services/fog.py` then raises `ValueError: invalid literal for int() with
  base 16: 'No'` from inside server startup.
- Proposed solution: validate colour values (`fog.fog_color` and any other
  colour keys) as `#rgb`/`#rrggbb` in the config loader, and fail before
  bootstrap with a source/section/key message that suggests quoting. Consider the
  same treatment for other typed leaves bug 24 left out of scope.
- Regression: null, unquoted-comment, non-hex and wrong-length colours abort CLI
  startup with an actionable message and no database writes; valid 3- and 6-digit
  colours still load.

## I1. After a forced password change, continue to the map

- [x] Implementation delivered on `features/claude` on 2026-11-23; see handover record 103. Acceptance pending.
- Status (original): open improvement, agreed by the user on 2026-11-22. Not a bug.
- Today `POST /account` always redirects to `/account?ok=Account+updated`, so a
  player whose change was forced must open the map from the header themselves.
- Proposed solution: when the change clears `must_change_password`, redirect to
  the portal's start page (viewer `/`, which forwards to the only campaign) or a
  validated local `next`, with the success message. Ordinary account edits keep
  today's behaviour.
- Regression: forced change → lands on the map and live updates arrive; ordinary
  display-name or voluntary password change → stays on `/account`; an external
  or backslash `next` is never followed.
