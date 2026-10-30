## Viewer synchronization status

Open a campaign or expand Players in its fog editor. The synchronization panel updates
about every five seconds and lists username, an ephemeral connection identifier, status
and seconds since contact. Multiple tabs for one account appear separately. Reconnecting
creates a new row; the old disconnected row can remain for 90 seconds, so this is not a
unique player count. The existing live-viewer counter remains a socket count, not readiness.

| Status | Meaning |
|---|---|
| Connected | Socket accepted; no valid display report yet (including old ping-only clients). |
| Loading | Current image is loading, or the reported displayed version differs from the campaign's active version. |
| Up to date | Viewer reports successful decode and installation of the currently expected fogged image, or the waiting screen when blank. |
| Display failed | The viewer reported a state/image/decode failure; its last image can remain on screen. |
| Disconnected / reconnecting | Socket closed, or no valid status/keepalive contact for more than 65 seconds. The server cannot prove a reconnect attempt is running. |

A browser tab reports status/keepalive about every 25 seconds; decode has a 30-second
timeout. The existing 40-second state refresh remains a recovery fallback. WebSocket
reconnects use the existing backoff; a missing pong eventually forces a new socket. A
healthy ping-only legacy viewer remains Connected, never Up to date; reload it to enable
reports. Refresh the updated viewer and manager pages after deployment.

Up to date is browser-reported, not an independent screenshot, hardware/display-power,
visibility or operator-presence check. A sleeping/background tab can be marked reconnecting
because timers are throttled. Failure is cleared by a successful subsequent refresh. If
manager polling fails, reports are cleared and the panel says status unavailable rather
than displaying stale success. The viewer HUD distinguishes its own load state and transport.

These diagnostics are read-only and do not reveal maps, reset fog, change assignments or
send zoom commands. Only the campaign manager or superadmin sees the connection list.
No IP address, user-agent, raw image, wall data or arbitrary client error text is shown.
History is in memory and disappears on process restart.

