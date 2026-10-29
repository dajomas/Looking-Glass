# Importing Foundry VTT walls

## Supported files (auto-detected)

| Source | How to get it | Notes |
|---|---|---|
| **Scene export JSON** (recommended, v9–v13+) | Foundry: Scenes sidebar → right-click scene → **Export Data** | Contains `width`, `height`, `padding`, `grid`, `background.offsetX/Y` and `walls[]`, so alignment is automatic |
| Adventure / compendium JSON with `scenes[]` | Exported adventure / unpacked compendium | You pick a scene in the editor |
| NeDB `scenes.db` (Foundry ≤ v10) | `Data/worlds/<world>/data/scenes.db` | One scene per line; you pick one |
| NeDB `walls.db` / JSON list of wall docs | e.g. macro output `canvas.scene.walls.toObject()` | No scene metadata, so alignment defaults to offset 0, scale 1 |
| Universal VTT `.dd2vtt` / `.uvtt` / `.df2vtt` | Dungeondraft, DungeonFog, Arkenforge… | `line_of_sight` polylines + `portals` (doors) |

Foundry v11+ worlds use **LevelDB directories**, which can't be uploaded
directly. Use *Export Data* on the scene, or unpack with the official CLI:
`fvtt package unpack -n <world> --type World` gives JSON per scene.

## NeDB record histories

NeDB newline-delimited records are replayed in file order. A document with an
`_id` replaces that ID's current document. A record with a truthy `$$deleted`
value removes it; a later document can recreate the same ID. Deleting an absent
ID has no effect. Identified records require non-empty string IDs; malformed
IDs produce an import error. IDs are case-sensitive and are not trimmed.

Non-deleted documents without `_id` are retained independently. Anonymous
deletion records and non-object lines are ignored. Live identified documents
are returned in insertion order, followed by anonymous documents in source
order. Updating an ID keeps its position; deleting and recreating it inserts it
after the other live IDs. Wall sets without usable segments are omitted. A direct
import with no usable walls reports `No walls found`; a ZIP with no supported
wall sets reports the ZIP import error.

This replay applies to NeDB record histories, including histories inside ZIP
packs. A complete JSON object or array follows JSON import rules, not NeDB replay.
Saved source bytes and walls already copied to maps are not rewritten by parsing;
review the selected wall set before explicitly applying it to an existing map.

## Select a wall set and reuse the database

A database may contain many scenes, including variants of the same location.
Looking Glass treats each parsed, non-empty scene as an independent wall set;
it does not merge all scenes into one geometry.

1. Open **Saved wall sources** in the map editor’s left sidebar. For instructions, expand **? Help → Saved wall sources**, then one of its five collapsed subsections.
2. Save the `.db` or JSON source. Saving validates the file but changes no walls.
3. Select the saved source, then the desired wall set by scene name. Counts and
   original source positions help distinguish variants and duplicate names.
   Wall sets are shown alphabetically by name, ignoring case, with natural
   numeric ordering. Equal names retain original source-index order.
4. Choose whether to auto-align, then select **Apply selected wall set** to replace the current map’s walls.
5. On another battle map in the same campaign, select the saved database again
   and choose the same or another wall set. The file is not uploaded again.

If the source is supplied while creating a map, it is saved automatically.
Single-set sources are applied immediately. Multi-set sources wait for explicit
selection in the editor. Sources saved before a restart remain available after
restart. Existing one-off editor imports are not retroactively saved; save the
file once through the library to make it reusable.

Auto-alignment is calculated separately for each target image. Disabling it
keeps the map's current offset and scale. Each apply replaces only the target
map's walls, retaining its door setting and fog history. Blank players before
changing walls during play: replaying old fog actions with new walls can reveal
different areas. Reset fog and inspect the player preview as needed.

The source is immutable. Identical bytes uploaded twice within a campaign reuse
one entry (and its original filename); edited bytes create another entry even if
the filename is the same. Source IDs in the menu distinguish identical filenames.
Deleting a source does not delete walls already copied to maps. Deleting the
campaign removes its saved sources. To reuse across campaigns, save the same
file separately in each campaign; no cross-campaign sharing is enabled.

Sources live as BLOBs in the application database, obey the existing per-file
upload limit, and are included in database backups. There is no aggregate source
quota; remove unused uploads if storage growth matters. LevelDB directories are
still unsupported. The `.db` suffix alone does not imply SQLite support.

## Wall types

