# Bug 28: regression-first fog point bounds (2026-11-05)

## Scope and status

The user requested fixing backlog bug 28 after accepting bug 27. Target remains
dajomas/Looking-Glass, features/perplexity. This first increment adds regressions
before changing production behavior. Bug 28 stays open; no application fix,
closure, migration, archive or other branch is included in this commit.

Reviewed live README.md, HANDOVER.md, workflow/file-size directives, original
audit, admin API, fog engine, HTTP fixtures and existing fog tests. The live
_fog_op still passes points to describe_click without image-bound validation.
label_at clamps to edge pixels. _room_at already uses half-open image bounds.
The client check is not a substitute for validation on the authorized API.

## Regression design

python/tests/test_fog_point_bounds_web.py uses existing test_web.env and the
wall-free active-map/viewer setup from test_fog_response_web.prepare. It adds
25 parametrized test cases, not a claimed executed result:

- 20 invalid-point cases: reveal/hide at each edge, exact width/height, small
  negative fractions, beyond the image and two corners on a 400x200 map.
- Three valid-point cases, each performing reveal and hide: zero, interior and
  fractional coordinates just inside the upper bounds.
- One in-map wall snapping control using the existing two-room Foundry fixture.
- One combined missing-CSRF/unauthenticated/other-manager permission control.

Invalid cases deliberately use fully hidden state before reveal and fully
revealed state before hide. Every edge on the wall-free map belongs to an open
area, so clamping cannot hide behind a legitimate no-op or an unrelated wall
error. Tests require HTTP 400 with Point is outside the map., no describe_click
call, unchanged campaigns/maps/fog_ops/map_fog_snapshots rows, unchanged decoded
admin-mask and authorized viewer-image pixels, and no map_changed notification.
Valid controls require changed image pixels, version/history increments, a
matching active-map snapshot and one notification per successful mutation.
The wall control checks the fixture's wall pixel before testing nearest-area
snapping. If HTTP execution exposes a fixture/import/setup failure, correct that
first; do not label it as the intended bug-28 failure.

## Actual validation and limits

The proposed HTTP test source was parsed with Python ast.parse successfully and
measured at 6,308 UTF-8 bytes. No HTTP/application/browser/live/full-suite test or
CI execution occurred in this preparation. Imports, fixtures, SQL checkpoint
assertions and error-envelope behavior therefore still need normal-environment
execution. The new test and documentation files are below 25,000 bytes; no
behavior-preserving split is required for this increment.

A separate sandbox experiment executed the extracted live _fog_op body with
in-memory SQLite, injected dependencies and a synthetic one-area fog double.
The unmodified body mutated in all 20 invalid cases; the candidate bounds guard
rejected all 20 before area lookup, writes/checkpoints or notifications. Six
valid-point controls still performed mutations. This supports the placement of
the guard, not real HTTP routing, the full schema, the actual fog engine or
image rendering. Initial sandbox string/event-loop harness errors were corrected
before obtaining those results; they are not application failures.

## Next implementation and verification

Run the new focused tests in the normal Python 3.14 development environment:

```bash
cd python
../.venv/bin/python -m pytest -q tests/test_fog_point_bounds_web.py
```

Capture the pre-fix baseline and distinguish intended bounds failures from
fixture failures. Then add the narrow _fog_op guard immediately after obtaining
the current spec and before area_map/describe_click:

```python
if not (0 <= point.x < spec.width and 0 <= point.y < spec.height):
    raise BadRequest("Point is outside the map.")
```

Do not change FogEngine.label_at, replay of historical operations, valid in-map
wall snapping, authentication, CSRF or permissions. This does not solve stale
geometry/context protection for otherwise valid ordinary coordinate actions,
which remains a separate limitation. Measure resulting api.py UTF-8 bytes and
split coherently in the same implementation commit if growth exceeds 25,000.
Update the existing API bounds documentation and handover with the actual
implementation/results; rerun focused HTTP and fog tests and the normal CI
suites before acceptance. Do not close bug 28 merely because tests are added.

README.md remains accurate for this test-only increment and is not cosmetically
edited. TODO.md and the historical audit remain unchanged and open for bug 28.
HANDOVER.md links this current record. No [skip ci] is requested for this new
regression-first commit; the previous [skip ci] request applied to bug-27 closure.
Report a commit SHA only after the approved GitHub write succeeds.
