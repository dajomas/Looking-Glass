## Independent admin and viewer arrow visibility

| Admin arrows | Viewer arrows | Result |
|---|---|---|
| On | On | Both displays show eligible arrows. |
| On | Off | DM sees/clicks arrows; players see no arrow hints. |
| Off | On | Players see hints; DM arrow overlay and arrow click targets are hidden. |
| Off | Off | Neither display shows arrows; saved colors are retained. |

These settings affect arrow indicators, not actual door wall segments or the map image. Show walls and per-type Show controls are unchanged. Hiding admin arrows prevents unlocking through a hidden locked arrow; wall segment double-clicks do not toggle passage state. Viewer hints remain noninteractive. The in-editor Player preview (opaque fog) is still the admin overlay with opaque fog; use Open exact player image for the viewer-specific arrow setting.

Both flags survive reloads/restarts and map activation/Reset. Switching visibility does not change designed/runtime door types or fog operations/checkpoints. An admin-only visibility update does not bump the viewer's image version or notify viewers; other admin tabs receive it on the existing 15-second poll. Viewer visibility/color changes use the existing live image refresh. Color inputs are disabled only when both screens are off or saving is in progress. Failed saves restore confirmed values.


