"""Bug-2 HTTP integration contract. Requires migration 18 and recovery routes.

GET room-note-archives returns {ok,archives}; POST recovery accepts target
validation fields plus overwrite and returns the normal room payload.
These are intentionally red before implementation; no skips or exclusions.
"""
import copy
import io
import json
from contextlib import ExitStack
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from conftest import png_bytes, two_room_scene
from test_web import env, login, csrf_of

NAME = 'Crypt'
MARKDOWN = '# Custom secret\r\n\n**Gold** and café 🐉.\n\n<script>secret()</script>\n'
POINT = {'x': 100, 'y': 50}
HALL = {'x': 300, 'y': 50}
VALIDATION = ('area_key', 'revision', 'cache_token', 'walls_version', 'room_notes_version')
TABLES = ('campaigns', 'maps', 'walls', 'fog_ops', 'map_fog_snapshots', 'room_notes',
          'room_note_archives', 'imported_room_notes', 'map_wall_type_settings',
          'door_runtime_states', 'passage_runtime_states', 'map_transitions',
          'map_transition_travel', 'double_reveal_maps', 'double_reveal_rooms',
          'double_reveal_history', 'campaign_checkpoints', 'wall_sources', 'campaign_viewers')

def ok(response):
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['ok'] is True
    return result

def redirect_id(response):
    assert response.status_code == 303, response.text
    assert 'err=' not in response.headers['location'], response.headers['location']
    return int(response.headers['location'].split('/')[2].split('?')[0])

def state(ctx):
    with ctx.db.connect() as conn:
        return {t: [dict(r) for r in conn.execute(f'SELECT * FROM {t} ORDER BY rowid')] for t in TABLES}

def room(f, mid=None, point=None):
    mid = f.mid if mid is None else mid
    return ok(f.dm.post(f'/api/maps/{mid}/room-at', json=point or POINT, headers=f.headers))

def draft(selected, name=NAME, markdown=MARKDOWN, point=None):
    assert set(VALIDATION) <= selected.keys(), selected
    return {**(point or POINT), **{k: selected[k] for k in VALIDATION}, 'name': name, 'markdown': markdown}

def save(f, name=NAME, markdown=MARKDOWN, mid=None, point=None):
    mid = f.mid if mid is None else mid
    return ok(f.dm.post(f'/api/maps/{mid}/room-notes',
        json=draft(room(f, mid, point), name, markdown, point), headers=f.headers))

def set_geometry(f, split):
    scene = two_room_scene()
    if split:
        scene['walls'].append({'c': [110, 200, 300, 200], 'move': 20, 'sight': 20})
    return ok(f.dm.post(f'/api/maps/{f.mid}/walls', headers=f.headers,
        files={'file': ('walls.json', json.dumps(scene).encode(), 'application/json')}))

def archives(f, mid=None):
    mid = f.mid if mid is None else mid
    response = f.dm.get(f'/api/maps/{mid}/room-note-archives')
    result = ok(response)
    assert response.headers.get('cache-control') == 'no-store'
    return result['archives']

def detach(f):
    set_geometry(f, True)
    result = archives(f)
    assert len(result) == 1
    assert (result[0]['name'], result[0]['markdown']) == (NAME, MARKDOWN)
    return result[0]

def recovery_body(f, overwrite=False, selected=None):
    selected = room(f) if selected is None else selected
    return {**POINT, **{k: selected[k] for k in VALIDATION}, 'overwrite': overwrite}

def recover(f, archive, body=None, client=None, mid=None, headers=None):
    client = f.dm if client is None else client
    mid = f.mid if mid is None else mid
    return client.post(f"/api/maps/{mid}/room-note-archives/{archive['id']}/recover",
        json=recovery_body(f) if body is None else body, headers=f.headers if headers is None else headers)

def viewer_snapshot(f):
    result = ok(f.alice.get(f'/api/c/{f.cid}/state'))
    response = f.alice.get(result['map']['image_url'])
    assert response.status_code == 200, response.text
    with Image.open(io.BytesIO(response.content)) as image:
        image.load()
        decoded = (image.size, image.convert('RGBA').tobytes())
    return result, response.content, decoded

def note_only_guard(f):
    snapshot = state(f.ctx)
    snapshot.pop('room_notes')
    snapshot.pop('room_note_archives')
    for row in snapshot['maps']:
        row.pop('room_notes_version')
    return snapshot, viewer_snapshot(f)

