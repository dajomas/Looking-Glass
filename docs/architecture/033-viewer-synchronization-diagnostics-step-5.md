## Viewer synchronization diagnostics (step 5)

`services/viewer_sync.py` owns the pure-Python per-connection tracker and shared display
version formatter. EventHub registers a record at subscribe and marks it disconnected on
unsubscribe, including failed publish/kick paths. Viewer sockets bind usernames/user IDs
from authenticated server state, not incoming JSON. Only validated loading/ready/failed
reports or keepalive pings advance contact freshness. No new database tables are created.

The manager-only async status route reads the campaign's active target under a SQLite read
transaction and computes diagnostics on the shared event loop. Active map identity/cache
UUID/wall/fog versions use the same formatter as the viewer API; blank is an explicit target.
An old acknowledgement becomes Loading immediately when compared against a new target.
Readiness is not inferred from publish success, image generation, socket count or HTTP 200.
Failed reports take precedence over mismatched versions; closed/stale transport takes
precedence over all rendering states. No play-state changes, caches or events are emitted.

The viewer preserves the existing refresh-generation checks. It reports Loading before
decode, Ready after successful decode and image installation, and Ready/blank after hiding
the stage. Superseded completions/errors cannot report readiness or failure for a later
refresh. Failed state/image requests and decode errors/timeouts report Failed without
exposing exception text. Existing 40-second fallback refresh permits recovery. Reports are
repeated every 25 seconds with keepalives; a 65-second missing-server-message watchdog is
checked at those intervals. No arbitrary image URLs or authored content enter diagnostics.

Manager panels use non-overlapping five-second polls and textContent-only rendering. On
poll failure old rows are cleared; 401/403/404 stops further polling. Page exit stops polls.
Connection records are in-memory, use monotonic time, and expire 90 seconds after disconnect.
Disconnected history is globally capped at 1024 records; oldest entries can disappear earlier.
Open records follow actual sockets; no unique-player or stable cross-reconnect identity is
claimed. Snapshot/report/connect/disconnect calls run on the one shared application loop.
Process restart clears history, matching the application's supported single-process model.

A client report is diagnostic evidence, not trusted proof of physical display visibility.
Browser sleep, timer throttling or a broken transport can lag classification by the heartbeat,
65-second threshold and manager polling interval. It does not provide durable telemetry,
transport delivery guarantees, screenshots, monitoring of the campaign picker or automatic
repairs. Keep complete backup/restore and viewer authorization behavior unchanged.

