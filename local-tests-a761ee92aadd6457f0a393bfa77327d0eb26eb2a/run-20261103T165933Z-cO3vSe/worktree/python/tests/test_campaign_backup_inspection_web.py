import html
import io
import re
import zipfile
import pytest
pytest.importorskip("fastapi")
from test_web import env,login,csrf_of


def test_inspect_restore_recovery_http(env):
    ctx,admin,viewer=env
    dm=login(admin,"dm","dmpass123");other=login(admin,"dm2","dmpass123");alice=login(viewer,"alice","alicepass")
    csrf=csrf_of(dm)
    response=dm.post("/campaigns",data={"csrf_token":csrf,"name":"Adventure"},follow_redirects=False)
    cid=int(response.headers["location"].split("/")[2].split("?")[0]);base=f"/campaigns/{cid}"
    raw=dm.post(base+"/backup",data={"csrf_token":csrf}).content
    def inspect(client,token):
        return client.post(base+"/restore/inspect",data={"csrf_token":token},files={"backup":("backup.zip",raw)},follow_redirects=False)
    assert inspect(other,csrf_of(other)).status_code==403
    assert inspect(alice,csrf_of(alice)).status_code==404
    assert inspect(dm,"wrong").status_code==403
    preview=inspect(dm,csrf)
    assert preview.status_code==200 and preview.headers["cache-control"]=="no-store"
    token=html.unescape(re.search(r'name="preview" value="([^"]+)"',preview.text)[1])
    def restore(token):
        return dm.post(base+"/restore",data={"csrf_token":csrf,"confirm":"Adventure","preview":token},files={"backup":("backup.zip",raw)},follow_redirects=False)
    assert restore("").status_code==303
    success=restore(token)
    assert success.status_code==200 and "Campaign restored" in success.text
    url=re.search(r'href="([^"]+/recovery/[^"]+)"',success.text)[1]
    saved=dm.get(url)
    assert saved.status_code==200
    with zipfile.ZipFile(io.BytesIO(raw)) as before,zipfile.ZipFile(io.BytesIO(saved.content)) as after:
        assert {n:before.read(n) for n in before.namelist()}=={n:after.read(n) for n in after.namelist()}
    assert other.get(url).status_code==403 and alice.get(url).status_code==404
    assert restore(token).status_code==303
    assert "Retained recovery backups" in dm.get(base).text
