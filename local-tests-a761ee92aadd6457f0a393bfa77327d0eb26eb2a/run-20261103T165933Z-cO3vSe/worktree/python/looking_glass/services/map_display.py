"""Transactional activation policy and last-displayed reveal checkpoints."""

import json

from ..repositories import campaigns as campaigns_repo
from ..repositories import fog_ops as fog_repo
from ..repositories import maps as maps_repo


def checkpoint(conn, map_id: int) -> None:
    ops = [{"op": op.op, "x": op.x, "y": op.y} for op in fog_repo.list_for_map(conn, map_id)]
    conn.execute(
        "INSERT INTO map_fog_snapshots(map_id, operations) VALUES (?, ?) "
        "ON CONFLICT(map_id) DO UPDATE SET operations = excluded.operations, updated_at = datetime('now')",
        (map_id, json.dumps(ops)),
    )


def checkpoint_if_active(conn, map_id: int) -> None:
    if conn.execute("SELECT 1 FROM campaigns WHERE active_map_id = ?", (map_id,)).fetchone():
        checkpoint(conn, map_id)


def activate(conn, campaign_id: int, map_id: int | None, fog_action: str | None, user_id: int) -> None:
    """Caller authorises campaign/map and owns the transaction. Reset is not undoable."""
    if map_id is not None and fog_action not in ("restore", "reset"):
        raise ValueError("Choose restore or reset before showing a map.")
    campaign = campaigns_repo.get(conn, campaign_id)
    if map_id is not None:
        target = maps_repo.get(conn, map_id)
        if target is None or target["campaign_id"] != campaign_id:
            raise ValueError("Map does not belong to this campaign.")
    if campaign["active_map_id"] is not None:
        checkpoint(conn, campaign["active_map_id"])
    if map_id is not None:
        if fog_action == "reset":
            from .door_runtime import reset as reset_doors
            reset_doors(conn, map_id)
            fog_repo.clear(conn, map_id)
        else:
            saved = conn.execute("SELECT operations FROM map_fog_snapshots WHERE map_id = ?", (map_id,)).fetchone()
            if saved is not None:
                fog_repo.clear(conn, map_id)
                for op in json.loads(saved["operations"]):
                    fog_repo.add(conn, map_id, op["op"], op["x"], op["y"], user_id)
        maps_repo.bump_fog(conn, map_id)
        checkpoint(conn, map_id)
    campaigns_repo.set_active_map(conn, campaign_id, map_id)
