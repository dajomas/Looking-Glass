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

## Select a wall set and reuse the database

A database may contain many scenes, including variants of the same location.
Looking Glass treats each parsed, non-empty scene as an independent wall set;
it does not merge all scenes into one geometry.

1. Open **Walls → Saved wall sources** in a map editor.
2. Save the `.db` or JSON source. Saving validates the file but changes no walls.
3. Select the saved source, then the desired wall set by scene name. Counts and
   list positions help distinguish variants and duplicate names.
4. Choose whether to auto-align, then apply and confirm replacement.
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
| Door (`door: 1`) | `door` | per-map toggle **Doors split areas** (default on) |
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
