"""Bug 27: expose the notes revision independently of fog and wall revisions."""
from test_room_note_archive_web import flow, ok, room, save, NAME


def test_admin_map_payload_tracks_notes_save_and_unassign(flow):
    f = flow
    base = f'/api/maps/{f.mid}'

    def payload():
        result = ok(f.dm.get(base))
        assert type(result['room_notes_version']) is int
        assert result['room_notes_version'] >= 0
        assert result['room_notes_version'] == room(f)['room_notes_version']
        return result

    before = payload()
    stable = ('cache_token', 'walls_version', 'fog_version')
    saved = save(f, NAME, 'Notes-only edit from another editor')
    after_save = payload()
    assert after_save['room_notes_version'] == saved['room_notes_version']
    assert after_save['room_notes_version'] > before['room_notes_version']
    assert {key: after_save[key] for key in stable} == {key: before[key] for key in stable}

    entries = ok(f.dm.get(base + '/room-note-library'))['entries']
    entry = next(item for item in entries if item['name'] == NAME)
    assert entry['assigned'] is True
    ok(f.dm.post(base + f"/room-note-library/{entry['id']}/unassign",
                 json={}, headers=f.headers))
    after_unassign = payload()
    assert after_unassign['room_notes_version'] > after_save['room_notes_version']
    assert {key: after_unassign[key] for key in stable} == {key: before[key] for key in stable}
    assert room(f)['name'] == room(f)['markdown'] == ''
    assert payload()['room_notes_version'] == after_unassign['room_notes_version']
