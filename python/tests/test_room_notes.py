"""Room identity, migration, persistence and Markdown safety regression tests."""
import sqlite3
from types import SimpleNamespace
import numpy as np
import pytest
from looking_glass.db import Database
from looking_glass.services.room_notes import area_key, render, payload


def area(labels):
    return SimpleNamespace(labels=np.array(labels), scale=1.0, shape=np.array(labels).shape, region_signatures={})


def test_geometry_identity_not_component_number():
    a=area([[1,0,2],[1,0,2]])
    b=area([[7,0,9],[7,0,9]])
    assert area_key(a,1,3,2)==area_key(b,7,3,2)
    assert area_key(a,1,3,2)!=area_key(a,2,3,2)
    assert area_key(a,1,3,2)!=area_key(area([[1,1,2],[1,0,2]]),1,3,2)


def test_markdown_safety_and_formatting():
    html=render("# Crypt\n\n**Treasure** and *danger*.\n\n- gold\n- bones\n\n<script>alert(1)</script>\n\n[x](javascript:alert(1))\n\n![remote](https://example.org/track)")
    assert "<h1>Crypt</h1>" in html and "<strong>Treasure</strong>" in html
    assert "<ul>" in html
    assert "<script>" not in html and 'href="javascript:' not in html and "<img" not in html


def test_migration_idempotent_and_foreign_key_cascade(tmp_path):
    db=Database(tmp_path/"rooms.db")
    version=db.migrate()
    assert db.migrate()==version
    with db.connect() as conn:
        assert {r[1] for r in conn.execute("PRAGMA table_info(room_notes)")} >= {"map_id","area_key","name","markdown","revision"}
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO room_notes(map_id,area_key,x,y,name) VALUES(999,'k',1,1,'Crypt')")
        assert payload(conn,999,'k',False)["revision"]==0
