"""Application context shared by the admin and viewer apps."""

from dataclasses import dataclass

from ..config import Settings
from ..db import Database
from ..security import LoginThrottle
from ..services.events import EventHub
from ..services.fog import FogEngine


@dataclass(slots=True)
class AppContext:
    settings: Settings
    db: Database
    fog: FogEngine
    hub: EventHub
    throttle: LoginThrottle

    @classmethod
    def build(cls, settings: Settings) -> "AppContext":
        settings.ensure_dirs()
        db = Database(settings.database_path)
        db.migrate()
        sec = settings.section("security")
        return cls(
            settings=settings,
            db=db,
            fog=FogEngine(settings.section("fog"), settings.section("viewer"), settings.cache_dir),
            hub=EventHub(),
            throttle=LoginThrottle(int(sec["login_max_failures"]), int(sec["login_lockout_seconds"])),
        )
