"""Resolve per-screen updates while preserving compatibility with the old shared API."""


def resolve_visibility(row, *, enabled=None, admin_enabled=None, viewer_enabled=None):
    for value in (enabled, admin_enabled, viewer_enabled):
        if value is not None and type(value) is not bool:
            raise ValueError("Arrow visibility must be a boolean.")
    admin = bool(row["door_arrows_enabled"])
    viewer = bool(row["viewer_door_arrows_enabled"])
    # The legacy shared field still updates both; explicit per-screen values take precedence.
    if enabled is not None:
        admin = viewer = enabled
    if admin_enabled is not None:
        admin = admin_enabled
    if viewer_enabled is not None:
        viewer = viewer_enabled
    return admin, viewer
