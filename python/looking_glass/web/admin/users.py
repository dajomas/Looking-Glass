"""Superadmin-only user management."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request

from ...rbac import Role
from ...repositories import sessions as sessions_repo
from ...repositories import users as users_repo
from ..deps import BadRequest, CtxDep, SuperadminDep, verify_csrf
from ..templating import render
from .campaigns import _back

router = APIRouter(prefix="/users")
Csrf = Depends(verify_csrf)


def _guard_last_superadmin(conn: sqlite3.Connection, target: sqlite3.Row, *, new_role: Role | None = None,
                           new_active: bool | None = None, deleting: bool = False) -> None:
    if target["role"] != Role.SUPERADMIN or not target["active"]:
        return
    loses = deleting or (new_role is not None and new_role != Role.SUPERADMIN) or new_active is False
    if loses and users_repo.count_superadmins(conn) <= 1:
        raise BadRequest("At least one active superadmin must remain.")


@router.get("")
def users_page(request: Request, ctx: CtxDep, user: SuperadminDep):
    with ctx.db.connect() as conn:
        users = users_repo.list_all(conn)
        assignments = {
            u["id"]: [r["name"] for r in conn.execute(
                "SELECT c.name FROM campaign_viewers v JOIN campaigns c ON c.id = v.campaign_id"
                " WHERE v.user_id = ? ORDER BY c.name", (u["id"],))]
            for u in users
        }
    return render(request, "admin/users.html", users=users, assignments=assignments, roles=list(Role),
                  min_len=ctx.settings.section("security")["min_password_length"])


@router.post("", dependencies=[Csrf])
def create_user(ctx: CtxDep, user: SuperadminDep,
                username: Annotated[str, Form(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_.@-]+$")],
                password: Annotated[str, Form()],
                role: Annotated[Role, Form()],
                display_name: Annotated[str, Form(max_length=120)] = "",
                must_change: Annotated[bool, Form()] = False):
    min_len = int(ctx.settings.section("security")["min_password_length"])
    if len(password) < min_len:
        return _back("/users", err=f"Password must be at least {min_len} characters")
    with ctx.db.connect() as conn:
        try:
            users_repo.create(conn, username, password, role, display_name, created_by=user["id"],
                              must_change_password=must_change)
        except sqlite3.IntegrityError:
            return _back("/users", err=f"Username '{username}' already exists")
    return _back("/users", ok=f"User '{username}' created")


@router.post("/{user_id}/update", dependencies=[Csrf])
async def update_user(ctx: CtxDep, user: SuperadminDep, user_id: int,
                      role: Annotated[Role, Form()],
                      display_name: Annotated[str, Form(max_length=120)] = "",
                      active: Annotated[bool, Form()] = False):
    with ctx.db.connect() as conn:
        target = users_repo.get(conn, user_id)
        if target is None:
            raise BadRequest("Unknown user")
        if target["id"] == user["id"] and (role != Role.SUPERADMIN or not active):
            raise BadRequest("You cannot demote or deactivate yourself.")
        _guard_last_superadmin(conn, target, new_role=role, new_active=active)
        revoke_sessions = role != target["role"] or not active
        users_repo.update(conn, user_id, display_name=display_name, role=role, active=active)
        if revoke_sessions:
            sessions_repo.delete_for_user(conn, user_id)
    if revoke_sessions:
        await ctx.hub.kick_user(user_id)
    return _back("/users", ok=f"User '{target['username']}' updated")


@router.post("/{user_id}/password", dependencies=[Csrf])
async def reset_password(ctx: CtxDep, user: SuperadminDep, user_id: int,
                         password: Annotated[str, Form()],
                         must_change: Annotated[bool, Form()] = False):
    min_len = int(ctx.settings.section("security")["min_password_length"])
    if len(password) < min_len:
        return _back("/users", err=f"Password must be at least {min_len} characters")
    with ctx.db.connect() as conn:
        target = users_repo.get(conn, user_id)
        if target is None:
            raise BadRequest("Unknown user")
        users_repo.set_password(conn, user_id, password, must_change=must_change)
        if user_id != user["id"]:
            sessions_repo.delete_for_user(conn, user_id)
    if user_id != user["id"]:
        await ctx.hub.kick_user(user_id)
    return _back("/users", ok=f"Password for '{target['username']}' reset")


@router.post("/{user_id}/delete", dependencies=[Csrf])
async def delete_user(ctx: CtxDep, user: SuperadminDep, user_id: int):
    with ctx.db.connect() as conn:
        target = users_repo.get(conn, user_id)
        if target is None:
            raise BadRequest("Unknown user")
        if target["id"] == user["id"]:
            raise BadRequest("You cannot delete yourself.")
        _guard_last_superadmin(conn, target, deleting=True)
        owned = conn.execute("SELECT COUNT(*) FROM campaigns WHERE owner_id = ?", (user_id,)).fetchone()[0]
        if owned:
            raise BadRequest(f"'{target['username']}' still owns {owned} campaign(s); transfer them first.")
        users_repo.delete(conn, user_id)
    await ctx.hub.kick_user(user_id)
    return _back("/users", ok=f"User '{target['username']}' deleted")