| Foundry wall | Stored as | Splits areas? |
|---|---|---|
| Normal (move + sight) | `wall` | yes |
| Door (`door: 1`, not locked) | `door` | per-map toggle **Doors split areas** (default on) |
| Locked door (`door: 1`, `ds: 2`) | `locked_door` | same door boundary toggle; unlock does not reveal |
| Secret door (`door: 2`) | `secret` | same toggle |
| Limited sight / window / terrain | `window` | yes |
| Invisible (blocks movement, not sight) | `invisible` | yes |
| Ethereal (blocks nothing) | `ethereal` | no |

v9 values (`move` 0/1, `sense` 0/1/2) and v10+ values (0/10/20/30/40) are both
understood.

## Alignment

Foundry draws the scene inside a padded canvas, so wall coordinates include
that padding. Looking Glass computes

```
offset = ceil(width × padding / grid) × grid  +  background.offsetX   (same for Y)
scale  = image_width / scene_width                                   (same for Y)
image  = (wall − offset) × scale
```

This means a map image exported at 2× (e.g. 140 px/grid art in a 70 px/grid
scene) still lines up. If walls appear shifted, open **Alignment** in the
editor. Nudge with the arrow buttons (Shift = 10 px) or type values, then
press **Apply alignment**. The preview updates instantly. Fog is recalculated
when you apply.

## Numeric geometry and calibration

Converted wall coordinates, scene origins and derived coordinates must be finite.
Explicit scene dimensions, grid sizes, UVTT pixels-per-grid and map sizes must be
positive and finite; scene padding must be non-negative and finite. Omitted or
null optional size/grid metadata uses the documented defaults. Explicit zero or
negative sizes/scales and nonnumeric grid values are rejected, not defaulted.
Negative coordinates and image offsets are supported, as are finite numeric
strings. Metadata-free wall lists remain supported with unit calibration.

Target-map calibration and the resulting endpoint coordinates are validated before
wall replacement, including when retaining a map's existing calibration. Numeric
values that overflow during padding, scaling or transformation are rejected.
A finite source value alone does not guarantee that its target transform is usable.

A direct numeric validation failure produces an import error. ZIPs retain their
per-entry policy: an invalid entry can be skipped while usable companion entries
are imported; a ZIP with no supported wall sets is rejected. Review the selected
wall set before applying it. Records without usable wall coordinates and
zero-length wall segments retain their wall-list omission behavior.

## Malformed input and partial imports

Expected input failures such as unusable Foundry door conversions, non-iterable
wall/geometry containers, non-object UVTT resolution/origin/size metadata and
malformed portal records or endpoints produce an import error. Portal endpoints
used to form a segment must be objects containing both `x` and `y`.

This validation does not impose a new strict schema on all inputs. Existing
falsy/default handling and iterable filtering remain, as do omission of unusable
Foundry coordinates, filtering of incomplete standard-UVTT polyline points and
ignoring portal bounds too short to form a segment. Numeric and calibration rules
above still apply. Saved source bytes and existing map walls are not repaired.

ZIP validation remains per entry, not all-or-nothing: malformed entries can be
skipped while usable companions import. An invalid-only pack is rejected. Review
the resulting wall sets and original source indexes before applying geometry.

When creating a map with accompanying walls, an invalid wall import can leave
the successfully imported map and report that its walls were not imported. A
source rejected during parsing is not saved; if parsing succeeds and a later
target-calibration/application check rejects it, the already saved source can
remain available. Explicit wall imports and source inspections report rejection
instead of treating the upload as a successful wall replacement. File-size errors
outside wall parsing and image-file cleanup have their existing separate behavior.

## Tips for clean areas

- Walls only need to *nearly* meet. Lines are drawn `fog.wall_thickness` px
  thick at work resolution, which closes small gaps.
- If one click reveals more than `fog.leak_warn_fraction` of the map, the
  editor warns about a probable leak. Press **Ctrl+Z**, find the gap (walls
  overlay), and fix it in Foundry or with the alignment tools.
- Without walls, the entire map is one area. **Reveal all** and **Reset** still
  work.

A demo map and matching scene export are in `docs/examples/`
(`demo-crypt.png`, `fvtt-Scene-demo-crypt.json`). The image is 1.5× the scene
size, with 25 % padding.

## Pack artwork and consistent screens

In Saved wall sources, save a `.db`, JSON, Universal VTT, or `.zip` pack,
select its wall set, and, when the optional pack-image controls are present,
tick **Use image from this wall set on BOTH screens** before applying. If those
controls are absent, wall selection still works and applying retains your
current artwork. Unticked (the default) also retains your current artwork.
Selection is reset when changing wall sets, preventing accidental reuse of a
previous image choice. Applying replaces this map's walls; it does not alter
other maps using the saved source.

