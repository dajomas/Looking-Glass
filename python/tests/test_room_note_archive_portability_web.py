"""Bug-2 portability HTTP integration contracts; intentionally red before implementation."""
import html
import io
import json
import re
import zipfile

import pytest
from PIL import Image, ImageColor
from test_web import env  # Fixture dependency of imported flow.
from test_room_note_archive_web import (flow, archives, detach, draft, room, ok,
    recover, recovery_body, redirect_id, state, viewer_snapshot, MARKDOWN)

SOURCE_FIELDS = ('origin_uuid', 'source_map_id', 'source_campaign_id', 'source_map_name',
    'source_campaign_name', 'source_map_token', 'observed_walls_version', 'source_width',
    'source_height', 'area_key', 'x', 'y', 'name', 'markdown', 'source_revision', 'reason', 'archived_at')

def history(row):
    return {k: row[k] for k in SOURCE_FIELDS}

def backup(f):
    response = f.dm.post(f'/campaigns/{f.cid}/backup', data={'csrf_token': f.csrf})
    assert response.status_code == 200, response.text
    assert response.headers['content-type'].startswith('application/zip')
    return response.content

def document(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        return json.loads(archive.read('campaign.json'))

def rewrite(raw, mutate):
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as source, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as target:
        for name in source.namelist():
            payload = source.read(name)
            if name == 'campaign.json':
                data = json.loads(payload)
                mutate(data)
                payload = json.dumps(data, ensure_ascii=False, allow_nan=False).encode('utf-8')
            target.writestr(name, payload)
    return output.getvalue()

def inspect(f, raw):
    return f.dm.post(f'/campaigns/{f.cid}/restore/inspect', data={'csrf_token': f.csrf},
        files={'backup': ('backup.zip', raw, 'application/zip')}, follow_redirects=False)

def preview_token(response):
    assert response.status_code == 200, response.text
    assert response.headers.get('cache-control') == 'no-store'
    match = re.search(r'name="preview" value="([^"]+)"', response.text)
    assert match, response.text
    return html.unescape(match[1])

def restore(f, raw, token):
    return f.dm.post(f'/campaigns/{f.cid}/restore',
        data={'csrf_token': f.csrf, 'confirm': 'Archive integration', 'preview': token},
        files={'backup': ('backup.zip', raw, 'application/zip')}, follow_redirects=False)

def map_by_name(f, cid, name):
    with f.ctx.db.connect() as conn:
        found = [dict(r) for r in conn.execute('SELECT * FROM maps WHERE campaign_id=? AND name=?', (cid, name))]
    assert len(found) == 1
    return found[0]

def test_archive_survives_http_backup_inspection_restore_and_remains_recoverable(flow):
    f = flow
    archive = detach(f)
    selected = room(f)
    stale_save, stale_recovery = draft(selected), recovery_body(f, selected=selected)
    before = state(f.ctx)
    raw = backup(f)
    assert state(f.ctx) == before
    data = document(raw)
    assert data['schema'] == 18
    exported = data['tables']['room_note_archives']
    assert len(exported) == 1 and history(exported[0]) == history(archive)
    token = preview_token(inspect(f, raw))
    assert state(f.ctx) == before
    result = restore(f, raw, token)
    assert result.status_code == 200 and 'Campaign restored' in result.text, result.text
    restored = map_by_name(f, f.cid, 'Primary')
    assert restored['cache_token'] != selected['cache_token']
    f.mid = restored['id']
    retained = archives(f)
    assert len(retained) == 1 and retained[0]['map_id'] == f.mid
    assert history(retained[0]) == history(archive)
    before_stale = state(f.ctx)
    assert f.dm.post(f'/api/maps/{f.mid}/room-notes', json=stale_save, headers=f.headers).status_code == 400
    assert recover(f, retained[0], stale_recovery).status_code == 400
    assert state(f.ctx) == before_stale
    with f.ctx.db.connect() as conn:
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
    assert ok(recover(f, retained[0]))['markdown'] == MARKDOWN
    match = re.search(r'href="([^"]+/recovery/[^"]+)"', result.text)
    assert match, result.text
    safety = f.dm.get(html.unescape(match[1]))
    assert safety.status_code == 200
    assert history(document(safety.content)['tables']['room_note_archives'][0]) == history(archive)

@pytest.mark.parametrize('schema', [15, 16, 17])
def test_valid_legacy_backup_is_normalized_without_inventing_archives(flow, schema):
    f = flow
    detach(f)
    def legacy(data):
        data['schema'] = schema
        data['tables'].pop('room_note_archives')
        for row in data['tables']['maps']:
            row.pop('room_notes_version')
        if schema in (15, 16):
            for table in ('double_reveal_maps', 'double_reveal_rooms', 'double_reveal_history'):
                data['tables'].pop(table)
    raw = rewrite(backup(f), legacy)
    before = state(f.ctx)
    token = preview_token(inspect(f, raw))
    assert state(f.ctx) == before
    result = restore(f, raw, token)
    assert result.status_code == 200 and 'Campaign restored' in result.text, result.text
    f.mid = map_by_name(f, f.cid, 'Primary')['id']
    assert archives(f) == [] and room(f)['name'] == room(f)['markdown'] == ''
    with f.ctx.db.connect() as conn:
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []

@pytest.mark.parametrize('malformation', ['legacy_with_archive_table', 'legacy_with_note_generation',
    'current_without_archive_table', 'current_without_note_generation',
    'archive_wrong_owner', 'archive_invalid_reason', 'archive_truncated_columns'])
def test_malformed_archive_backup_is_rejected_without_changes(flow, malformation):
    f = flow
    detach(f)
    def corrupt(data):
        if malformation.startswith('legacy_'):
            data['schema'] = 17
            if malformation == 'legacy_with_archive_table':
                for row in data['tables']['maps']:
                    row.pop('room_notes_version')
            else:
                data['tables'].pop('room_note_archives')
        elif malformation == 'current_without_archive_table':
            data['tables'].pop('room_note_archives')
        elif malformation == 'current_without_note_generation':
            data['tables']['maps'][0].pop('room_notes_version')
        elif malformation == 'archive_wrong_owner':
            data['tables']['room_note_archives'][0]['map_id'] = 99999999
        elif malformation == 'archive_invalid_reason':
            data['tables']['room_note_archives'][0]['reason'] = 'automatic_purge'
        else:
            data['tables']['room_note_archives'][0].pop('markdown')
    raw = rewrite(backup(f), corrupt)
    before, pixels = state(f.ctx), viewer_snapshot(f)
    f.publications.clear()
    response = inspect(f, raw)
    assert response.status_code == 303 and 'err=' in response.headers['location'], response.text
    assert state(f.ctx) == before and viewer_snapshot(f) == pixels
    assert f.publications == []

@pytest.mark.parametrize('kind', ['map', 'campaign'])
def test_clean_http_duplicate_preserves_archives_without_reattaching_or_publishing(flow, kind):
    f = flow
    archive = detach(f)
    selected = room(f)
    stale_recovery, stale_save = recovery_body(f, selected=selected), draft(selected)
    original_mid, original_cid = f.mid, f.cid
    before, pixels = state(f.ctx), viewer_snapshot(f)
    f.publications.clear()
    if kind == 'map':
        new_mid = redirect_id(f.dm.post(f'/maps/{f.mid}/duplicate',
            data={'csrf_token': f.csrf, 'name': 'Copied map'}, follow_redirects=False))
        new_cid = f.cid
    else:
        new_cid = redirect_id(f.dm.post(f'/campaigns/{f.cid}/duplicate',
            data={'csrf_token': f.csrf, 'name': 'Copied campaign'}, follow_redirects=False))
        new_mid = map_by_name(f, new_cid, 'Primary')['id']
    copied = archives(f, new_mid)
    assert len(copied) == 1 and copied[0]['map_id'] == new_mid
    assert history(copied[0]) == history(archive)
    assert room(f, new_mid)['name'] == room(f, new_mid)['markdown'] == ''
    after = state(f.ctx)
    for table in ('room_notes', 'room_note_archives', 'fog_ops', 'map_fog_snapshots'):
        assert [r for r in after[table] if r['map_id'] in (original_mid, f.other_mid)] == [r for r in before[table] if r['map_id'] in (original_mid, f.other_mid)]
    with f.ctx.db.connect() as conn:
        original = conn.execute('SELECT * FROM maps WHERE id=?', (original_mid,)).fetchone()
        target = conn.execute('SELECT * FROM maps WHERE id=?', (new_mid,)).fetchone()
        assert target['cache_token'] != original['cache_token']
        assert target['image_file'] != original['image_file']
        with Image.open(f.ctx.settings.maps_dir / target['image_file']) as image:
            image.load()
            assert image.size == (400, 200)
        assert conn.execute('SELECT COUNT(*) FROM fog_ops WHERE map_id=?', (new_mid,)).fetchone()[0] == 0
        assert conn.execute('SELECT COUNT(*) FROM map_fog_snapshots WHERE map_id=?', (new_mid,)).fetchone()[0] == 0
        assert conn.execute('SELECT active_map_id FROM campaigns WHERE id=?', (original_cid,)).fetchone()[0] == original_mid
        if kind == 'campaign':
            assert conn.execute('SELECT active_map_id FROM campaigns WHERE id=?', (new_cid,)).fetchone()[0] is None
            assert conn.execute('SELECT COUNT(*) FROM campaign_viewers WHERE campaign_id=?', (new_cid,)).fetchone()[0] == 0
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
    preview = f.dm.get(f'/api/maps/{new_mid}/viewer-preview')
    assert preview.status_code == 200
    with Image.open(io.BytesIO(preview.content)) as image:
        rgb = image.convert('RGB')
        fog_color = ImageColor.getrgb(f.ctx.settings.section('fog')['fog_color'])
        assert rgb.getpixel((100, 50)) == fog_color
        assert rgb.getpixel((300, 50)) == fog_color
    assert viewer_snapshot(f) == pixels and f.publications == []
    before_stale = state(f.ctx)
    assert f.dm.post(f'/api/maps/{new_mid}/room-notes', json=stale_save, headers=f.headers).status_code == 400
    assert recover(f, copied[0], stale_recovery, mid=new_mid).status_code == 400
    assert state(f.ctx) == before_stale and archives(f, original_mid) == [archive]
    f.mid = new_mid
    assert ok(recover(f, copied[0]))['markdown'] == MARKDOWN
    assert archives(f, original_mid) == [archive] and viewer_snapshot(f) == pixels
