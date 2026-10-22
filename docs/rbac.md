# Roles and permissions

All checks live in `python/looking_glass/rbac.py`.

| Action | superadmin | admin | viewer |
|---|:-:|:-:|:-:|
| Log in on admin port (5000) | ✔ | ✔ | ✘ |
| Log in on viewer port (5100) | ✔ | ✔ | ✔ |
| Create / edit / disable / delete users, set roles, reset passwords | ✔ | ✘ | ✘ |
| Create campaigns | ✔ | ✔ | ✘ |
| Manage a campaign (maps, walls, fog, settings, delete) | all campaigns | own campaigns | ✘ |
| Transfer campaign ownership | ✔ | ✘ | ✘ |
| Assign / remove viewers on a campaign | all | own | ✘ |
| Create new **viewer** accounts from a campaign page | ✔ | ✔ (if `security.admins_can_create_viewers`) | ✘ |
| View a campaign on the viewer screen | all | own + assigned | assigned only |

Notes

- Any active user can be assigned to a campaign, so an admin can be a player in
  someone else's campaign.
- Sessions belong to one entry point (`lg_admin_session` / `lg_viewer_session`
  cookies). An admin-port session never authenticates on the viewer port, or
  the other way round.
- At least one active superadmin always remains. You cannot demote, disable
  or delete yourself.
- Changing a user's role, disabling them or resetting their password revokes
  their sessions and closes their live viewer sockets. So does removing them
  from a campaign.
- Users created by an admin (and, by default, by a superadmin) must change
  their password at first login.
- Unassigned viewers get **404** (not 403) for campaigns, so IDs can't be probed.
- Every state-changing request needs the session's CSRF token (hidden form
  field or `X-CSRF-Token` header). Cookies are `HttpOnly`, `SameSite=Lax`,
  and `Secure` when `security.secure_cookies: true`.


## Remote viewer camera control

Only a user allowed to manage the selected map's campaign may POST the new admin viewer-zoom command, with the existing admin session and CSRF token. The map must be the campaign's active map and the target must be currently revealed. Viewer accounts still have only their existing read-only local area-bounds navigation; no viewer-port mutation/control endpoint is added. Camera events are broadcast only to that campaign's subscribed sockets and revalidated through each viewer's authorized area lookup.

## Passage actions remain admin-only

Passage following, discovery and lock changes use the existing campaign-management
permission and admin CSRF session. Viewer arrows are display-only; no viewer write
route or hidden portal graph is exposed. Existing authorized read-only viewer
room zoom remains unchanged. See Passages.md.

## Portal overview and route highlighting

The wall-editor overview reads the current authorized authored draft only. New
portal_routes metadata is part of the existing manage-authorized admin map payload
and is never added to viewer state or the viewer compositor. Client-side highlighting
never calls a reveal, lock/discovery or save endpoint. Existing manager/CSRF checks
remain unchanged. Moving a modal or opening an overview does not mutate campaign
state. No new viewer permission or interactive viewer arrow action is introduced.


## Cross-map passages

Endpoint listings, previews and configuration require campaign management permission.
The DM owner and superadmins use the existing management policy; being an assigned
viewer is insufficient. All mutations/travel require CSRF. Source and destination
must belong to the managed campaign. Viewer application routes do not include the
admin transition API. Players receive server-composited discovered markers only,
not endpoint IDs, routes, destination names, private notes or admin-only labels.
A DM override can permit a particular secret/blocked/approval-required trip without
changing authored or session state. It is not a player permission bypass.


### Travel approval presentation

The travel modal uses I approve this trip for approval-required sources and Allow
this trip despite passage restrictions for secret/blocked sources, with the actual
saved-state reasons beneath the control. It hides the checkbox when approval is not
needed and clears it for every new preview. This is per-trip consent, not a saved
permission/state change. Authorization, stale-input validation and large-arrival
confirmation stay enforced. See [travel approval wording](travel-approval.md).
