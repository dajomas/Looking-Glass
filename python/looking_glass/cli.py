"""Command line interface.

  python3.14 python/main.py [serve]                 start both portals
  python3.14 python/main.py create-user NAME --role admin
  python3.14 python/main.py reset-password NAME
  python3.14 python/main.py list-users
"""

import argparse
import asyncio
import getpass
import logging
import sys

from .config import load_settings
from .db import Database
from .rbac import Role
from .repositories import sessions as sessions_repo
from .repositories import users as users_repo


def _db(args) -> Database:
    settings = load_settings(args.config)
    settings.ensure_dirs()
    db = Database(settings.database_path)
    db.migrate()
    return db


def _ask_password() -> str:
    while True:
        p1 = getpass.getpass("Password: ")
        if len(p1) < 8:
            print("Use at least 8 characters.")
            continue
        if p1 == getpass.getpass("Repeat:   "):
            return p1
        print("Passwords do not match.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="looking-glass", description="Looking Glass - D&D fog of war")
    parser.add_argument("-c", "--config", help="Path to config.yaml")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="Run the admin and viewer portals (default)")
    cu = sub.add_parser("create-user", help="Create a user")
    cu.add_argument("username")
    cu.add_argument("--role", choices=[r.value for r in Role], default="viewer")
    cu.add_argument("--display-name", default="")
    rp = sub.add_parser("reset-password", help="Reset a user's password and revoke their sessions")
    rp.add_argument("username")
    sub.add_parser("list-users", help="List users")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    match args.cmd:
        case None | "serve":
            settings = load_settings(args.config)
            logging.getLogger().setLevel(settings.section("server")["log_level"].upper())
            try:
                asyncio.run(_serve(settings))
            except KeyboardInterrupt:
                pass
            return 0
        case "create-user":
            with _db(args).connect() as conn:
                if users_repo.get_with_hash(conn, args.username):
                    print(f"User '{args.username}' already exists", file=sys.stderr)
                    return 1
                users_repo.create(conn, args.username, _ask_password(), Role(args.role), args.display_name)
            print(f"Created {args.role} '{args.username}'")
        case "reset-password":
            with _db(args).connect() as conn:
                row = users_repo.get_with_hash(conn, args.username)
                if not row:
                    print(f"No user '{args.username}'", file=sys.stderr)
                    return 1
                users_repo.set_password(conn, row["id"], _ask_password())
                users_repo.update(conn, row["id"], active=True)
                sessions_repo.delete_for_user(conn, row["id"])
            print("Password reset")
        case "list-users":
            with _db(args).connect() as conn:
                for u in users_repo.list_all(conn):
                    print(f"{u['id']:>4}  {u['username']:<24} {u['role']:<11} {'active' if u['active'] else 'disabled'}")
    return 0


async def _serve(settings):
    from .server import serve
    await serve(settings)
