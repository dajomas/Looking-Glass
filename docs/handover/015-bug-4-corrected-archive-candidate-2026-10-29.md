## Bug 4 corrected archive candidate (2026-10-29)

Explicit baseline: 54cae125d996ceccff6cc61d3942edea88209c4e. All five existing replacement files
(fog service, viewer/admin APIs, README and HANDOVER) were verified byte-for-byte
against GitHub blob hashes at that revision before modification. The supplied
older source bundle was used only as a reconstruction starting point; it was
not accepted as the baseline for those replacements. Existing documentation is
preserved as an exact prefix, including the bug backlog and bug 1/3 records.
Bug 1 and bug 3 implementations are present at this baseline; historical
candidate/open wording above must not be read as their current TODO status.

The entire fog.py implementation change is the addition of viewer_bytes(),
which holds the existing per-map RLock across viewer_image() and read_bytes().
The viewer image and admin preview routes use that helper via asyncio.to_thread
and return Response bytes instead of a deferred FileResponse path. The viewer
post-render access and version checks, media type and no-store header remain.
Bug 1's clipped dilation, nearest-neighbour support, inward-only feathering and
fog-cache-v3-inward-feather identity are unchanged. No bug 3 JS/template files,
TODO status, migrations, configuration or unrelated implementation is replaced.

Validation actually run on Python 3.14.4: focused new service regressions plus
existing fog, bug 1 privacy, door-arrow and viewer-area tests: 73 passed, 1 skipped.
The skipped module contains five HTTP cases; FastAPI is unavailable in this
execution environment. No ASGI integration, full suite, browser or live-server
checks were performed. New service coverage includes PNG/JPEG/WebP bytes after
cleanup, cold/warm map locking against invalidation/new renders, read-failure
lock release and independent map locks. Bug 3 was not retested in this delivery;
its JS/template files are excluded from the overlay and therefore preserved.

Implementation complete as an archive candidate; HTTP and deployment acceptance
remain pending. No GitHub writes or pushes were attempted. Corrected archive
supersedes the earlier stale-baseline bug 4 archive. Do not use that earlier ZIP.
The commit edd5c121f3ee292a6cf3d75dfa8f991c464595c8 contains a bug 1 rollback and
documentation loss; this corrected overlay restores the chosen baseline content
in its replacements while retaining bug 4. Review any other local later edits.

Limitations: per-instance/per-process cleanup coordination only; external file
deletion and shared-cache multi-process locking are outside this fix. Encoded
response bytes consume memory for each concurrent response. No files are deleted
or renamed. Newly generated Patch/ material is archive-only and must be excluded
from git staging; do not remove unrelated pre-existing tracked Patch/ contents.

