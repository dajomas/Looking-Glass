"""Manual calibration validation and route registration."""

from pydantic import BaseModel, Field

from ...repositories import maps as maps_repo
from ...repositories import walls as walls_repo
from ...services.foundry_import import WallImportError, validated_calibration
from ...services.wall_model import Calibration, WallSet
from ..access import map_for_manage
from ..deps import BadRequest, CsrfUserDep, CtxDep
from . import notify


class CalibrationIn(BaseModel):
    offset_x: float = Field(allow_inf_nan=False)
    offset_y: float = Field(allow_inf_nan=False)
    scale_x: float = Field(gt=0, le=100, allow_inf_nan=False)
    scale_y: float = Field(gt=0, le=100, allow_inf_nan=False)
    doors_block: bool = True


def register_calibration(router, map_payload):
    @router.post("/maps/{map_id}/calibration")
    async def calibration(ctx: CtxDep, user: CsrfUserDep, map_id: int, body: CalibrationIn):
        with ctx.db.connect() as conn:
            # Keep source-wall validation and the update in one write transaction.
            conn.execute("BEGIN IMMEDIATE")
            m, _ = map_for_manage(conn, user, map_id)
            cal = Calibration(body.offset_x, body.offset_y, body.scale_x, body.scale_y)
            try:
                validated_calibration(
                    WallSet("Manual calibration", walls_repo.list_for_map(conn, map_id)),
                    m["width"], m["height"], calibration=cal)
            except WallImportError as exc:
                raise BadRequest(str(exc)) from exc
            maps_repo.set_calibration(conn, map_id, cal.offset_x, cal.offset_y, cal.scale_x, cal.scale_y,
                                      body.doors_block)
            ctx.fog.invalidate(map_id)
            payload = map_payload(ctx, conn, map_id)
        await notify.map_changed(ctx, map_id, "walls")
        return payload

    return calibration
