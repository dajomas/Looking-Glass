# Retired artwork maintenance

## Current split-delivery stage

Map deletion, campaign deletion and HTTP campaign restore register old original
and alternate image paths before their references are removed, in the same write
transaction. Successful operations retain these files for existing readers.
Failed mutations roll back retirement registration and database removal together.

Alternate replacement retirement and normal CLI ownership are not integrated
yet; they are steps 3 and 4. Replaced alternates are still deliberately retained
without new retirement registration. Original-image replacement and cleanup of
new files after failed operations retain their existing behavior. This is not
a claim that every prior artwork lifecycle race or crash window is solved.

## Offline ownership requirement

STOP ALL servers and readers before collection: both listeners, older versions,
direct ASGI applications and standalone service/backup readers. The current
normal CLI DOES NOT acquire the shared storage lock. The collector's exclusive
lock therefore does not detect or exclude that uncoordinated serving process.
--confirm-stopped acknowledges this responsibility; it does not prove a stop.

Use one normal serving process per local database/maps/cache installation.
Collection requires a local filesystem with reliable POSIX flock semantics and
refuses on platforms without fcntl. Distributed/network-filesystem locking and
shared-cache multi-server operation are outside this support model. Never remove
or replace maps/.image-retirement.lock or rename/replace storage during use.
Custom cooperating launchers can hold storage_use across their entire reader
lifetime, including path selection, response/file consumption and worker shutdown;
all uncoordinated readers must still be stopped.

## Procedure

1. Stop all serving and standalone readers.
2. Back up the stopped installation's complete database and map storage.
3. Use the installation's Python environment and identical configuration:

```bash
PYTHONPATH=python python -m looking_glass.services.image_retirement \
  -c /etc/looking-glass/config.yaml --confirm-stopped
```

Omit -c only if default/environment settings select the correct installation.
The database must already exist; collection does not migrate it. Review the
removed/missing/referenced/blocked counts. Busy cooperating storage, unsupported
locking or operational/database errors fail the command. Blocked paths return
exit 1; referenced paths remain queued. Resolve causes, rerun and then restart.
Ordinary requests, startup, context construction and account CLI commands do not
run collection. Disk use can grow until explicit maintenance.

## Candidate selection and retry

Only transactionally registered known paths are considered. No filesystem scan
adopts arbitrary existing untracked files, including leaks predating this fix.
There is no historical backfill and recovery ZIPs are not collection candidates.

The installation-local image_retirements table is operational bookkeeping,
created transactionally on first use. It is excluded from portable campaign ZIPs
and clean duplication; full stopped database backups include it. No applied
migration or portable schema/version is changed.

With exclusive cooperating-storage ownership, collection holds BEGIN IMMEDIATE
across checks of both maps.image_file and double_reveal_maps.image_file, unlink
and queue removal. Duplicates are deduplicated. Active references, invalid paths,
symlinks and failed unlinks remain queued. Missing files are acknowledged safely
on retry, including after unlink followed by a database commit failure. This is
not an fsync/power-loss guarantee or protection against external filesystem
mutation. Referenced or blocked candidates can remain indefinitely.

See [the stage and evidence record](handover/073-bug-15-route-cli-integration-2026-10-31.md).
