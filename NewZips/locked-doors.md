# Locked and unlocked doors

## Design and appearance

The two wall kinds are `locked_door` and `unlocked_door`. Choose them in the dedicated wall editor's Add/Change type menus or Edit dialog and save the wall set. Locked Door is dashed orange; Unlocked Door is solid orange. Orange is `#ff9f43`. Both retain the doubled screen-pixel door stroke width in both admin editors.

Both types have Show and Enabled legend controls. Show affects only the local DM overlay. During play a runtime-changed door retains the boundary participation of its **designed category**, not its temporary effective category. Both still obey Doors split areas and their stored blocking flag. This prevents unlocking/locking from merging rooms or exposing additional pixels when the two category settings differ. To change actual boundary design, edit/save walls or change the designed category's Enabled setting explicitly; inspect the player preview after boundary changes.

## Arrows and actions

Locked door arrows default to the same orange as locked door walls. A separate **Locked door arrow color** picker in the fog controls overrides their color per map, on both admin and viewer images. Unlocked door arrows use the regular Door arrow color picker, not orange. The existing shared arrow enable toggle controls all arrow kinds. Secret doors still generate no hints.

| Effective door type | Primary single click | Primary double click |
|---|---|---|
| Locked Door segment | No change | No change: unlock using its arrow |
| Locked Door arrow | No change | Change to Unlocked Door; fog is unchanged |
| Unlocked Door arrow | Reveal the adjacent hidden room | Change to Locked Door; fog is unchanged |
| Unlocked Door segment | Reveal the adjacent hidden room if a currently valid arrow exists for that door; otherwise no change | Change to Locked Door; fog is unchanged |
| Regular Door arrow | Existing reveal behavior | No new lock-state feature |

All state-changing actions are on the admin fog editor only. Viewers see the updated server-rendered arrows but remain read-only. Right-click retains inverse-mode behavior for unlocked/regular doors; locked door hits do nothing. Primary single clicks on managed doors wait **500 ms**. A second primary tap on the same door in that window cancels the single and executes only the double action. This application window does not read OS/browser double-click timing. A newer map state, another map operation, drag, wheel movement, focus loss or another target cancels a pending tap. Zoom/pan coordinates and raster-arrow hits are revalidated server-side.

Unlocking never means opening a passage in the fog topology: the door remains an area boundary until an ordinary reveal action reveals the neighboring room. Locking does not hide rooms already revealed. These are DM interaction controls, not access-control restrictions: the DM may still reveal an area manually or use Reveal all.

## Designed and session state

`walls.kind` stores the authored design. `door_runtime_states` stores temporary per-wall overrides with cascading deletion. The fog editor shows effective state; the dedicated wall editor and saved-set export load designed state. Single-clicking an unlocked arrow adds one normal reveal, so Undo works for the reveal. Lock/unlock changes do not add fog operations and are not reverted by fog Undo.

Toolbar Reset covers fog and clears runtime overrides, restoring each door to its own designed state. The Show-map Reset option also clears overrides while retaining its existing fog-history reset behavior. A door designed unlocked becomes unlocked again on Reset; Reset does not lock every door. Undoing a toolbar fog Reset restores fog history, not the discarded runtime overrides. Restore/checkpoint semantics for fog are unchanged; runtime states persist per map until Reset or a design replacement.

Saving/reimporting/replacing walls establishes the new design and drops runtime overrides attached to the replaced wall IDs. Download alone does not change runtime state. Deleting a wall or map cascades its overrides. No runtime play changes modify immutable saved source uploads.

## API and storage

Migration **8** adds `maps.locked_door_arrow_color` (default `#ff9f43`) and `door_runtime_states(wall_id,kind)`. Migrations 1–7 are unchanged. `WallSegment` gains keyword-only, equality-neutral `id` and `designed_kind` metadata; existing six-value serialized wall rows and positional constructors remain supported.

`POST /api/maps/{id}/door-arrows` additionally accepts `locked_color`, a six-digit hexadecimal color string. Omitted/null values preserve the existing setting. Existing `color` and `enabled` fields keep their meaning. The normalized color is returned as `locked_door_arrow_color` and participates in render cache identity.

Admin map payloads additionally contain `managed_doors` (IDs/effective kinds/calibrated endpoints) and `door_arrows` (IDs/effective kinds/work-coordinate polygons). No hidden target point is supplied to the browser. These fields are not added to the viewer API.

`POST /api/maps/{id}/door-action` accepts:

```json
{
  "wall_id": 9,
  "hit": "arrow",
  "gesture": "double",
  "x": 175.5,
  "y": 100.5,
  "tolerance": 10,
  "cache_token": "map-incarnation-token",
  "walls_version": 1,
  "fog_version": 1
}
```

The endpoint requires normal campaign-management authorization and CSRF. `hit` is `arrow` or `wall`; `gesture` is `single` or `double`. Arrow coordinates identify a visible raster pixel, not a requested destination. Wall hits use point-to-segment distance with a bounded image-pixel tolerance (the UI uses 10 screen pixels). Under `BEGIN IMMEDIATE` the server checks authorization, incarnation, both versions, the wall's map/type and current actual hit before choosing the action. Stale, disabled-arrow, mismatched-ID and invalid hits make no mutation. Response `door_action` is `none`, `lock`, `unlock` or `reveal` plus the normal updated map payload. Ignored valid hits return `none` without changing versions/history or broadcasting.

Lock/unlock bumps wall/fog versions to invalidate caches and stale click stamps, but does not append reveal history or change snapshots. A reveal updates normal fog history/checkpoints. After commit, changed maps use the existing live notification path. The legacy arrow-reveal endpoint explicitly excludes locked arrows, preventing that endpoint from revealing through a locked arrow.

## Import/export

Foundry ordinary doors with `door:1, ds:2` import as Locked Door. Other ordinary doors keep their regular Door classification, and secret doors remain secret. Looking Glass UVTT extension rows losslessly preserve both new designed types. Core UVTT fallback uses closed portals for both, so other VTTs may lose the lock distinction; no new third-party lock compatibility is claimed. Export uses designed, not temporary session, types.

## Installation and limits

Apply the incremental archive over development commit `cb32190c53cdc982847e628e8b211cf62b3816e9` (the viewer center/fit update). Stop both processes and back up the database/data first. Extract replacement files at repository root; restart normally for migration 8 and reload admin tabs. New script/CSS version URLs prevent stale editor assets. Viewer center/fit functionality is not replaced by this patch.

Run the complete suite in the project's installed environment and perform the manual checks in `Patch/locked-doors.md`. The generation of arrows retains the existing raster-resolution, gap and tight-room limitations. Roll back using the matching previous code/database backup; no down-migration is supplied.
