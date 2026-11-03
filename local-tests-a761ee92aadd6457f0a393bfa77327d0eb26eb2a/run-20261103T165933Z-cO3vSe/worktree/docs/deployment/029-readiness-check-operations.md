## Readiness-check operations

Campaign readiness is available to campaign managers through **Check campaign**. No new
configuration, migration or dependency is required. Restart the application after applying
updated Python/templates. Existing admin/viewer ports remain unchanged (viewer 5100 by default).

Checks decode images, build topology where notes/endpoints exist and serialize the current
backup payload in memory. Run large campaigns outside active preparation/editing and allow
adequate memory/time. Checks use a SQLite read snapshot with query-only enforcement but
cannot freeze map files against concurrent replacements. They do not write cache images.

Expanded backup content is compared with `storage.max_upload_mb`; serialization includes
base64 wall-source overhead. Missing/unreadable images make the size result incomplete.
Compressed upload size, reverse-proxy limits, free disk space, archive compatibility and
actual restore execution are not validated. Readiness is not a replacement for restore
rehearsals or full instance backups. Revert the changed files to roll back; no database
migration needs reversing.

