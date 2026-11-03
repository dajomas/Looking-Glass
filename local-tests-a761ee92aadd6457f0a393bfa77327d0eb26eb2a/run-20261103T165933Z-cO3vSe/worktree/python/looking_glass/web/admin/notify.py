"""Helpers that push live updates to viewers."""

from ..context import AppContext


async def campaign_changed(ctx: AppContext, campaign_id: int, reason: str) -> None:
    await ctx.hub.publish(campaign_id, {"type": "refresh", "reason": reason})


async def map_changed(ctx: AppContext, map_id: int, reason: str) -> None:
    """Notify only when the map is the one currently shown to the campaign's viewers.

    Call this *after* the transaction is committed so viewers re-fetch fresh data.
    """
    with ctx.db.connect() as conn:
        row = conn.execute("SELECT id FROM campaigns WHERE active_map_id = ?", (map_id,)).fetchone()
    if row:
        await campaign_changed(ctx, row["id"], reason)
