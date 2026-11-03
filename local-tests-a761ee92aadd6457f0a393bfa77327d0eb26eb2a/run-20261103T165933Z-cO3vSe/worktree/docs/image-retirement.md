# Retired artwork maintenance

## Artwork retirement

Map deletion, campaign deletion and HTTP campaign restore register old original
and alternate paths in the transaction removing their references. Alternate
replacement registers its old alternate before the upsert. First uploads have
no previous alternate. Files stay readable until explicit offline collection.
Failed mutations roll back registration and database changes together. Existing
new-file failure cleanup and original-image replacement keep their contracts.

## Serving ownership and limitations

Use one normal `python python/main.py serve` process per local database/maps/cache
installation. On POSIX the CLI holds shared storage_use ownership before server
setup, through both listeners, asyncio.run and worker-executor shutdown. The
collector requires exclusive nonblocking ownership: it refuses while that server
is running, and server startup refuses while collection holds the lock. Server
exceptions are not disguised as lock-acquisition failures.

Use a local filesystem with reliable POSIX flock semantics. This is not a
distributed lease or support for shared-cache multi-server operation. Never
remove/replace maps/.image-retirement.lock or rename/replace storage during use.
Without fcntl, serving retains its previous behavior but collection refuses;
do not bypass that refusal.

Older versions, direct ASGI applications, direct server.build/server.serve calls
and standalone service/backup readers do not implicitly hold this lock. Stop ALL
of them before collection. Custom launchers must hold storage_use across path
selection, response/file consumption and worker shutdown. The confirmation flag
acknowledges this obligation; it cannot detect arbitrary uncoordinated readers.
External filesystem mutation is outside this safety model.

## Procedure

1. Stop all servers and standalone readers. Stopping only one listener is not enough.
2. Back up the stopped installation's complete database and map storage.
3. Use its Python environment and identical configuration:

```bash
PYTHONPATH=python python -m looking_glass.services.image_retirement \
  -c /etc/looking-glass/config.yaml --confirm-stopped
```

Omit -c only when default/environment settings select the correct installation.
The database must already exist; collection does not migrate it. Review the
removed/missing/referenced/blocked counts. Busy ownership, unsupported locking or
operational/database errors fail the command; blocked candidates return exit 1.
Referenced paths remain queued. Resolve failures, rerun, then restart serving.
Ordinary requests, startup, context construction and account CLI commands never
run destructive collection. Disk use can grow until maintenance.

## Candidate selection and retry

Only registered known paths are considered. No filesystem scan adopts arbitrary
untracked files, including artwork leaked before the fix. There is no historical
backfill; recovery ZIPs are not collection candidates.

The local image_retirements table is operational bookkeeping, transactionally
created on first use. Portable campaign ZIPs and clean duplication exclude it;
full stopped database backups include it. No applied migration or portable
schema/version changes.

With exclusive cooperating ownership, collection holds BEGIN IMMEDIATE across
checks of maps.image_file and double_reveal_maps.image_file, unlink and queue
removal. Duplicates are deduplicated. Active references, unsafe paths, symlinks
and failed unlinks remain queued. Missing files make retry idempotent, including
unlink followed by commit failure. This is not an fsync/power-loss guarantee.
Blocked/referenced files can remain indefinitely. Original replacement's immediate
unlink and existing failed-new-file cancellation/crash windows are not redesigned.

See [validation and current status](handover/073-bug-15-route-cli-integration-2026-10-31.md).
