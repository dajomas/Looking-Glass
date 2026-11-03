## Clean map/campaign duplication (step 6)

On the campaign page, use Settings → Duplicate campaign to create an independently
owned clean campaign, or the Duplicate map disclosure beside a map to copy it into
the same campaign. Enter a copy name (1–120 non-whitespace characters).

Copies preserve authored map images (independent stored files), calibration, wall
and passage definitions, arrow/marker appearance settings, boundary settings,
room names/notes and imported room-library entries. Campaign copies also preserve
map order, description and saved wall sources. Passage endpoint IDs are regenerated;
connections among copied endpoints are remapped. A single-map copy detaches links
to endpoints outside that map; reconnect them explicitly if desired.

Copies start fully fogged, with no reveal history, last-display fog snapshots,
runtime door/passage/endpoint overrides, travel replay records, or session checkpoints.
A campaign copy belongs to the requesting DM, has no viewer assignments and no
active map. A map copy is appended in its existing campaign and never made active.
The source campaign, its viewer display and its runtime state are unchanged.

The operation requires campaign-management permission and CSRF validation; campaign
copy also requires campaign-creation permission. Database writes share one immediate
transaction. Images created before an error are removed after rollback. No migration,
new dependency, configuration change or port change is required. Large copies hold
the SQLite write transaction while validating and copying images; allow adequate disk
space and avoid concurrent bulk writes. Process termination can leave orphan image
files (as with other multi-resource operations); database commit is still transactional.

