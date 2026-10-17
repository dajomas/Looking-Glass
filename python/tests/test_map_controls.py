import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from looking_glass.db import Database,MIGRATIONS
from looking_glass.services.wall_type_settings import disabled_for_map,save_disabled,boundary_segments
from looking_glass.services.reveal_bounds import revealed_bounds
from looking_glass.services.wall_model import WallSegment,Calibration,FogOp
from looking_glass.services.fog import FogEngine,MapSpec
from looking_glass.config import DEFAULTS


@pytest.fixture
def db(tmp_path):
    db=Database(tmp_path/'test.db');assert db.migrate()==4
    with db.connect() as c:
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'M','m.png',100,100)")
    return db


def test_settings_persist_and_cascade(db):
    with db.connect() as c:
        row=c.execute('SELECT * FROM maps WHERE id=1').fetchone()
        assert disabled_for_map(c,row)==[]
        save_disabled(c,1,['wall']);assert disabled_for_map(c,row)==['wall']
    with Database(db.path).connect() as c:
        row=c.execute('SELECT * FROM maps WHERE id=1').fetchone()
        assert row['walls_version']==1 and disabled_for_map(c,row)==['wall']
        c.execute('DELETE FROM maps WHERE id=1')
        assert c.execute('SELECT COUNT(*) FROM map_wall_type_settings').fetchone()[0]==0


def test_legacy_column_is_retained_and_used_until_saved(db):
    with db.connect() as c:
        c.execute("ALTER TABLE maps ADD COLUMN disabled_wall_types TEXT DEFAULT '[]'")
        c.execute("UPDATE maps SET disabled_wall_types=?", (json.dumps(["door"]),))
        row=c.execute('SELECT * FROM maps WHERE id=1').fetchone()
        assert disabled_for_map(c,row)==['door']
        save_disabled(c,1,['window'])
        assert c.execute('SELECT disabled_wall_types FROM maps').fetchone()[0]=='["window"]'


def test_disabling_changes_boundaries_without_deleting_segments(tmp_path):
    segment=WallSegment(50,0,50,100,'wall',True)
    altered=boundary_segments([segment],['wall'])
    assert len(altered)==1 and segment.blocks and not altered[0].blocks
    e=FogEngine(dict(DEFAULTS['fog'],work_max_dim=100),DEFAULTS['viewer'],tmp_path)
    before=e.build_area_map(100,100,[segment],Calibration(),True)
    after=e.build_area_map(100,100,altered,Calibration(),True)
    assert before.count==2 and after.count==1


def test_invalid_type_is_rejected(db):
    with db.connect() as c:
        with pytest.raises(ValueError):save_disabled(c,1,['untrusted'])


def test_migration3_to4_preserves_tokens_and_history(tmp_path):
    db=Database(tmp_path/'old.db')
    with db.connect() as c:
        c.executescript(''.join(MIGRATIONS[:3]))
        c.executescript('CREATE TABLE schema_version(version INTEGER);INSERT INTO schema_version VALUES(3);')
        c.execute("INSERT INTO campaigns(id,name) VALUES(1,'C')")
        c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(1,1,'M','a',10,10)")
        token=c.execute('SELECT cache_token FROM maps').fetchone()[0]
    assert db.migrate()==4 and db.migrate()==4
    with db.connect() as c:assert c.execute('SELECT cache_token FROM maps').fetchone()[0]==token


def test_reveal_bounds_empty_and_scaled_union():
    m=np.zeros((10,20),dtype=bool)
    assert revealed_bounds(m,200,100) is None
    m[2:4,12:16]=True
    assert revealed_bounds(m,200,100)==dict(x=120.,y=20.,width=40.,height=20.)
    m[0,0]=True
    assert revealed_bounds(m,200,100)==dict(x=0.,y=0.,width=160.,height=40.)
