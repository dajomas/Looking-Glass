"""Object loading + permission checks used by route handlers."""

import sqlite3

from .. import rbac
from ..repositories import campaigns as campaigns_repo
from ..repositories import fog_ops as fog_repo
from ..repositories import maps as maps_repo
from ..repositories import walls as walls_repo
from ..services.fog import MapSpec
from ..services.wall_type_settings import boundary_segments, disabled_for_map
from ..services.wall_model import FogOp, WallSegment
from .context import AppContext
from .deps import Forbidden, NotFound, User


def campaign_for_manage(conn: sqlite3.Connection, user: User, campaign_id: int) -> sqlite3.Row:
    c = campaigns_repo.get(conn, campaign_id)
    if c is None:
        raise NotFound("Campaign not found.")
    if not rbac.can_manage_campaign(user, c):
        raise Forbidden("You do not manage this campaign.")
    return c


def campaign_for_view(conn: sqlite3.Connection, user: User, campaign_id: int) -> sqlite3.Row:
    c = campaigns_repo.get(conn, campaign_id)
    # Same response for missing and forbidden so viewers cannot probe IDs.
    if c is None or not rbac.can_view_campaign(conn, user, c):
        raise NotFound("Campaign not found.")
    return c


def map_for_manage(conn: sqlite3.Connection, user: User, map_id: int) -> tuple[sqlite3.Row, sqlite3.Row]:
    m = maps_repo.get(conn, map_id)
    if m is None:
        raise NotFound("Map not found.")
    return m, campaign_for_manage(conn, user, m["campaign_id"])


def fog_inputs(ctx: AppContext, conn: sqlite3.Connection, map_id: int) -> tuple[MapSpec, list[WallSegment], list[FogOp]]:
    m = maps_repo.get(conn, map_id)
    if m is None:
        raise NotFound("Map not found.")
    return (MapSpec.from_row(m, ctx.settings.maps_dir),
            boundary_segments(walls_repo.list_for_map(conn, map_id), disabled_for_map(conn, m)),
            fog_repo.list_for_map(conn, map_id))
