## How area reveal works

1. Wall segments are stored **raw** (Foundry scene coordinates). A per-map
   calibration maps them onto the image: `image = (wall − offset) × scale`.
   On import the calibration comes from the scene (padding, background offset
   and image size versus scene size). You can fine-tune it in the editor.
2. `FogEngine.build_area_map` draws the blocking walls as thick lines on a
   "work" bitmap (≤ `fog.work_max_dim` px). It then labels the open pixels into
   4-connected components with `scipy.ndimage.label`. Each component is one
   area enclosed by walls. Doors block by default (toggle per map). Ethereal
   walls never block.
3. A click stores only a **fog operation** (`reveal`/`hide` + point,
   `reveal_all`, `hide_all`) in `fog_ops`. Replaying the ops gives the set of
   revealed labels. That makes undo trivial, and the fog stays correct after
   walls are re-aligned.
4. The revealed mask is dilated by the wall thickness, so the walls around a
   revealed room are visible too. It is then upscaled, feathered and composited
   over the (downscaled) map. The result is cached as
   `data/cache/viewer_<map>_<walls_v>_<fog_v>.webp`.
5. Viewers fetch `/api/c/<id>/state`, then the versioned image URL. Every fog
   change bumps `maps.fog_version` and pushes `{"type":"refresh"}` over the
   WebSocket.

Caches: area labels per `(map, walls_version)` and masks per `(map,
fog_version)` live in in-memory LRU caches. Composite images live on disk.
The heavy work runs in `asyncio.to_thread` behind per-map locks.

