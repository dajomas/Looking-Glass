## Clean duplication form endpoints

- `POST /campaigns/{campaign_id}/duplicate`: form `name` (1–120 characters),
  session + CSRF, source campaign management and campaign creation permission.
  Creates a campaign owned by the caller and redirects there with HTTP 303.
- `POST /maps/{map_id}/duplicate`: form `name`, session + CSRF and map/campaign
  management permission. Copies into the same campaign, then redirects to the new editor.

Both are explicit create operations, not backup restores. They reset all play state,
copy independent image files, and remap copied passage endpoints. Links leaving a
single-map selection are detached. No viewer notification/publication occurs.
On image/storage/database failure, rollback and file cleanup precede an error redirect.

