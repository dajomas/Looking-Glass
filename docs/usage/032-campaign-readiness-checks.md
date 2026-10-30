## Campaign readiness checks

Open a campaign and select **Check campaign**. Checks run on demand, not on every
campaign-page load. The report groups errors, warnings and informational findings and
provides **Inspect map (DM only)** links. Select **Run checks again** after changes.

The report checks:
- Map image storage containment, readability/full decoding and stored dimensions.
- Maps without walls (informational; an open map can be intentional).
- Cross-map passage endpoint bounds, wall-pixel placement, missing destinations,
  out-of-campaign destinations and same-map connections.
- Saved room-note anchors and geometry signatures against current effective boundaries.
- Current expanded backup content size and restore archive-entry count limits.

Arrival-only endpoints without outgoing links are informational, not errors. Secret,
blocked and approval-required passages are valid configurations, not readiness errors.
Wall-pixel placement is advisory: travel can resolve nearby open pixels.

Checks never repair content, remove stale notes, activate a map, change fog or notify
viewers. Inspection opens a separate read-only DM page highlighting the reported point;
out-of-bounds points are drawn at the nearest edge without changing stored coordinates.
The inspection page lists endpoint and room-note anchors and links to editors for manual
review. Deliberately opening an editor leaves read-only inspection; existing editor
behavior, including room-note reconciliation, still applies.

The report is scoped to the selected campaign and restricted to its owning admin or a
superadmin. Results describe the current snapshot, not a guarantee of campaign readiness.
File changes during a run can affect results. Checks use current runtime door states,
calibration and enabled wall types; they do not predict every possible passage state.

