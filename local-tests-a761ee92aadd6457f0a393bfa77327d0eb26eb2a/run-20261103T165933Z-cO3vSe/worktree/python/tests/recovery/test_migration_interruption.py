"""Kill a child at known points inside the real migration-3 transaction."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from looking_glass.db import Database, MIGRATIONS

ROOT = Path(__file__).resolve().parents[3]
TABLES = ("users", "sessions", "campaigns", "campaign_viewers", "maps", "walls", "fog_ops", "wall_sources")
CHILD = r"""
import json
import os
from pathlib import Path
import sys
from looking_glass.db import Database
from looking_glass import migration_hooks

database, ready, phase = sys.argv[1:]
ready = Path(ready)
original = migration_hooks._initialize_ordered_fog_snapshots

def pause(conn):
    assert conn.in_transaction, 'Hook is not inside a transaction'
    version = conn.execute('SELECT MAX(version) FROM schema_version').fetchone()[0]
    assert version == 2, version
    if phase == 'after-initialization':
        original(conn)
    operations = {
        str(row['map_id']): json.loads(row['operations'])
        for row in conn.execute('SELECT map_id,operations FROM map_fog_snapshots ORDER BY map_id')
    }
    payload = {'pid':os.getpid(), 'phase':phase, 'in_transaction':conn.in_transaction,
               'recorded_version':version, 'snapshots':operations}
    temporary = ready.with_suffix('.pending')
    temporary.write_text(json.dumps(payload), encoding='utf-8')
    temporary.replace(ready)
    print('Paused inside migration 3: ' + phase, flush=True)
    sys.stdin.buffer.read(1)
    raise AssertionError('Child must be killed while paused, never released')

migration_hooks._initialize_ordered_fog_snapshots = pause
Database(database).migrate()
raise AssertionError('Paused migration unexpectedly completed')
"""


def data_snapshot(conn, columns=None):
    if columns is None:
        columns = {table: [row["name"] for row in conn.execute(f'PRAGMA table_info("{table}")')] for table in TABLES}
    data = {}
    for table in TABLES:
        projection = ",".join('"' + name + '"' for name in columns[table])
        data[table] = [list(row) for row in conn.execute(f'SELECT {projection} FROM "{table}" ORDER BY rowid')]
    return columns, data


def schema_snapshot(conn):
    return [list(row) for row in conn.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
    )]


@pytest.fixture
def legacy_database(tmp_path):
    db = Database(tmp_path / "legacy.db")
    with db.connect() as conn:
        conn.executescript(MIGRATIONS[0] + MIGRATIONS[1])
        conn.executescript("CREATE TABLE schema_version(version INTEGER NOT NULL); INSERT INTO schema_version VALUES(2);")
        conn.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'migration-dm','synthetic-unused','admin')")
        conn.execute("INSERT INTO campaigns(id,name,description,owner_id) VALUES(1,'Migration recovery','Preserve this committed text',1)")
        conn.executemany(
            "INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(?,1,?,'synthetic.png',400,200)",
            [(1,"A"),(2,"B"),(3,"Empty")],
        )
        conn.executemany(
            "INSERT INTO fog_ops(id,map_id,op,x,y,created_by) VALUES(?,?,?,?,?,1)",
            [(8,1,"hide_all",None,None),(2,1,"reveal",12.5,20.5),
             (5,2,"hide",3,4),(1,2,"reveal_all",None,None)],
        )
    return db


@pytest.mark.parametrize("phase", ["before-initialization", "after-initialization"])
def test_interrupted_migration_rolls_back_and_retries(legacy_database, tmp_path, phase):
    db = legacy_database
    evidence = ROOT / "test-results/migration-interruption" / phase
    evidence.mkdir(parents=True, exist_ok=True)
    ready = tmp_path / "ready.json"
    env = {key:value for key,value in os.environ.items() if not key.startswith("LG_")}
    env.update(PYTHONPATH=str(ROOT / "python"), PYTHONUNBUFFERED="1")
    with db.connect() as conn:
        columns, before_data = data_snapshot(conn)
        before_schema = schema_snapshot(conn)
        expected = {
            str(mid): [dict(row) for row in conn.execute("SELECT op,x,y FROM fog_ops WHERE map_id=? ORDER BY id", (mid,))]
            for mid in (1,2)
        }
    with (evidence / "interrupted-child.log").open("wb") as log:
        process = subprocess.Popen(
            [sys.executable,"-c",CHILD,str(db.path),str(ready),phase],
            cwd=tmp_path, env=env, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 15
            while not ready.exists():
                assert process.poll() is None, f"Child exited before handshake; see {evidence}"
                if time.monotonic() >= deadline:
                    pytest.fail(f"Child did not reach migration pause within 15 seconds; see {evidence}")
                time.sleep(0.025)
            handshake = json.loads(ready.read_text(encoding="utf-8"))
            shutil.copy2(ready, evidence / "handshake.json")
            assert process.poll() is None
            assert handshake["pid"] == process.pid and handshake["phase"] == phase
            assert handshake["in_transaction"] and handshake["recorded_version"] == 2
            if phase == "after-initialization":
                assert handshake["snapshots"] == expected
            # A different connection must still see the complete committed v2 state.
            with db.connect() as conn:
                assert conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] == 2
                assert schema_snapshot(conn) == before_schema
                assert data_snapshot(conn, columns)[1] == before_data
            process.kill()
            assert process.wait(timeout=5) != 0
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            process.stdin.close()
    with db.connect() as conn:
        assert conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] == 2
        assert schema_snapshot(conn) == before_schema
        assert data_snapshot(conn, columns)[1] == before_data
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    retry = "from looking_glass.db import Database; import sys; print(Database(sys.argv[1]).migrate())"
    with (evidence / "retry-child.log").open("wb") as log:
        result = subprocess.run([sys.executable,"-c",retry,str(db.path)], cwd=tmp_path, env=env,
                                stdout=log, stderr=subprocess.STDOUT, timeout=20, check=False)
    assert result.returncode == 0, f"Fresh-process migration retry failed; see {evidence}"
    with db.connect() as conn:
        assert conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] == len(MIGRATIONS)
        assert data_snapshot(conn, columns)[1] == before_data
        actual = {str(row["map_id"]):json.loads(row["operations"]) for row in conn.execute(
            "SELECT map_id,operations FROM map_fog_snapshots ORDER BY map_id")}
        assert actual == expected
        assert all(row[0] for row in conn.execute("SELECT cache_token FROM maps"))
        saved_tokens = [tuple(row) for row in conn.execute("SELECT id,cache_token FROM maps ORDER BY id")]
        saved_snapshots = [tuple(row) for row in conn.execute("SELECT * FROM map_fog_snapshots ORDER BY map_id")]
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert db.migrate() == len(MIGRATIONS)
    with db.connect() as conn:
        assert [tuple(row) for row in conn.execute("SELECT id,cache_token FROM maps ORDER BY id")] == saved_tokens
        assert [tuple(row) for row in conn.execute("SELECT * FROM map_fog_snapshots ORDER BY map_id")] == saved_snapshots
    (evidence / "result.json").write_text(json.dumps({
        "phase":phase, "child_exit":process.returncode, "retry_exit":result.returncode,
        "final_version":len(MIGRATIONS), "legacy_rows_preserved":True,
        "ordered_snapshots_verified":True, "idempotent_retry":True,
    }, indent=2), encoding="utf-8")
