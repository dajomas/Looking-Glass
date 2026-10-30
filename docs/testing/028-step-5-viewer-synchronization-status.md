## Step 5 viewer synchronization status

Run from the repository root:

```sh
PYTHONPATH=python python -m pytest -q python/tests/test_viewer_sync.py python/tests/test_viewer_sync_web.py
node --test python/tests/test_viewer_sync.js python/tests/test_viewer_refresh.js
```

Executed in the patch build: six Python service tests passed; the HTTP module skipped
because FastAPI is unavailable. Twelve JavaScript tests passed (seven new synchronization
checks plus five existing refresh/display-prompt regressions). Changed Python sources
compiled using Python 3.14; changed JavaScript passed node --check. Python service tests
ran on Python 3.12. These results do not imply real HTTP/WebSocket/browser acceptance.

Service coverage: connected/loading/ready/current-version comparison and blank targets;
failed/timeout freshness; disconnect expiry and bounded history; per-tab/campaign isolation;
untrusted/malformed reports; legacy ping contact without false readiness. JavaScript checks:
decode-before-ready, stale completion/failure guards, blank invalidation, failed decode and
recovery, request failure/timeout, reconnect HUD, text-only manager rendering and failed-poll
clearing. The HTTP regression checks manager/superadmin access, other-admin and viewer
isolation, no-store output and absence of database changes.

Before deployment, run HTTP tests with existing development dependencies installed and
perform these browser checks:

1. Open two viewer tabs for the same user plus a second user's tab. Verify distinct rows
   and username labels in campaign and editor Players panels; counts are connections.
2. Reveal, hide, undo, switch maps, restore a session checkpoint and blank the campaign.
   Confirm Loading until the latest image installs, then Up to date; blank is acknowledged.
3. Throttle image transfer, force decode/image/state failures and verify Failed appears;
   restore connectivity and confirm periodic refresh recovers without changing play state.
4. Race several reveals and a blank/switch while an old image decode is pending. Old success
   or failure must not overwrite the latest image/status or acknowledge the wrong version.
5. Drop the network/WebSocket, suspend the tab, and block pongs. Check reconnect/backoff,
   stale detection after roughly 65 seconds plus polling, and old-row expiry after close.
6. Confirm manager poll failure clears stale success, and revoked/other-admin/viewer users
   cannot obtain connection diagnostics. Verify legacy ping-only clients stay Connected.
7. Test proxy upgrade/idle timeout handling and a cache-reloaded viewer. Confirm current
   read-only diagnostics do not expose raw maps, walls or notes on the viewer port.
8. Restart the service: history must clear and viewer reconnects must repopulate it. Review
   CPU/request rates with many open manager pages. Sleep/background timing is best effort.

