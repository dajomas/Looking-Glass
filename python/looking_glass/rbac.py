"""Role based access control.

Roles are hierarchical:  superadmin > admin > viewer

* superadmin - manages all users; may also manage every campaign
* admin      - manages own campaigns and assigns viewers to them
* viewer     - can only view campaigns they are assigned to (viewer port)

All permission decisions live in this module so the web layer never
hard-codes role checks.
"""

import sqlite3
from enum import StrEnum
from typing import Any, Mapping


class Role(StrEnum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    VIEWER = "viewer"


RANK = {Role.VIEWER: 0, Role.ADMIN: 1, Role.SUPERADMIN: 2}

type UserLike = Mapping[str, Any]
type CampaignLike = Mapping[str, Any]


def role_of(user: UserLike) -> Role:
    return Role(user["role"])


def at_least(user: UserLike, role: Role) -> bool:
    return RANK[role_of(user)] >= RANK[role]


# --- portal access ---------------------------------------------------------
def can_use_admin_portal(user: UserLike) -> bool:
    return bool(user["active"]) and at_least(user, Role.ADMIN)


def can_use_viewer_portal(user: UserLike) -> bool:
    return bool(user["active"])


# --- user management -------------------------------------------------------
def can_manage_users(user: UserLike) -> bool:
    return role_of(user) is Role.SUPERADMIN


def can_create_viewers(user: UserLike, admins_allowed: bool) -> bool:
    return can_manage_users(user) or (admins_allowed and role_of(user) is Role.ADMIN)


def assignable_roles(user: UserLike) -> list[Role]:
    if can_manage_users(user):
        return [Role.SUPERADMIN, Role.ADMIN, Role.VIEWER]
    return [Role.VIEWER]


# --- campaigns ---------------------------------------------------------------
def can_create_campaign(user: UserLike) -> bool:
    return at_least(user, Role.ADMIN)


def can_manage_campaign(user: UserLike, campaign: CampaignLike) -> bool:
    if role_of(user) is Role.SUPERADMIN:
        return True
    return role_of(user) is Role.ADMIN and campaign["owner_id"] == user["id"]


def can_view_campaign(conn: sqlite3.Connection, user: UserLike, campaign: CampaignLike) -> bool:
    if can_manage_campaign(user, campaign):
        return True
    row = conn.execute(
        "SELECT 1 FROM campaign_viewers WHERE campaign_id = ? AND user_id = ?",
        (campaign["id"], user["id"]),
    ).fetchone()
    return row is not None
