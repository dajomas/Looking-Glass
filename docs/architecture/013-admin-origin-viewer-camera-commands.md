## Admin-origin viewer camera commands

`admin_area_taps.js` provides a separate 400-ms/12-screen-pixel delayed-single/double recognizer. The admin tap wrapper first checks existing arrow/managed-door targets and secondary clicks, delegating them unchanged. Only ordinary primary area taps enter the new queue. Singles invoke the original fog handler after version/mode checks; doubles POST a versioned source coordinate to the admin camera endpoint without invoking any fog handler. Pending area work is cancelled by state changes, mutations, camera transforms and navigation gestures.

`admin/viewer_zoom.py` is mounted only on the admin app. The management/CSRF endpoint uses the existing revealed-area service for eligibility, checks current map/version/authorization before and after lookup and publishes a scoped point-only command through the existing EventHub. There is no storage write or schema change. The shared hub distributes the event to this campaign's currently connected viewer sockets; existing session revocation handling remains in force.

The viewer adds only a remote-command receiver around its existing local lookup/toggle path. Recent IDs are deduplicated in a bounded set of 64; a newer command supersedes older pending commands. The displayed version must match after any refresh, and a newer local interaction invalidates pending remote work. Each viewer then performs the unchanged authorized area-bounds lookup, with its existing out-of-order response guards, actual-pose comparison, focus/overview and resize/live-update behavior. This deliberately preserves the exact local lookup and onTap function bodies.

Admin camera transforms, fog/door/rendering services, arrow settings, viewer read-only permissions and schema are unchanged by camera commands. Multiple viewers evaluate the toggle independently against their own actual poses. Commands are ephemeral: no acknowledgment/replay/persistent camera state or external messaging broker is added.


