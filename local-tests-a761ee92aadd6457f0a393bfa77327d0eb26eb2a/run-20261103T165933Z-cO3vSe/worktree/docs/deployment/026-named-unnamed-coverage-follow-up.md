## Named / unnamed coverage follow-up

Incremental patch targets e75d505. Deploy changed Python/template/CSS and the new
JS file, restart backend and refresh the editor (asset versions updated). No
migration, configuration or dependency changes. Like the edit marker, coverage
uses data:image/png sources, so external admin CSP must allow data: images. Restore
baseline code and refresh for rollback; no saved data is changed by this feature.

