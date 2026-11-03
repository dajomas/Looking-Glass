"""Bug 15 HTTP/SQLite/file contracts, with exact-content reader barriers."""
import html
import io
import json
from pathlib import Path
import re
import sqlite3
import threading
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit
import zipfile

from PIL import Image
import pytest
from conftest import png_bytes, two_room_scene
from test_web import env, login, csrf_of
from looking_glass import db as db_module
from looking_glass.services import image_retirement as retirement
from looking_glass.web.access import fog_inputs
from looking_glass.web.admin import double_reveal as artwork_routes


def stamp(state):
    return {key: state[key] for key in ('cache_token','walls_version','fog_version','image_revision')}


def inventory(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*.png')}


def references(ctx):
    with ctx.db.connect() as conn:
        return {r[0] for r in conn.execute('SELECT image_file FROM maps UNION SELECT image_file FROM double_reveal_maps')}


def pending(ctx):
    with ctx.db.connect() as conn:
        if conn.execute("SELECT 1 FROM sqlite_master WHERE name='image_retirements'").fetchone() is None:
            return set()
        return {r[0] for r in conn.execute('SELECT image_file FROM image_retirements')}


def dump(ctx):
    with ctx.db.connect() as conn:
        return tuple(conn.iterdump())


def redirect_ok(response):
    assert response.status_code == 303, response.text
    query = parse_qs(urlsplit(response.headers['location']).query)
    assert query.get('ok') and not {'err','error'} & query.keys(), response.headers['location']


@pytest.fixture
def case(env):
    ctx, admin, _ = env
    dm = login(admin, 'dm', 'dmpass123')
    token = csrf_of(dm)
    headers = {'X-CSRF-Token': token}
    def campaign(name):
        response = dm.post('/campaigns', data=dict(csrf_token=token, name=name), follow_redirects=False)
        redirect_ok(response)
        return int(response.headers['location'].split('/')[2].split('?')[0])
    cid, other_cid = campaign('Retirement'), campaign('Control')
    def create_map(owner, name, original, alternate=None):
        response = dm.post(f'/campaigns/{owner}/maps', data=dict(csrf_token=token, name=name),
            files={'image': ('original.png', png_bytes(color=original), 'image/png'),
                   'walls': ('walls.json', json.dumps(two_room_scene()).encode(), 'application/json')},
            follow_redirects=False)
        redirect_ok(response)
        mid = int(response.headers['location'].split('/')[2].split('?')[0])
        if alternate is not None:
            base = f'/api/maps/{mid}/double-reveal'
            response = dm.post(base + '/image', data=stamp(dm.get(base).json()), headers=headers,
                files={'file': ('alternate.png', png_bytes(color=alternate), 'image/png')})
            assert response.status_code == 200, response.text
        return mid
    mids = [create_map(cid, 'One', (210,20,20), (20,210,20)),
            create_map(cid, 'Two', (200,50,20), (20,200,50)),
            create_map(cid, 'No alternate', (180,70,20))]
    control = create_map(other_cid, 'Unrelated', (20,20,210), (180,20,180))
    base = f'/api/maps/{mids[0]}/double-reveal'
    state = dm.get(base + '/room?x=100&y=100').json()
    response = dm.post(base + '/room', json=stamp(state) | dict(x=100,y=100,revision=0,enabled=True), headers=headers)
    assert response.status_code == 200, response.text
    state = response.json()
    room = state['rooms'][0]
    response = dm.post(base + '/appearance', json=stamp(state) | dict(
        area_key=room['area_key'],revision=room['revision'],true_active=True), headers=headers)
    assert response.status_code == 200, response.text
    assert dm.post(f'/api/maps/{mids[0]}/reveal', json=dict(x=100,y=100), headers=headers).status_code == 200
    (ctx.settings.maps_dir / 'untracked.png').write_bytes(png_bytes(color=(10,10,10)))
    with ctx.db.connect() as conn:
        original = conn.execute('SELECT image_file FROM maps WHERE id=?', (mids[0],)).fetchone()[0]
        alternate = conn.execute('SELECT image_file FROM double_reveal_maps WHERE map_id=?', (mids[0],)).fetchone()[0]
        control_rows = tuple(tuple(row) for row in conn.execute('SELECT * FROM maps WHERE campaign_id=?', (other_cid,)))
    result = SimpleNamespace(ctx=ctx,dm=dm,token=token,headers=headers,cid=cid,mids=mids,
        other_cid=other_cid,control=control,control_rows=control_rows,original=original,alternate=alternate)
    result.before, result.refs, result.rows = inventory(ctx.settings.maps_dir), references(ctx), dump(ctx)
    try:
        yield result
    finally:
        dm.close()


def operation(case, kind, *, upload_stamp=None, confirm='Retirement', color=(20,20,220)):
    dm, cid, mid = case.dm, case.cid, case.mids[0]
    if kind == 'map':
        return dm.post(f'/maps/{mid}/delete', data=dict(csrf_token=case.token), follow_redirects=False)
    if kind == 'campaign':
        return dm.post(f'/campaigns/{cid}/delete', data=dict(csrf_token=case.token,confirm=confirm), follow_redirects=False)
    if kind == 'alternate':
        base = f'/api/maps/{mid}/double-reveal'
        current = upload_stamp if upload_stamp is not None else stamp(dm.get(base).json())
        return dm.post(base + '/image', data=current, headers=case.headers,
            files={'file': ('new.png',png_bytes(color=color),'image/png')})
    raw = dm.post(f'/campaigns/{cid}/backup', data=dict(csrf_token=case.token))
    assert raw.status_code == 200
    inspected = dm.post(f'/campaigns/{cid}/restore/inspect', data=dict(csrf_token=case.token),
        files={'backup': ('backup.zip',raw.content)}, follow_redirects=False)
    assert inspected.status_code == 200, inspected.text
    preview = html.unescape(re.search(r'name="preview" value="([^"]+)"', inspected.text)[1])
    return dm.post(f'/campaigns/{cid}/restore', data=dict(csrf_token=case.token,confirm=confirm,preview=preview),
        files={'backup': ('backup.zip',raw.content)}, follow_redirects=False)


def assert_control(case):
    with case.ctx.db.connect() as conn:
        assert tuple(tuple(row) for row in conn.execute('SELECT * FROM maps WHERE campaign_id=?',
                                                       (case.other_cid,))) == case.control_rows
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
        paths = [r[0] for r in conn.execute('SELECT image_file FROM maps WHERE id=? UNION '
            'SELECT image_file FROM double_reveal_maps WHERE map_id=?', (case.control,case.control))]
    now = inventory(case.ctx.settings.maps_dir)
    assert len(paths) == 2 and all(now[p] == case.before[p] for p in paths)
    assert now['untracked.png'] == case.before['untracked.png']


def assert_success(case, kind, response):
    if kind in ('map','campaign'):
        redirect_ok(response)
    else:
        assert response.status_code == 200, response.text
        if kind == 'restore':
            assert 'Campaign restored' in response.text
        else:
            assert response.json()['ok']
    after_refs = references(case.ctx)
    retired = case.refs - after_refs
    assert len(retired) == {'map':2,'campaign':5,'restore':5,'alternate':1}[kind]
    assert pending(case.ctx) == retired
    with case.ctx.db.connect() as conn:
        rows = conn.execute('SELECT id FROM maps WHERE campaign_id=?', (case.cid,)).fetchall()
        if kind == 'map':
            assert len(rows) == 2 and case.mids[0] not in [r[0] for r in rows]
        elif kind == 'campaign':
            assert not rows and conn.execute('SELECT 1 FROM campaigns WHERE id=?', (case.cid,)).fetchone() is None
        else:
            assert len(rows) == 3
    before_collection = inventory(case.ctx.settings.maps_dir)
    assert all(before_collection[p] == value for p,value in case.before.items())
    assert all(p in before_collection for p in after_refs)
    if kind == 'restore':
        assert sorted(before_collection[p] for p in after_refs) == sorted(case.before[p] for p in case.refs)
        recovery = list((case.ctx.settings.data_dir / 'recovery').glob('*.zip'))
        assert recovery and all(p.stat().st_size > 0 for p in recovery)
    if kind == 'alternate':
        with case.ctx.db.connect() as conn:
            path = conn.execute('SELECT image_file FROM double_reveal_maps WHERE map_id=?', (case.mids[0],)).fetchone()[0]
        assert path not in case.refs
        with Image.open(io.BytesIO(before_collection[path])) as image:
            assert image.getpixel((100,100)) == (20,20,220)
    assert retirement.collect(case.ctx.db,case.ctx.settings.maps_dir)['removed'] == len(retired)
    after = inventory(case.ctx.settings.maps_dir)
    assert set(after) == set(before_collection) - retired
    assert all(after[p] == before_collection[p] for p in after)
    assert not pending(case.ctx) and retirement.collect(case.ctx.db,case.ctx.settings.maps_dir)['removed'] == 0
    assert_control(case)


@pytest.mark.parametrize('kind', ['map','campaign','restore','alternate'])
def test_mutation_retirement_and_offline_collection(case, kind):
    assert_success(case,kind,operation(case,kind))


@pytest.mark.parametrize('kind', ['map','campaign','restore','alternate'])
def test_precommit_rollback_and_verified_retry(case, monkeypatch, kind):
    real_connect, real_retire = db_module._connect, retirement.retire_paths
    target = []
    class Proxy:
        def __init__(self, conn): self.conn = conn
        def __getattr__(self, name): return getattr(self.conn,name)
        def commit(self):
            if self in target:
                raise sqlite3.OperationalError('injected retirement precommit')
            return self.conn.commit()
    def register(conn, paths):
        real_retire(conn,paths)
        target.append(conn)
    with monkeypatch.context() as patch:
        patch.setattr(db_module,'_connect',lambda path: Proxy(real_connect(path)))
        patch.setattr(retirement,'retire_paths',register)
        if kind == 'restore':
            response = operation(case,kind)
            assert response.status_code == 303 and 'err=' in response.headers['location']
        else:
            with pytest.raises(sqlite3.OperationalError,match='retirement precommit'):
                operation(case,kind)
    assert len(target) == 1
    assert dump(case.ctx) == case.rows and inventory(case.ctx.settings.maps_dir) == case.before
    assert references(case.ctx) == case.refs and not pending(case.ctx)
    assert_success(case,kind,operation(case,kind))


def test_map_without_alternate(case):
    mid = case.mids[2]
    with case.ctx.db.connect() as conn:
        path = conn.execute('SELECT image_file FROM maps WHERE id=?',(mid,)).fetchone()[0]
    redirect_ok(case.dm.post(f'/maps/{mid}/delete',data=dict(csrf_token=case.token),follow_redirects=False))
    assert references(case.ctx) == case.refs - {path} and pending(case.ctx) == {path}
    assert inventory(case.ctx.settings.maps_dir) == case.before
    assert retirement.collect(case.ctx.db,case.ctx.settings.maps_dir)['removed'] == 1
    assert inventory(case.ctx.settings.maps_dir) == {p:b for p,b in case.before.items() if p != path}
    assert_control(case)


def test_repeated_replacement_collects_all_old_versions(case):
    for color in ((20,20,220),(220,20,220),(220,180,20)):
        assert operation(case,'alternate',color=color).status_code == 200
    assert case.refs - references(case.ctx) == {case.alternate}
    queued = pending(case.ctx)
    before = inventory(case.ctx.settings.maps_dir)
    assert len(queued) == 3
    assert len({before[p] for p in queued}) == 3
    assert retirement.collect(case.ctx.db,case.ctx.settings.maps_dir)['removed'] == 3
    after = inventory(case.ctx.settings.maps_dir)
    assert after == {p:b for p,b in before.items() if p not in queued}
    assert not pending(case.ctx)
    assert_control(case)


@pytest.mark.parametrize('kind',['campaign','restore'])
def test_wrong_confirmation_does_not_retire(case,kind):
    response = operation(case,kind,confirm='wrong')
    assert response.status_code == 303 and 'err=' in response.headers['location']
    assert dump(case.ctx) == case.rows and inventory(case.ctx.settings.maps_dir) == case.before
    assert not pending(case.ctx)


def test_stale_alternate_stamp_does_not_retire(case):
    base = f'/api/maps/{case.mids[0]}/double-reveal'
    old_stamp = stamp(case.dm.get(base).json())
    assert operation(case,'alternate',upload_stamp=old_stamp).status_code == 200
    rows,before,queued = dump(case.ctx),inventory(case.ctx.settings.maps_dir),pending(case.ctx)
    assert operation(case,'alternate',upload_stamp=old_stamp).status_code == 400
    assert dump(case.ctx) == rows and inventory(case.ctx.settings.maps_dir) == before
    assert pending(case.ctx) == queued


@pytest.mark.parametrize('reader_kind',['initial','true','current','fog','backup'])
def test_exact_selected_reader_content_survives_mutation(case,monkeypatch,reader_kind):
    selected,release,committed = (threading.Event() for _ in range(3))
    result,errors,seen = [],[],[]
    original_open,original_response,original_write = Image.open,artwork_routes.FileResponse,zipfile.ZipFile.write
    target = case.original if reader_kind == 'initial' else case.alternate
    expected_path = (case.ctx.settings.maps_dir / target).resolve()
    def barrier(path):
        if isinstance(path,(str,Path)) and Path(path).resolve() == expected_path and not selected.is_set():
            seen.append(Path(path).resolve())
            selected.set()
            assert release.wait(15),'specific reader release timed out'
    def opened(path,*args,**kwargs):
        barrier(path)
        return original_open(path,*args,**kwargs)
    def response(path,*args,**kwargs):
        barrier(path)
        return original_response(path,*args,**kwargs)
    def written(archive,path,*args,**kwargs):
        barrier(path)
        return original_write(archive,path,*args,**kwargs)
    if reader_kind in ('initial','true'):
        monkeypatch.setattr(artwork_routes,'FileResponse',response)
    elif reader_kind == 'backup':
        monkeypatch.setattr(zipfile.ZipFile,'write',written)
    else:
        monkeypatch.setattr(Image,'open',opened)
    def read():
        try:
            if reader_kind == 'fog':
                with case.ctx.db.connect() as conn:
                    conn.execute('BEGIN')
                    spec,walls,ops = fog_inputs(case.ctx,conn,case.mids[0])
                result.append(case.ctx.fog.viewer_bytes(spec,walls,ops))
            elif reader_kind == 'backup':
                value = case.dm.post(f'/campaigns/{case.cid}/backup',data=dict(csrf_token=case.token))
                assert value.status_code == 200
                result.append(value.content)
            else:
                value = case.dm.get(f'/api/maps/{case.mids[0]}/double-reveal/artwork?appearance={reader_kind}')
                assert value.status_code == 200
                result.append(value.content)
        except BaseException as exc:
            errors.append(exc)
    real_invalidate = case.ctx.fog.invalidate
    def invalidate(mid):
        committed.set()  # route reaches invalidation only after DB context commit
        return real_invalidate(mid)
    monkeypatch.setattr(case.ctx.fog,'invalidate',invalidate)
    mutation = []
    def mutate():
        try:
            redirect_ok(operation(case,'map'))
            mutation.append(True)
        except BaseException as exc:
            errors.append(exc)
    # Model CLI lifetime for TestClient/direct readers; separate tests cover CLI wiring.
    with retirement.storage_use(case.ctx.settings.maps_dir):
        reader = threading.Thread(target=read,daemon=True)
        writer = threading.Thread(target=mutate,daemon=True)
        reader.start()
        try:
            assert selected.wait(15),(reader_kind,seen,errors)
            writer.start()
            assert committed.wait(15),('mutation did not commit',errors)
            assert pending(case.ctx) == {case.original,case.alternate}
            assert not {case.original,case.alternate} & references(case.ctx)
            with pytest.raises(RuntimeError,match='busy'):
                retirement.collect(case.ctx.db,case.ctx.settings.maps_dir)
        finally:
            release.set()
            reader.join(15)
            if writer.ident is not None:
                writer.join(15)
        assert not reader.is_alive() and not writer.is_alive() and not errors
        assert mutation == [True] and len(result) == 1 and seen == [expected_path]
    if reader_kind == 'backup':
        with zipfile.ZipFile(io.BytesIO(result[0])) as archive:
            data = json.loads(archive.read('campaign.json'))['tables']
            for row in data['maps']:
                assert archive.read(f"images/{row['id']}.png") == case.before[row['image_file']]
            for row in data['double_reveal_maps']:
                assert archive.read(f"alternate/{row['map_id']}.png") == case.before[row['image_file']]
            assert len(data['maps']) == 3 and len(data['double_reveal_maps']) == 2
    elif reader_kind in ('initial','true'):
        assert result[0] == case.before[target]
    else:
        with original_open(io.BytesIO(result[0])) as image:
            assert image.size == (400,200)
            assert image.convert('RGB').getpixel((100,100)) == (20,210,20)
            assert image.convert('RGB').getpixel((300,100)) == ((0,0,0) if reader_kind == 'fog' else (210,20,20))
    assert retirement.collect(case.ctx.db,case.ctx.settings.maps_dir)['removed'] == 2
    assert_control(case)
