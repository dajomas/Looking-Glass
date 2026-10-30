## Deploying viewer synchronization status (step 5)

Apply the step 5 delta over uploaded source baseline 7895445 (which already includes step 4).
Preserve local modifications by checking the patch manifest base hashes. Stop the service,
copy changed/new files at repository-relative paths, restart and reload manager/viewer
pages. Static script URLs are versioned for this update. No schema, dependency or settings
change is needed. Old ping-only clients remain Connected but cannot claim Up to date.

Use the supported single-process installation so both portals share EventHub and its
in-memory tracker. A reverse proxy must continue forwarding WebSocket upgrade requests.
The existing keepalive is about 25 seconds; reports become stale after 65 seconds of no
contact and manager polling runs every five seconds. A connection can become reconnecting
before the transport detects it as closed. Background/suspended browsers can cause false
staleness; diagnostics cannot establish TV/display power or physical visibility.

Disconnected rows expire after 90 seconds, with a global cap of 1024 retained rows. Active
records last as long as their sockets; all records vanish on restart. Nothing is written to
SQLite, backups or campaign ZIPs. There is no new telemetry service or retention job.
Polling adds one small authenticated read per open manager panel every five seconds. Decode
has a 30-second watchdog; normal 40-second viewer polling and reconnect backoff remain.

For rollback restore the previous code/template/static files and restart/reload both portals;
no database downgrade is needed. Complete the browser/WebSocket acceptance checklist in
[testing](testing.md#step-5-viewer-synchronization-status) on the real proxy/deployment.

