import io
import sqlite3
from types import SimpleNamespace
import numpy as np
import pytest
from PIL import Image
from looking_glass.db import Database
from looking_glass.services.room_notes import edit_mask_png
from looking_glass.services.room_note_import import parse, store, list_entries, delete_unassigned, ImportError


def test_edit_mask_marks_only_selected_room_without_changing_labels():
    labels=np.zeros((20,40),dtype=np.int32);labels[2:18,2:18]=1;labels[2:18,22:38]=2
    area=SimpleNamespace(labels=labels)
    before=labels.copy()
    pixels=np.asarray(Image.open(io.BytesIO(edit_mask_png(area,1))))
    assert tuple(pixels[8,8])==(255,193,7,75)
    assert pixels[2,2,3]==245
    assert not pixels[:,22:,3].any() and not pixels[0,:,3].any()
    assert np.array_equal(before,area.labels)


def test_delete_rechecks_assignment_and_map_scope(tmp_path):
    db=Database(tmp_path/'db.sqlite');db.migrate()
    with db.connect() as conn:
        conn.execute("INSERT INTO campaigns(id,name) VALUES(1,'Campaign')")
        for mid in (1,2):
            conn.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(?,1,'Map','map.png',400,200)",(mid,))
        store(conn,1,parse(b'# Crypt\nGold\n# Hall\nBones\n')['entries'])
    with db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        entries=list_entries(conn,1);crypt,hall=entries
        conn.execute("INSERT INTO room_notes VALUES(1,'key',100,100,'  CRYPT  ','Edited notes',1)")
        marked=list_entries(conn,1)
        assert marked[0]['assigned'] and not marked[0]['notes_match']
        with pytest.raises(ImportError):delete_unassigned(conn,1,crypt['id'])
        with pytest.raises(ImportError):delete_unassigned(conn,2,hall['id'])
        delete_unassigned(conn,1,hall['id'])
        assert [e['name'] for e in list_entries(conn,1)]==['Crypt']
        assert conn.execute('SELECT COUNT(*) FROM room_notes').fetchone()[0]==1
        assert conn.execute('SELECT COUNT(*) FROM fog_ops').fetchone()[0]==0
        conn.execute("UPDATE room_notes SET markdown='Gold'")
        assert list_entries(conn,1)[0]['notes_match']
        conn.execute("UPDATE room_notes SET name=''")
        delete_unassigned(conn,1,crypt['id'])
        assert list_entries(conn,1)==[]
