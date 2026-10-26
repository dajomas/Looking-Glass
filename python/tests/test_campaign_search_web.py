import pytest
pytest.importorskip('fastapi')
from test_web import env, login, csrf_of


def test_campaign_search_http(env):
    ctx,admin,viewer=env
    dm=login(admin,'dm','dmpass123');other=login(admin,'dm2','dmpass123');root=login(admin,'root','rootpass1');alice=login(viewer,'alice','alicepass')
    cid=int(dm.post('/campaigns',data={'csrf_token':csrf_of(dm),'name':'Adventure'},follow_redirects=False).headers['location'].split('/')[2].split('?')[0])
    with ctx.db.connect() as c:
        mid=c.execute("INSERT INTO maps(campaign_id,name,image_file,width,height) VALUES(?,'Map','missing.png',400,200)",(cid,)).lastrowid
        c.execute("INSERT INTO room_notes VALUES(?,'key',10,20,'Room','secret <script>',1)",(mid,))
        before='\n'.join(c.iterdump())
    for prefix in ('/campaigns','/api/campaigns'):
        url=f'{prefix}/{cid}/search?q=secret'
        assert dm.get(url).status_code==200 and root.get(url).status_code==200
        assert other.get(url).status_code==403
        assert alice.get(url).status_code==404
    response=dm.get(f'/api/campaigns/{cid}/search?q=secret')
    assert response.headers['cache-control']=='no-store'
    target=response.json()['results'][0]['url']
    inspect=dm.get(target)
    assert inspect.status_code==200 and '&lt;script&gt;' in inspect.text
    assert other.get(target).status_code==403
    assert dm.get(f'/campaigns/{cid}/inspect/maps/{mid}?kind=room&key=missing').status_code==404
    assert dm.get(f'/api/campaigns/{cid}/search?kind=invalid').status_code==422
    assert dm.get(f'/api/campaigns/{cid}/search?q='+('a'*201)).status_code==422
    with ctx.db.connect() as c:assert '\n'.join(c.iterdump())==before
