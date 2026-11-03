"""Recovery workspace authorization and read-only server rendering."""
from test_web import env
from test_room_note_archive_web import flow, state


def test_recovery_page_is_management_only_no_store_and_nonmutating(flow):
    f=flow
    path=f"/maps/{f.mid}/room-note-recovery"
    before=state(f.ctx)
    response=f.dm.get(path)
    assert response.status_code==200,response.text
    assert response.headers["cache-control"]=="no-store"
    assert 'id="room-recovery"' in response.text
    assert 'id="recovery-apply" type="button" disabled' in response.text
    assert 'room_note_recovery_page.js' in response.text
    assert f.other.get(path).status_code==403
    assert f.alice.get(path).status_code==404
    anonymous=f.anon.get(path,follow_redirects=False)
    assert anonymous.status_code==303 and anonymous.headers["location"].startswith("/login")
    assert state(f.ctx)==before


def test_editor_exposes_new_tab_link_without_replacing_its_draft(flow):
    response=flow.dm.get(f"/maps/{flow.mid}")
    assert response.status_code==200,response.text
    assert f'href="/maps/{flow.mid}/room-note-recovery" target="_blank" rel="noopener"' in response.text
