import re
import pytest
pytest.importorskip('fastapi')
from test_web import env,login,csrf_of
from conftest import png_bytes


def setup_campaign(ctx,dm):
    cid=int(dm.post('/campaigns',data={'csrf_token':csrf_of(dm),'name':'Adventure'},follow_redirects=False).headers['location'].split('/')[2].split('?')[0])
    path=ctx.settings.maps_dir/'session.png';path.write_bytes(png_bytes(40,30))
    with ctx.db.connect() as c:
        mid=c.execute("INSERT INTO maps(campaign_id,name,image_file,width,height) VALUES(?,'Map','session.png',40,30)",(cid,)).lastrowid
    return cid,mid


def test_checkpoint_http_workflow_and_csrf(env):
    ctx,admin,_=env;dm=login(admin,'dm','dmpass123')
    cid,mid=setup_campaign(ctx,dm);token=csrf_of(dm)
    base=f'/campaigns/{cid}/checkpoints'
    assert dm.post(base,data={'name':'Before'}).status_code==403
    response=dm.post(base,data={'csrf_token':token,'name':'Before'},follow_redirects=False)
    assert response.status_code==303
    with ctx.db.connect() as c:
        checkpoint=c.execute('SELECT id FROM campaign_checkpoints WHERE campaign_id=?',(cid,)).fetchone()[0]
        assert c.execute('SELECT active_map_id FROM campaigns WHERE id=?',(cid,)).fetchone()[0] is None
        c.execute('UPDATE campaigns SET active_map_id=? WHERE id=?',(mid,cid))
        c.execute("INSERT INTO fog_ops(map_id,op,x,y) VALUES(?,'reveal',2,2)",(mid,))
    page=dm.get(f'{base}/{checkpoint}')
    assert page.status_code==200 and page.headers['cache-control']=='no-store'
    state_token=re.search(r'name="token" value="([a-f0-9]+)"',page.text).group(1)
    response=dm.post(f'{base}/{checkpoint}/restore',data={'csrf_token':token,'token':state_token,'confirm':'Adventure'},follow_redirects=False)
    assert response.status_code==303 and 'ok=' in response.headers['location']
    with ctx.db.connect() as c:
        assert c.execute('SELECT active_map_id FROM campaigns WHERE id=?',(cid,)).fetchone()[0] is None
        assert c.execute('SELECT COUNT(*) FROM fog_ops WHERE map_id=?',(mid,)).fetchone()[0]==0
        assert c.execute('SELECT COUNT(*) FROM campaign_checkpoints WHERE campaign_id=?',(cid,)).fetchone()[0]==2
    response=dm.post(f'{base}/{checkpoint}/restore',data={'csrf_token':token,'token':state_token,'confirm':'Adventure'},follow_redirects=False)
    assert 'err=' in response.headers['location']
    assert dm.post(f'{base}/{checkpoint}/delete',data={'confirm':'Before'}).status_code==403
    dm.post(f'{base}/{checkpoint}/delete',data={'csrf_token':token,'confirm':'Before'})
    assert dm.get(f'{base}/{checkpoint}').status_code==404


def test_checkpoint_rbac_and_readonly_preview(env):
    ctx,admin,viewer=env
    dm=login(admin,'dm','dmpass123');other=login(admin,'dm2','dmpass123');root=login(admin,'root','rootpass1');alice=login(viewer,'alice','alicepass')
    cid,_=setup_campaign(ctx,dm);base=f'/campaigns/{cid}/checkpoints'
    dm.post(base,data={'csrf_token':csrf_of(dm),'name':'Before'})
    with ctx.db.connect() as c:
        checkpoint=c.execute('SELECT id FROM campaign_checkpoints WHERE campaign_id=?',(cid,)).fetchone()[0]
        before='\n'.join(c.iterdump())
    assert dm.get(base).status_code==200 and root.get(base).status_code==200
    assert other.get(base).status_code==403 and alice.get(base).status_code==404
    assert dm.get(f'{base}/{checkpoint}').status_code==200
    assert other.post(f'{base}/{checkpoint}/restore',data={'csrf_token':csrf_of(other),'confirm':'Adventure','token':'x'}).status_code==403
    with ctx.db.connect() as c:assert '\n'.join(c.iterdump())==before
