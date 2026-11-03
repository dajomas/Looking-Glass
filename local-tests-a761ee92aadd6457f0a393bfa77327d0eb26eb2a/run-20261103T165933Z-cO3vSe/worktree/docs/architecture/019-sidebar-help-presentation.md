## Sidebar help presentation

`templates/partials/_admin_sidebar_help.html` contains the fog editor’s help copy
and native details/summary disclosures. `web_html/admin/map_editor.html` includes
it near the map selector. No help disclosure has an `open` or `name` attribute,
so all start closed and remain outside the control-panel accordion managed by
`sidebar_sections.js`. The five source-library help subsections nest inside the
Saved wall sources help topic. CSS is scoped to `#editor-help`.

The template hides the passage control wrapper for `siblings|length <= 1`, while
retaining DOM targets required by existing map-transition event bindings. The
passage help topic is conditionally omitted for single-map campaigns. No backend
behavior, schema or API changes are required.