@pytest.fixture
def flow(env, monkeypatch):
    ctx, admin, viewer = env
    with ctx.db.connect() as conn:
        assert conn.execute("SELECT 1 FROM sqlite_master WHERE name='room_note_archives'").fetchone(), 'Install bug-2 implementation; do not skip this contract'
    with ExitStack() as stack:
        def client(app, user, password):
            result = login(app, user, password)
            stack.callback(result.close)
            return result
        dm = client(admin, 'dm', 'dmpass123')
        other = client(admin, 'dm2', 'dmpass123')
        alice = client(viewer, 'alice', 'alicepass')
        anon = TestClient(admin)
        stack.callback(anon.close)
        csrf = csrf_of(dm)
        headers = {'X-CSRF-Token': csrf}
        def campaign(name):
            return redirect_id(dm.post('/campaigns', data={'csrf_token': csrf, 'name': name}, follow_redirects=False))
        cid, foreign_cid = campaign('Archive integration'), campaign('Separate campaign')
        def upload(campaign_id, name):
            return redirect_id(dm.post(f'/campaigns/{campaign_id}/maps',
                data={'csrf_token': csrf, 'name': name},
                files={'image': ('map.png', png_bytes(), 'image/png'),
                       'walls': ('walls.json', json.dumps(two_room_scene()).encode(), 'application/json')},
                follow_redirects=False))
        mid, other_mid, foreign_mid = upload(cid, 'Primary'), upload(cid, 'Independent'), upload(foreign_cid, 'Foreign')
        f = SimpleNamespace(ctx=ctx, admin=admin, viewer=viewer, dm=dm, other=other, alice=alice,
            anon=anon, csrf=csrf, headers=headers, cid=cid, foreign_cid=foreign_cid,
            mid=mid, other_mid=other_mid, foreign_mid=foreign_mid)
        for current in (mid, other_mid):
            ok(dm.post(f'/api/maps/{current}/room-note-library/import', headers=headers,
                files={'file': ('rooms.md', b'# Crypt\nOriginal library\n# Hall\nHall library', 'text/markdown')}))
            save(f, mid=current)
            save(f, 'Hall', 'Unaffected hall', mid=current, point=HALL)
        f.saved = room(f)
        f.old_draft = draft(f.saved)
        with ctx.db.connect() as conn:
            uid = conn.execute("SELECT id FROM users WHERE username='alice'").fetchone()[0]
        assigned = dm.post(f'/campaigns/{cid}/viewers/add', data={'csrf_token': csrf, 'user_id': uid}, follow_redirects=False)
        assert assigned.status_code == 303
        ok(dm.post(f'/api/maps/{mid}/reveal', json=POINT, headers=headers))
        ok(dm.post(f'/api/campaigns/{cid}/active', json={'map_id': mid, 'fog_action': 'restore'}, headers=headers))
        f.publications = []
        original_publish = ctx.hub.publish
        async def publish(campaign_id, event):
            f.publications.append((campaign_id, copy.deepcopy(event)))
            await original_publish(campaign_id, event)
        monkeypatch.setattr(ctx.hub, 'publish', publish)
        yield f

def test_geometry_import_archives_custom_edits_and_preserves_other_rooms(flow):
    f = flow
    before = state(f.ctx)
    detached = detach(f)
    after = state(f.ctx)
    assert [r for r in before['room_notes'] if r['map_id'] == f.other_mid] == [r for r in after['room_notes'] if r['map_id'] == f.other_mid]
    assert room(f, point=HALL)['markdown'] == 'Unaffected hall'
    entries = ok(f.dm.get(f'/api/maps/{f.mid}/room-note-library'))['entries']
    crypt = next(e for e in entries if e['name'] == NAME)
    assert not crypt['assigned'] and crypt['markdown'] == 'Original library'
    assert detached['source_revision'] == f.saved['revision']
    assert room(f)['name'] == room(f)['markdown'] == ''
    f.publications.clear()
    guard = note_only_guard(f)
    for _ in range(2):
        ok(f.dm.get(f'/api/maps/{f.mid}'))
        ok(f.dm.get(f'/api/maps/{f.mid}/room-notes'))
        assert archives(f) == [detached]
    assert note_only_guard(f) == guard
    assert f.publications == []

