## Fog editor flash-message placement

`templates/base.html` exposes a `flash_messages` block around the shared flash
partial. Its default preserves the existing placement for other pages.
`web_html/admin/map_editor.html` overrides that block to suppress the default
output and includes the same partial once inside `.editor-flash-messages` under
`#viewport`. Status/alert roles remain defined by the shared partial.

`static/css/admin.css` anchors this wrapper 1.2rem above the viewport bottom,
centered horizontally with a constrained width and wrapping for long text.
The wrapper is outside the transformed map stage, so it does not pan or zoom
with the image. It uses `pointer-events: none` to avoid blocking map input.
The old top-positioned `main.editor > .flash` rule is removed. The editor CSS
query version is bumped to `editor-bottom-flash-12` for cache invalidation.
No API, database, dependency, configuration, or import-processing change is needed.