Supported artwork is a Foundry `background.src` or legacy `img` data URI,
a Universal VTT base64 `image`, or a referenced file included in a ZIP alongside
scene exports. ZIP references are matched by their full pack-root path or a
path relative to the scene file. Paths are case-sensitive. Nested archives,
absolute/traversal paths and duplicate normalized archive paths are rejected.
ZIPs are limited to 2,000 entries and 150 MiB total expanded content; individual
uploads and decoded images also obey `storage.max_upload_mb`. Unsupported
metadata JSON is skipped. Supported images are validated using the normal
image-import path and pixel limits.

Foundry exports commonly contain only an external path and a small embedded
`thumb`. When only that thumbnail is embedded, it is explicitly labelled as low
resolution and never selected automatically. Upload the full-resolution art or
include it in a ZIP for best results. URLs and local Foundry module paths are
not fetched or read from the server filesystem. Existing databases are reusable
without being uploaded again, because image metadata is parsed from saved bytes.

There is one canonical `maps.image_file` per map, not separate DM/player images.
Every newly imported image is normalized to an oriented, static RGB PNG (first
frame for animated inputs). Both admin artwork and viewer fog compositing use
that file. The viewer may downscale/re-encode it and adds fog; it never receives
an alternate scene image, the raw image endpoint, or wall data. Replacing artwork
updates image dimensions, wall/fog versions and cache keys; admin refreshes its
versioned image URL and viewers receive the existing refresh notification.
The currently selected active map must be the map being compared: another map
can still be edited while the viewer displays the campaign's active map.

Auto-align uses the selected image dimensions. Disable auto-align to preserve
manual offsets/scales. Applying artwork or changing boundaries retains fog
history and replays it against the new geometry; blank the viewer first and
reset fog if old reveals are inappropriate. Source deletion leaves copied map
artwork and walls intact.

## Wall legend and type controls

| Type | Overlay | Boundary behavior when enabled |
|---|---|---|
| Normal wall | Magenta solid | Blocks areas |
| Door | Blue solid | Blocks when Doors split areas is on |
| Locked Door | Orange dashed | Same boundary rule; double-click its arrow to unlock only |
| Unlocked Door | Orange solid | Same boundary rule; double-click to lock |
| Secret door | Purple dashed | Same boundary rule |
| Window / terrain | Green solid | Blocks areas |
| Invisible wall | Yellow dashed | Blocks areas |
| Ethereal | Grey dashed | Never blocks (source semantics) |

Each legend row has **Show** (DM overlay only, page-local) and **Enabled**
(persistent per-map boundary participation). Press **Apply wall types** to save
the Enabled switches and recalculate fog on the server. Disabled categories
remain stored and visible at reduced opacity unless Show is unticked, so they
can be re-enabled without re-import. Ethereal can be toggled but remains
non-blocking even when enabled. The global Show walls checkbox still hides all
overlays. The existing Doors split areas toggle is an additional gate for both
door categories. Filters are independent of source selection and survive
re-import. Disabling boundaries can merge rooms and expand prior reveals;
confirmation warns to blank the viewer before recalculating.

## Wall-set ordering and import identity

Alphabetical sorting changes only the saved-source dropdown's presentation.
Each option retains the parser's original zero-based `scene_index`; the number
in square brackets is its original one-based source position, not its sorted
position. Duplicate scene names remain separate selectable wall sets. Saved
source bytes and backend scene ordering are not rewritten. The separate
one-off file-import scene selector is unchanged by this patch.


## Locked and unlocked doors

Foundry ordinary doors with `ds: 2` are classified as Locked Door; other ordinary doors retain Door classification, and secret doors remain secret. Manually authored Locked/Unlocked Door types round-trip through the existing Looking Glass UVTT extension, including saved reusable sources. Standard UVTT fallback exports either as a closed portal, without promising that third-party importers preserve the lock distinction. The wall editor exports the authored design rather than runtime session overrides.

## Passage graph round-tripping

Foundry classification is unchanged: normal locked doors import as locked_door,
secret doors as secret (default after=door). Configure secret outcomes and actual
teleport pairs in the wall editor. A standard UVTT `portals` record still denotes
an ordinary door, not a Looking Glass teleport pair.

Looking Glass extension v2 preserves authored pair IDs, side roles, routes and
Entry initial/post-discovery states. Existing v1 files remain supported. A whole
pair must occur in one wall set/map; invalid graphs are rejected atomically.
Runtime discovery/locks are not exported. Standard fallback uses opaque boundaries
for teleport elements, preserving geometry but not teleport behavior. No third-party
teleport compatibility is claimed. See Passages.md.
