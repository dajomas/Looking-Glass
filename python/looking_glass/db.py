"""SQLite3 storage: connection handling and schema migrations.

Every request opens its own short-lived connection (cheap for SQLite) so the
two uvicorn servers and worker threads never share a connection object.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# Each entry is applied once, in order. Never edit an applied migration;
# append a new one instead.
MIGRATIONS: list[str] = [
    # 1 - initial schema
    """
    CREATE TABLE users (
        id                   INTEGER PRIMARY KEY,
        username             TEXT NOT NULL UNIQUE COLLATE NOCASE,
        display_name         TEXT NOT NULL DEFAULT '',
        password_hash        TEXT NOT NULL,
        role                 TEXT NOT NULL CHECK (role IN ('superadmin','admin','viewer')),
        active               INTEGER NOT NULL DEFAULT 1,
        must_change_password INTEGER NOT NULL DEFAULT 0,
        created_by           INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at           TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE sessions (
        token_hash  TEXT PRIMARY KEY,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        entry       TEXT NOT NULL CHECK (entry IN ('admin','viewer')),
        csrf_token  TEXT NOT NULL,
        expires_at  INTEGER NOT NULL,
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX idx_sessions_user ON sessions(user_id);

    CREATE TABLE campaigns (
        id            INTEGER PRIMARY KEY,
        name          TEXT NOT NULL,
        description   TEXT NOT NULL DEFAULT '',
        owner_id      INTEGER REFERENCES users(id) ON DELETE SET NULL,
        active_map_id INTEGER REFERENCES maps(id) ON DELETE SET NULL,
        created_at    TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE campaign_viewers (
        campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        added_by    INTEGER REFERENCES users(id) ON DELETE SET NULL,
        added_at    TEXT NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY (campaign_id, user_id)
    );

    CREATE TABLE maps (
        id             INTEGER PRIMARY KEY,
        campaign_id    INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
        name           TEXT NOT NULL,
        image_file     TEXT NOT NULL,
        width          INTEGER NOT NULL,
        height         INTEGER NOT NULL,
        sort_order     INTEGER NOT NULL DEFAULT 0,
        wall_offset_x  REAL NOT NULL DEFAULT 0,
        wall_offset_y  REAL NOT NULL DEFAULT 0,
        wall_scale_x   REAL NOT NULL DEFAULT 1,
        wall_scale_y   REAL NOT NULL DEFAULT 1,
        doors_block    INTEGER NOT NULL DEFAULT 1,
        walls_source   TEXT NOT NULL DEFAULT '',
        walls_version  INTEGER NOT NULL DEFAULT 0,
        fog_version    INTEGER NOT NULL DEFAULT 0,
        created_at     TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX idx_maps_campaign ON maps(campaign_id);

    -- Raw wall segments in source (Foundry scene) coordinates.
    CREATE TABLE walls (
        id      INTEGER PRIMARY KEY,
        map_id  INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
        x1 REAL NOT NULL, y1 REAL NOT NULL, x2 REAL NOT NULL, y2 REAL NOT NULL,
        kind    TEXT NOT NULL DEFAULT 'wall',   -- wall|door|secret|window|invisible|ethereal
        blocks  INTEGER NOT NULL DEFAULT 1      -- participates in area detection
    );
    CREATE INDEX idx_walls_map ON walls(map_id);

    -- Ordered fog operations; the fog state is a replay of these.
    CREATE TABLE fog_ops (
        id          INTEGER PRIMARY KEY,
        map_id      INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
        op          TEXT NOT NULL CHECK (op IN ('reveal','hide','reveal_all','hide_all')),
        x           REAL,
        y           REAL,
        created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX idx_fog_ops_map ON fog_ops(map_id, id);
    """,
    # 2 - reusable campaign-scoped wall source uploads
    """
    CREATE TABLE wall_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
        filename TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        raw BLOB NOT NULL,
        scene_count INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(campaign_id, sha256)
    );
    """,
    # 3 - map incarnation identity and last-displayed fog checkpoints
    """
    ALTER TABLE maps ADD COLUMN cache_token TEXT NOT NULL DEFAULT '';
    UPDATE maps SET cache_token = lower(hex(randomblob(16)));
    CREATE TRIGGER maps_cache_token AFTER INSERT ON maps
    WHEN NEW.cache_token = ''
    BEGIN
        UPDATE maps SET cache_token = lower(hex(randomblob(16))) WHERE id = NEW.id;
    END;
    CREATE TABLE map_fog_snapshots (
        map_id INTEGER PRIMARY KEY REFERENCES maps(id) ON DELETE CASCADE,
        operations TEXT NOT NULL,
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    -- Existing reveal history is the best available pre-upgrade checkpoint.
    INSERT INTO map_fog_snapshots(map_id, operations)
        SELECT m.id, json_group_array(json_object('op', f.op, 'x', f.x, 'y', f.y))
        FROM maps m JOIN (SELECT * FROM fog_ops ORDER BY id) f ON f.map_id = m.id
        GROUP BY m.id;
    """,
    # 4 - persistent per-map wall-type boundary settings (legacy column remains intact)
    """
    CREATE TABLE map_wall_type_settings (
        map_id INTEGER PRIMARY KEY REFERENCES maps(id) ON DELETE CASCADE,
        disabled_types TEXT NOT NULL DEFAULT '[]'
    );
    """,
    # 5 - shared door arrow appearance
    """
    ALTER TABLE maps ADD COLUMN door_arrow_color TEXT NOT NULL DEFAULT '#46c0ff';
    """,
    # 6 - shared door arrow visibility (enabled by default)
    """
    ALTER TABLE maps ADD COLUMN door_arrows_enabled INTEGER NOT NULL DEFAULT 1
        CHECK (door_arrows_enabled IN (0, 1));
    """,
    # 7 - reserved for the rolled-back viewer-layout migration; no viewer feature enabled
    """SELECT 1;""",
    # 8 - authored door types remain in walls; play-time states live separately
    """
    ALTER TABLE maps ADD COLUMN locked_door_arrow_color TEXT NOT NULL DEFAULT '#ff9f43';
    CREATE TABLE door_runtime_states (
        wall_id INTEGER PRIMARY KEY REFERENCES walls(id) ON DELETE CASCADE,
        kind TEXT NOT NULL CHECK(kind IN ('locked_door','unlocked_door'))
    );
    CREATE TRIGGER reset_runtime_doors AFTER INSERT ON fog_ops
    WHEN NEW.op='hide_all'
    BEGIN
        UPDATE maps SET walls_version=walls_version+1 WHERE id=NEW.map_id AND EXISTS (
            SELECT 1 FROM door_runtime_states r JOIN walls w ON w.id=r.wall_id WHERE w.map_id=NEW.map_id);
        DELETE FROM door_runtime_states WHERE wall_id IN (SELECT id FROM walls WHERE map_id=NEW.map_id);
    END;
    """,
    # 9 - independent viewer arrow visibility; preserve each map's previous shared setting
    """
    ALTER TABLE maps ADD COLUMN viewer_door_arrows_enabled INTEGER NOT NULL DEFAULT 1
        CHECK (viewer_door_arrows_enabled IN (0, 1));
    UPDATE maps SET viewer_door_arrows_enabled = door_arrows_enabled;
    """,
    # 10 - authored passages and independent per-entry runtime state
    """
    ALTER TABLE walls ADD COLUMN passage TEXT NOT NULL DEFAULT '{}';
    CREATE TABLE passage_runtime_states (
        wall_id INTEGER NOT NULL REFERENCES walls(id) ON DELETE CASCADE,
        side INTEGER NOT NULL CHECK(side IN (-1,0,1)),
        kind TEXT NOT NULL CHECK(kind IN ('door','locked_door','unlocked_door')),
        PRIMARY KEY(wall_id,side)
    );
    CREATE TRIGGER reset_runtime_passages AFTER INSERT ON fog_ops
    WHEN NEW.op='hide_all'
    BEGIN
        UPDATE maps SET walls_version=walls_version+1 WHERE id=NEW.map_id AND EXISTS (
            SELECT 1 FROM passage_runtime_states r JOIN walls w ON w.id=r.wall_id WHERE w.map_id=NEW.map_id);
        DELETE FROM passage_runtime_states WHERE wall_id IN (SELECT id FROM walls WHERE map_id=NEW.map_id);
    END;
    """,
    # 11 - viewer exceptions when the main arrow toggle is off
    """
    ALTER TABLE maps ADD COLUMN viewer_portal_arrows_enabled INTEGER NOT NULL DEFAULT 0
        CHECK (viewer_portal_arrows_enabled IN (0, 1));
    ALTER TABLE maps ADD COLUMN viewer_secret_arrows_enabled INTEGER NOT NULL DEFAULT 0
        CHECK (viewer_secret_arrows_enabled IN (0, 1));
    """,
    # 12 - cross-map passage endpoints and replay-safe travel
    """
    ALTER TABLE maps ADD COLUMN viewer_transition_markers INTEGER NOT NULL DEFAULT 1 CHECK(viewer_transition_markers IN (0,1));
    ALTER TABLE maps ADD COLUMN viewer_transition_labels INTEGER NOT NULL DEFAULT 1 CHECK(viewer_transition_labels IN (0,1));
    CREATE TABLE map_transitions (
        id TEXT PRIMARY KEY,
        map_id INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
        name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 120),
        player_label TEXT NOT NULL DEFAULT '' CHECK(length(player_label)<=120),
        kind TEXT NOT NULL CHECK(kind IN ('stairs','ladder','hole','portal','climb','custom')),
        x REAL NOT NULL CHECK(x>=0), y REAL NOT NULL CHECK(y>=0),
        visibility TEXT NOT NULL CHECK(visibility IN ('secret','discovered','admin')),
        availability TEXT NOT NULL CHECK(availability IN ('usable','blocked','approval')),
        runtime_visibility TEXT CHECK(runtime_visibility IN ('secret','discovered','admin')),
        runtime_availability TEXT CHECK(runtime_availability IN ('usable','blocked','approval')),
        destination_id TEXT REFERENCES map_transitions(id) ON DELETE SET NULL,
        link_defined INTEGER NOT NULL DEFAULT 0 CHECK(link_defined IN (0,1)),
        arrival TEXT NOT NULL DEFAULT 'area' CHECK(arrival IN ('area','preserve')),
        notes TEXT NOT NULL DEFAULT '' CHECK(length(notes)<=2000),
        revision INTEGER NOT NULL DEFAULT 1
    );
    CREATE INDEX transitions_map ON map_transitions(map_id);
    CREATE INDEX transitions_destination ON map_transitions(destination_id);
    CREATE TRIGGER transition_campaign_insert BEFORE INSERT ON map_transitions
    WHEN NEW.destination_id IS NOT NULL AND (SELECT campaign_id FROM maps WHERE id=NEW.map_id) !=
        (SELECT m.campaign_id FROM maps m JOIN map_transitions t ON t.map_id=m.id WHERE t.id=NEW.destination_id)
    BEGIN SELECT RAISE(ABORT,'Cross-campaign transition'); END;
    CREATE TRIGGER transition_campaign_update BEFORE UPDATE ON map_transitions
    WHEN NEW.destination_id IS NOT NULL AND (SELECT campaign_id FROM maps WHERE id=NEW.map_id) !=
        (SELECT m.campaign_id FROM maps m JOIN map_transitions t ON t.map_id=m.id WHERE t.id=NEW.destination_id)
    BEGIN SELECT RAISE(ABORT,'Cross-campaign transition'); END;
    CREATE TRIGGER transition_insert AFTER INSERT ON map_transitions
    BEGIN UPDATE maps SET fog_version=fog_version+1 WHERE id=NEW.map_id; END;
    CREATE TRIGGER transition_update AFTER UPDATE ON map_transitions
    BEGIN UPDATE maps SET fog_version=fog_version+1 WHERE id=NEW.map_id; END;
    CREATE TRIGGER transition_delete BEFORE DELETE ON map_transitions
    BEGIN
        UPDATE maps SET fog_version=fog_version+1 WHERE id=OLD.map_id;
        UPDATE map_transitions SET revision=revision+1 WHERE destination_id=OLD.id;
    END;
    CREATE TABLE map_transition_travel (
        campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        request_id TEXT NOT NULL, request_json TEXT NOT NULL, result_json TEXT NOT NULL,
        PRIMARY KEY(campaign_id,user_id,request_id)
    );
    """,
    """
    CREATE TABLE room_notes (
        map_id INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
        area_key TEXT NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 200),
        markdown TEXT NOT NULL DEFAULT '' CHECK(length(markdown)<=100000),
        revision INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(map_id, area_key)
    );
    """,
    """
    CREATE TABLE imported_room_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        map_id INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
        name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 200),
        markdown TEXT NOT NULL CHECK(length(markdown)<=100000),
        digest TEXT NOT NULL,
        UNIQUE(map_id,digest)
    );
    """,
    """
    CREATE TABLE room_notes_new (
        map_id INTEGER NOT NULL REFERENCES maps(id) ON DELETE CASCADE,
        area_key TEXT NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        name TEXT NOT NULL CHECK(length(name)<=200),
        markdown TEXT NOT NULL DEFAULT '' CHECK(length(markdown)<=100000),
        revision INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(map_id, area_key)
    );
    INSERT INTO room_notes_new SELECT map_id,area_key,x,y,name,markdown,revision FROM room_notes;
    DROP TABLE room_notes;
    ALTER TABLE room_notes_new RENAME TO room_notes;
    """,
    # 16 - named campaign-wide play-state checkpoints (authored content stays separate)
    """
    ALTER TABLE campaigns ADD COLUMN session_version INTEGER NOT NULL DEFAULT 0;
    CREATE TABLE campaign_checkpoints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
        name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 120),
        notes TEXT NOT NULL DEFAULT '' CHECK(length(notes)<=2000),
        automatic INTEGER NOT NULL DEFAULT 0 CHECK(automatic IN (0,1)),
        created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        payload TEXT NOT NULL
    );
    CREATE INDEX idx_campaign_checkpoints ON campaign_checkpoints(campaign_id,id DESC);
    """,
]


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection; commit on success, roll back on error."""
        conn = _connect(self.path)
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def migrate(self) -> int:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = _connect(self.path)
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
            row = conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
            current = row["v"] or 0
            for idx, script in enumerate(MIGRATIONS, start=1):
                if idx <= current:
                    continue
                conn.executescript("BEGIN;" + script + f"; INSERT INTO schema_version VALUES ({idx}); COMMIT;")
                current = idx
            return current
        finally:
            conn.close()
