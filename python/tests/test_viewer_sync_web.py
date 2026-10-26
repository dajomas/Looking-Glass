import pytest
pytest.importorskip("fastapi")
from test_web import env,login,csrf_of


def test_status_management_boundary_and_no_state_changes(env):
    ctx,admin,viewer=env
    dm=login(admin,"dm","dmpass123");other=login(admin,"dm2","dmpass123");root=login(admin,"root","rootpass1");alice=login(viewer,"alice","alicepass")
    response=dm.post("/campaigns",data={"csrf_token":csrf_of(dm),"name":"Adventure"},follow_redirects=False)
    cid=int(response.headers["location"].split("/")[2].split("?")[0]);url=f"/api/campaigns/{cid}/viewer-status"
    with ctx.db.connect() as conn:before="\n".join(conn.iterdump())
    assert other.get(url).status_code==403 and alice.get(url).status_code==404
    assert root.get(url).status_code==200
    result=dm.get(url)
    assert result.status_code==200 and result.headers["cache-control"]=="no-store"
    assert result.json()["blank"] and result.json()["viewers"]==[]
    with ctx.db.connect() as conn:assert "\n".join(conn.iterdump())==before
