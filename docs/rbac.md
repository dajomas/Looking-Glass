# Roles and permissions

All checks live in `python/looking_glass/rbac.py`.

| Action | superadmin | admin | viewer |
|---|:-:|:-:|:-:|
| Log in on admin port (5000) | ✔ | ✔ | ✘ |
| Log in on viewer port (6000) | ✔ | ✔ | ✔ |
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
