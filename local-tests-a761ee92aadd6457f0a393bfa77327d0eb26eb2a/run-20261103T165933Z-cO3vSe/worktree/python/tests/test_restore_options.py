import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from looking_glass.services.restore_options import checkpoint_operations, has_restorable_reveals
from looking_glass.services.fog import FogEngine, MapSpec
from looking_glass.services.wall_model import Calibration, FogOp, WallSegment
from looking_glass.config import DEFAULTS


def test_checkpoint_absent_and_saved_order():
    c = sqlite3.connect(":memory:"); c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE map_fog_snapshots(map_id INTEGER PRIMARY KEY, operations TEXT)")
    assert checkpoint_operations(c, 1) == []
    c.execute("INSERT INTO map_fog_snapshots VALUES(1, ?)", (json.dumps([
        {"op":"reveal","x":20,"y":20},{"op":"hide_all"}]),))
    assert [op.op for op in checkpoint_operations(c, 1)] == ["reveal", "hide_all"]


def test_effective_reveals_not_operation_count(tmp_path):
    engine = FogEngine(dict(DEFAULTS["fog"], work_max_dim=100), DEFAULTS["viewer"], tmp_path)
    spec = MapSpec(1,100,100,tmp_path/"map.png",Calibration(),True,1,1)
    assert not has_restorable_reveals(engine,spec,[],[])
    assert not has_restorable_reveals(engine,spec,[],[FogOp("hide_all")])
    assert not has_restorable_reveals(engine,spec,[],[FogOp("reveal_all"),FogOp("hide_all")])
    assert not has_restorable_reveals(engine,spec,[],[FogOp("reveal",20,20),FogOp("hide",20,20)])
    assert has_restorable_reveals(engine,spec,[],[FogOp("reveal",20,20)])
    assert has_restorable_reveals(engine,spec,[],[FogOp("reveal_all")])