def test_read_triggered_reconciliation_is_lossless_and_does_not_publish(flow):
    from looking_glass.repositories import walls, maps
    from looking_glass.services.foundry_import import parse_wall_file
    f = flow
    scene = two_room_scene()
    scene['walls'].append({'c': [110, 200, 300, 200], 'move': 20, 'sight': 20})
    segments = parse_wall_file(json.dumps(scene).encode(), 'split.json')[0].segments
    with f.ctx.db.connect() as conn:
        conn.execute('BEGIN IMMEDIATE')
        walls.replace(conn, f.mid, segments)
        maps.set_walls_source(conn, f.mid, 'staged split')
    f.ctx.fog.invalidate(f.mid)
    before = note_only_guard(f)
    f.publications.clear()
    ok(f.dm.get(f'/api/maps/{f.mid}'))
    assert len(archives(f)) == 1 and archives(f)[0]['markdown'] == MARKDOWN
    assert room(f)['markdown'] == ''
    assert note_only_guard(f) == before
    assert f.publications == []

def test_explicit_recovery_preserves_archive_fog_viewer_pixels_and_notifications(flow):
    f = flow
    archive = detach(f)
    retained, before, body = archives(f), note_only_guard(f), recovery_body(f)
    f.publications.clear()
    recovered = ok(recover(f, archive, body))
    assert (recovered['name'], recovered['markdown']) == (NAME, MARKDOWN)
    assert '<script>' not in recovered['html']
    assert recovered['revision'] > body['revision']
    assert recovered['room_notes_version'] > body['room_notes_version']
    assert archives(f) == retained and note_only_guard(f) == before
    assert f.publications == []
    before_retry = state(f.ctx)
    assert recover(f, archive, body).status_code == 400
    assert state(f.ctx) == before_retry

@pytest.mark.parametrize('actor', ['anonymous', 'other_admin', 'viewer', 'missing_csrf', 'wrong_csrf'])
def test_recovery_access_denial_is_nonmutating(flow, actor):
    f = flow
    archive, body = detach(f), recovery_body(f)
    if actor == 'anonymous':
        client, headers, expected = f.anon, {}, 401
    elif actor == 'other_admin':
        client, headers, expected = f.other, {'X-CSRF-Token': csrf_of(f.other)}, 403
    elif actor == 'viewer':
        client, headers, expected = f.alice, {'X-CSRF-Token': csrf_of(f.alice)}, 404
    else:
        client, headers, expected = f.dm, ({} if actor == 'missing_csrf' else {'X-CSRF-Token': 'wrong'}), 403
    before, pixels = state(f.ctx), viewer_snapshot(f)
    f.publications.clear()
    assert recover(f, archive, body, client=client, headers=headers).status_code == expected
    assert state(f.ctx) == before and viewer_snapshot(f) == pixels
    assert f.publications == []

@pytest.mark.parametrize('actor,expected', [('anonymous', 401), ('other_admin', 403), ('viewer', 404)])
def test_archive_listing_is_management_only(flow, actor, expected):
    f = flow
    detach(f)
    client = {'anonymous': f.anon, 'other_admin': f.other, 'viewer': f.alice}[actor]
    before = state(f.ctx)
    response = client.get(f'/api/maps/{f.mid}/room-note-archives')
    assert response.status_code == expected
    assert MARKDOWN not in response.text and state(f.ctx) == before

@pytest.mark.parametrize('target', ['same_campaign', 'different_campaign'])
def test_recovery_cannot_use_another_maps_archive(flow, target):
    f = flow
    archive = detach(f)
    mid = f.other_mid if target == 'same_campaign' else f.foreign_mid
    body, before = recovery_body(f, selected=room(f, mid)), state(f.ctx)
    assert recover(f, archive, body, mid=mid).status_code == 404
    assert state(f.ctx) == before

@pytest.mark.parametrize('field', ['cache_token', 'walls_version', 'room_notes_version'])
def test_ordinary_save_requires_all_context_fields(flow, field):
    f = flow
    body = draft(room(f))
    del body[field]
    before = state(f.ctx)
    assert f.dm.post(f'/api/maps/{f.mid}/room-notes', json=body, headers=f.headers).status_code == 422
    assert state(f.ctx) == before

@pytest.mark.parametrize('field', ['cache_token', 'walls_version', 'room_notes_version', 'area_key', 'revision'])
def test_recovery_rejects_each_stale_validation_field(flow, field):
    f = flow
    archive = detach(f)
    body = recovery_body(f)
    body[field] = '0' * 64 if field in ('cache_token', 'area_key') else body[field] + 1
    before = state(f.ctx)
    assert recover(f, archive, body).status_code == 400
    assert state(f.ctx) == before

