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
