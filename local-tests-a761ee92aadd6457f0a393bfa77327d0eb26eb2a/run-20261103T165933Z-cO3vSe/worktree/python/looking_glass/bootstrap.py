"""First-run initialisation: make sure a superadmin exists."""

import logging
import os

from .rbac import Role
from .repositories import users as users_repo
from .security import generate_password
from .web.context import AppContext

log = logging.getLogger("looking_glass")


def ensure_superadmin(ctx: AppContext) -> None:
    with ctx.db.connect() as conn:
        if users_repo.count_superadmins(conn, active_only=False):
            return
        username = ctx.settings.section("security")["initial_superadmin"]
        password = os.environ.get("LG_SUPERADMIN_PASSWORD") or generate_password()
        users_repo.create(conn, username, password, Role.SUPERADMIN, "Superadmin",
                          must_change_password="LG_SUPERADMIN_PASSWORD" not in os.environ)
    banner = "=" * 64
    if "LG_SUPERADMIN_PASSWORD" in os.environ:
        log.warning("%s\nCreated superadmin '%s' from LG_SUPERADMIN_PASSWORD\n%s", banner, username, banner)
    else:
        log.warning("%s\nCreated initial superadmin\n  username: %s\n  password: %s\n"
                    "You will be asked to change it at first login.\n%s", banner, username, password, banner)