def test_old_editor_cannot_save_after_geometry_returns(flow):
    f = flow
    archive = detach(f)
    set_geometry(f, False)
    current = room(f)
    assert current['area_key'] == f.saved['area_key']
    assert current['name'] == current['markdown'] == ''
    before = state(f.ctx)
    assert f.dm.post(f'/api/maps/{f.mid}/room-notes', json=f.old_draft, headers=f.headers).status_code == 400
    assert state(f.ctx) == before and archives(f) == [archive]

def test_unassign_invalidates_editor_without_changing_geometry(flow):
    f = flow
    old = draft(room(f))
    entries = ok(f.dm.get(f'/api/maps/{f.mid}/room-note-library'))['entries']
    entry = next(e for e in entries if e['name'] == NAME)
    ok(f.dm.post(f"/api/maps/{f.mid}/room-note-library/{entry['id']}/unassign", json={}, headers=f.headers))
    current = room(f)
    assert current['area_key'] == old['area_key'] and current['name'] == current['markdown'] == ''
    before = state(f.ctx)
    assert f.dm.post(f'/api/maps/{f.mid}/room-notes', json=old, headers=f.headers).status_code == 400
    assert state(f.ctx) == before

def test_recovery_replacement_requires_confirmation_and_retains_previous_target(flow):
    f = flow
    archive = detach(f)
    saved = save(f, 'New target', 'Do not lose this target\r\n🐉')
    before = state(f.ctx)
    assert recover(f, archive, recovery_body(f)).status_code == 400
    assert state(f.ctx) == before
    body, guard = recovery_body(f, overwrite=True), note_only_guard(f)
    f.publications.clear()
    ok(recover(f, archive, body))
    retained = archives(f)
    assert next(r for r in retained if r['id'] == archive['id']) == archive
    replacement = next(r for r in retained if r['reason'] == 'recovery_replacement')
    assert (replacement['name'], replacement['markdown'], replacement['source_revision']) == ('New target', 'Do not lose this target\r\n🐉', saved['revision'])
    assert note_only_guard(f) == guard and f.publications == []

@pytest.mark.parametrize('stage', ['archive_target', 'write_target'])
def test_recovery_database_failure_rolls_back_and_allows_same_request_retry(flow, stage):
    f = flow
    archive = detach(f)
    save(f, 'Replacement target', 'Must survive failed recovery')
    body = recovery_body(f, overwrite=True)
    with f.ctx.db.connect() as conn:
        if stage == 'archive_target':
            conn.executescript("CREATE TRIGGER fail_recovery BEFORE INSERT ON room_note_archives WHEN NEW.reason='recovery_replacement' BEGIN SELECT RAISE(ABORT,'injected recovery failure'); END;")
        else:
            conn.executescript(f"CREATE TRIGGER fail_recovery AFTER UPDATE ON room_notes WHEN NEW.map_id={int(f.mid)} BEGIN SELECT RAISE(ABORT,'injected recovery failure'); END;")
    before, guard = state(f.ctx), note_only_guard(f)
    f.publications.clear()
    with TestClient(f.admin, cookies=f.dm.cookies, raise_server_exceptions=False) as failing:
        response = recover(f, archive, body, client=failing)
    assert response.status_code == 500, response.text
    assert state(f.ctx) == before and note_only_guard(f) == guard
    assert f.publications == []
    with f.ctx.db.connect() as conn:
        conn.execute('DROP TRIGGER fail_recovery')
    ok(recover(f, archive, body))
    assert room(f)['markdown'] == MARKDOWN and len(archives(f)) == 2

def test_second_editor_cannot_overwrite_a_newer_save(flow):
    f = flow
    first, second = room(f), room(f)
    assert {k: first[k] for k in VALIDATION} == {k: second[k] for k in VALIDATION}
    ok(f.dm.post(f'/api/maps/{f.mid}/room-notes', json=draft(first, 'First writer', 'Committed first'), headers=f.headers))
    before = state(f.ctx)
    assert f.dm.post(f'/api/maps/{f.mid}/room-notes', json=draft(second, 'Second writer', 'Must not overwrite'), headers=f.headers).status_code == 400
    assert state(f.ctx) == before and room(f)['markdown'] == 'Committed first'

def test_recovery_rejects_a_target_changed_after_confirmation_context_was_captured(flow):
    f = flow
    archive = detach(f)
    stale = recovery_body(f, overwrite=True)
    save(f, 'Concurrent writer', 'New target must survive')
    before = state(f.ctx)
    assert recover(f, archive, stale).status_code == 400
    assert state(f.ctx) == before
    assert room(f)['markdown'] == 'New target must survive' and archives(f) == [archive]
