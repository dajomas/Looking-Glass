from test_web import env,login,csrf_of
from conftest import png_bytes


def test_unassign_requires_owner_and_csrf_preserves_fog_and_rejects_stale_save(env):
    ctx,admin,viewer=env
    dm=login(admin,'dm','dmpass123');token=csrf_of(dm);headers={'X-CSRF-Token':token}
    res=dm.post('/campaigns',data={'csrf_token':token,'name':'Unassign'},follow_redirects=False)
    cid=int(res.headers['location'].split('/')[2].split('?')[0])
    res=dm.post(f'/campaigns/{cid}/maps',data={'csrf_token':token,'name':'Map'},files={'image':('map.png',png_bytes(),'image/png')},follow_redirects=False)
    mid=int(res.headers['location'].split('/')[2].split('?')[0]);base=f'/api/maps/{mid}'
    library=base+'/room-note-library'
    dm.post(library+'/import',files={'file':('rooms.md',b'# Crypt\nOriginal','text/markdown')},headers=headers)
    entry=dm.get(library).json()['entries'][0]
    room=dm.post(base+'/room-at',json={'x':100,'y':100},headers=headers).json()
    stamp_fields=('cache_token','walls_version','room_notes_version')
    body={'x':100,'y':100,'area_key':room['area_key'],'revision':room['revision'],'name':'Crypt','markdown':'Custom edits',
          **{key:room[key] for key in stamp_fields}}
    response=dm.post(base+'/room-notes',json=body,headers=headers)
    assert response.status_code==200,response.text
    saved=response.json()
    endpoint=library+f"/{entry['id']}/unassign"
    assert dm.post(endpoint,json={}).status_code==403
    other=login(admin,'dm2','dmpass123')
    assert other.post(endpoint,json={},headers={'X-CSRF-Token':csrf_of(other)}).status_code==403
    before=dm.get(base).json()
    result=dm.post(endpoint,json={},headers=headers)
    assert result.status_code==200,result.text
    result=result.json();assert result['unassigned']==1 and result['area_keys']==[room['area_key']]
    assert not result['entries'][0]['assigned'] and result['entries'][0]['markdown']=='Original'
    cleared=dm.post(base+'/room-at',json={'x':100,'y':100},headers=headers).json()
    assert cleared['name']==cleared['markdown']=='' and cleared['revision']>saved['revision']
    assert cleared['room_notes_version']>saved['room_notes_version']
    stale={**body,**{key:saved[key] for key in stamp_fields},'revision':saved['revision']}
    assert dm.post(base+'/room-notes',json=stale,headers=headers).status_code==400
    assert dm.get(base).json()['fog_version']==before['fog_version']
    assert dm.post(endpoint,json={},headers=headers).json()['unassigned']==0
