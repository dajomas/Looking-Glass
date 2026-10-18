# Map controls update

The update retains dropdown selections, implements independent wall-type overlay
and boundary controls, hardens editor image/state loading, warns on offline
reveals, and centers player display framing on the union of revealed pixels.

The production blank-editor symptom was not reproduced against a live backend.
Tests exercise complete rendered editor markup, real image decoding, real SVG
paths and pan/zoom; they also inject a metadata failure and verify artwork remains
visible and Retry recovers walls. Clear diagnostics replace a silent empty page.
A genuinely missing image, authorization error, unrepaired schema or server crash
still needs its underlying cause corrected. This is not a database reset script.

Schema 4 is a new separate per-map settings table. It does not renumber or rerun
migration 3. Fresh databases and version-3 upgrades are covered by focused tests.
The previous schema collision's cache-token/checkpoint repair remains a prerequisite
for deployments that encountered it. Legacy disabled_wall_types is not deleted;
its values are used until overwritten intentionally by Apply wall types.

Show is local/browser-scoped and never changes server boundaries. Enabled changes
boundaries only after Apply, persists server-side and leaves raw segments intact.
Ethereal remains non-blocking; door categories also honor Doors split areas.
Replaying old fog operations after disabling walls can expose more area, so blank
players first. The user-requested immediate Apply behavior is preserved.

Viewer bounds are based only on the revealed mask. They add no hidden wall data.
All visible regions are framed together; the last-clicked room is not privileged.
Automatic framing occurs on each new map/fog version, while pan/zoom remains usable
between updates. Fully hidden maps use full-map framing.
