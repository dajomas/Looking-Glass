## Campaign search and generic inspection

Admin-only authenticated GET routes, all requiring campaign-management access:

| Route | Response |
|---|---|
| `/campaigns/{campaign_id}/search` | Full HTML search page |
| `/api/campaigns/{campaign_id}/search` | JSON for quick-navigation dialog |
| `/campaigns/{campaign_id}/inspect/maps/{map_id}` | Generic read-only DM inspection |

Search accepts `q` (up to 200 characters, default blank) and `kind` (`all`, `map`, `room`,
`passage`, `library`; default `all`). Invalid type/length is rejected with HTTP 422.
JSON returns `query`, `kind`, `results`, `truncated`, `limit`. Each result includes
`kind`, `key`, `map_id`, `map_name`, `title`, `snippet`, and an internal inspection `url`.
Snippets are at most 222 characters including ellipses. Results are capped at 50 and
ranked; `truncated` means additional matches exist, not an exact total count.

Inspection accepts `kind` (`map` by default) and an object `key` (up to 200 characters).
Room keys are geometry signatures, passage keys endpoint IDs, library keys row IDs.
The object is resolved within the selected map after campaign/map access checks. Missing
or mismatched objects return 404. Stored coordinates take precedence for selected room
or passage targets; library entries have no authored location. Existing readiness
inspection URLs remain supported. Optional x/y markers retain their prior behavior.

Both search variants and inspection return `Cache-Control: no-store`. Query-only SQLite
snapshots enforce no database writes. GETs require no CSRF because they have no state
changes. No new viewer routes or player-control endpoints are exposed.

