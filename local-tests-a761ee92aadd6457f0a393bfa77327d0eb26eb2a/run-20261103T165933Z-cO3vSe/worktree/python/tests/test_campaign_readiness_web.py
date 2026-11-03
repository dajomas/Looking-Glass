"""HTTP access, escaping and read-only report/inspection regressions."""
import pytest
pytest.importorskip("fastapi")
from test_web import env, login, csrf_of


def test_readiness_http_and_readonly(env):
    ctx,admin,_=env
    dm=login(admin,'dm','dmpass123')
    token=csrf_of(dm)
    response=dm.post('/campaigns',data={'csrf_token':token,'name':'Dungeon'},follow_redirects=False)
    cid=int(response.headers['location'].split('/')[2].split('?')[0])
    with ctx.db.connect() as c:
        mid=c.execute("INSERT INTO maps(campaign_id,name,image_file,width,height) VALUES(?,'<script>bad</script>','missing.png',400,200)",(cid,)).lastrowid
        c.execute("INSERT INTO room_notes VALUES(?,'stale',10,10,'Keep','secret',1)",(mid,))
    with ctx.db.connect() as c:before='\n'.join(c.iterdump())
    report=dm.get(f'/campaigns/{cid}/readiness')
    assert report.status_code==200
    assert report.headers['cache-control']=='no-store'
    assert 'image_unreadable' in report.text
    assert '&lt;script&gt;bad&lt;/script&gt;' in report.text
    inspect=dm.get(f'/campaigns/{cid}/readiness/maps/{mid}?x=999&y=50')
    assert inspect.status_code==200
    assert 'cx="399"' in inspect.text or 'cx="399.0"' in inspect.text
    assert '<script' not in inspect.text.split('<h1>')[1].split('</h1>')[0]
    with ctx.db.connect() as c:assert '\n'.join(c.iterdump())==before


def test_readiness_rbac(env):
    _,admin,viewer=env
    dm=login(admin,'dm','dmpass123')
    root=login(admin,'root','rootpass1')
    other=login(admin,'dm2','dmpass123')
    alice=login(viewer,'alice','alicepass')
    cid=int(dm.post('/campaigns',data={'csrf_token':csrf_of(dm),'name':'Private'},follow_redirects=False).headers['location'].split('/')[2].split('?')[0])
    url=f'/campaigns/{cid}/readiness'
    assert dm.get(url).status_code==200
    assert root.get(url).status_code==200
    assert other.get(url).status_code==403
    assert alice.get(url).status_code==404
    assert other.get(f'/campaigns/{cid}/readiness/maps/1').status_code==403


def test_inspect_rejects_map_from_other_campaign(env):
    ctx,admin,_=env
    dm=login(admin,'dm','dmpass123')
    with ctx.db.connect() as c:
        uid=c.execute("SELECT id FROM users WHERE username='dm'").fetchone()[0]
        first=c.execute("INSERT INTO campaigns(name,owner_id) VALUES('First',?)",(uid,)).lastrowid
        second=c.execute("INSERT INTO campaigns(name,owner_id) VALUES('Second',?)",(uid,)).lastrowid
        mid=c.execute("INSERT INTO maps(campaign_id,name,image_file,width,height) VALUES(?,'Map','none.png',10,10)",(second,)).lastrowid
    assert dm.get(f'/campaigns/{first}/readiness/maps/{mid}').status_code==404
