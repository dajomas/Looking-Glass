"""Service regressions; runnable without the HTTP dependencies."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from looking_glass.db import Database
from looking_glass.services.duplication import duplicate


class DuplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.maps = base / "maps"
        self.maps.mkdir()
        Image.new("RGB", (20, 30)).save(self.maps / "a.png")
        self.db = Database(base / "test.db")
        self.db.migrate()
        with self.db.connect() as c:
            c.execute("INSERT INTO users(id,username,password_hash,role) VALUES(1,'dm','x','admin')")
            c.execute("INSERT INTO campaigns(id,name,owner_id) VALUES(1,'Source',1)")
            for mid in (1,2):
                c.execute("INSERT INTO maps(id,campaign_id,name,image_file,width,height) VALUES(?,1,'Map','a.png',20,30)",(mid,))
                c.execute("INSERT INTO map_transitions(id,map_id,name,kind,x,y,visibility,availability,runtime_visibility) VALUES(?,?,?,'stairs',1,2,'secret','usable','discovered')",(str(mid),mid,'Endpoint'))
            c.execute("UPDATE map_transitions SET destination_id='2',link_defined=1 WHERE id='1'")
            c.execute("UPDATE campaigns SET active_map_id=1 WHERE id=1")
            c.execute("INSERT INTO walls(id,map_id,x1,y1,x2,y2,kind) VALUES(1,1,0,0,10,0,'locked_door')")
            c.execute("INSERT INTO fog_ops(map_id,op) VALUES(1,'reveal_all')")
            c.execute("INSERT INTO door_runtime_states VALUES(1,'unlocked_door')")
            c.execute("INSERT INTO room_notes VALUES(1,'room',1,2,'Room','Secret',4)")
            c.execute("INSERT INTO campaign_viewers VALUES(1,1,NULL,'now')")

    def copy(self, map_id=None):
        with self.db.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            return duplicate(c,1,self.maps,[], 'Copy',1,map_id)

    def test_campaign_links_and_reset(self):
        target, ids = self.copy()
        with self.db.connect() as c:
            campaign = c.execute('SELECT * FROM campaigns WHERE id=?',(target,)).fetchone()
            self.assertIsNone(campaign['active_map_id'])
            self.assertEqual(campaign['owner_id'],1)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM campaign_viewers WHERE campaign_id=?',(target,)).fetchone()[0],0)
            copied = c.execute('SELECT * FROM map_transitions WHERE map_id=?',(ids[1],)).fetchone()
            destination = c.execute('SELECT * FROM map_transitions WHERE id=?',(copied['destination_id'],)).fetchone()
            self.assertEqual(destination['map_id'],ids[2])
            self.assertIsNone(copied['runtime_visibility'])
            self.assertEqual(c.execute('SELECT COUNT(*) FROM fog_ops').fetchone()[0],1)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM door_runtime_states').fetchone()[0],1)
            self.assertEqual(c.execute('SELECT markdown FROM room_notes WHERE map_id=?',(ids[1],)).fetchone()[0],'Secret')
            self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_map_external_link_detached(self):
        target, ids = self.copy(1)
        with self.db.connect() as c:
            row = c.execute('SELECT * FROM map_transitions WHERE map_id=?',(ids[1],)).fetchone()
            self.assertEqual(target,1)
            self.assertIsNone(row['destination_id'])
            self.assertEqual(row['link_defined'],0)
            self.assertEqual(c.execute('SELECT active_map_id FROM campaigns WHERE id=1').fetchone()[0],1)

    def test_map_internal_link_remapped(self):
        with self.db.connect() as c:
            c.execute("UPDATE map_transitions SET map_id=1 WHERE id='2'")
        _, ids = self.copy(1)
        with self.db.connect() as c:
            endpoints = c.execute('SELECT * FROM map_transitions WHERE map_id=?',(ids[1],)).fetchall()
            self.assertIn(endpoints[0]['destination_id'],{r['id'] for r in endpoints})

    def test_independent_image(self):
        _, ids = self.copy(1)
        with self.db.connect() as c:
            path = c.execute('SELECT image_file FROM maps WHERE id=?',(ids[1],)).fetchone()[0]
        self.assertNotEqual(path,'a.png')
        with Image.open(self.maps/path) as image:
            self.assertEqual(image.size,(20,30))

    def test_invalid_name_and_map(self):
        for name, mid in [(' ',None),('Copy',999)]:
            with self.assertRaises(ValueError), self.db.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                duplicate(c,1,self.maps,[],name,1,mid)

    def test_partial_copy_cleanup_contract(self):
        from looking_glass.services.images import delete_map_image
        with self.db.connect() as c:
            c.execute("UPDATE maps SET image_file='missing.png' WHERE id=2")
        created = []
        try:
            with self.assertRaises(OSError), self.db.connect() as c:
                c.execute('BEGIN IMMEDIATE')
                duplicate(c,1,self.maps,created,'Copy',1)
        finally:
            for path in created:
                delete_map_image(self.maps,path)
        self.assertEqual(len(created),1)
        self.assertFalse((self.maps/created[0]).exists())
        with self.db.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM campaigns').fetchone()[0],1)

    def test_missing_image_rolls_back(self):
        (self.maps/'a.png').unlink()
        with self.assertRaises(OSError):
            self.copy()
        with self.db.connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM campaigns').fetchone()[0],1)


if __name__ == '__main__':
    unittest.main()
