import io
import json
import zipfile
import pytest
from test_campaign_backup import env
from looking_glass.services import campaign_backup as service


def test_inspection_read_only(env):
    db,maps,raw=env
    before=sorted(str(p) for p in maps.rglob("*"))
    with db.connect() as conn:
        conn.execute("BEGIN")
        digest=service.target_digest(conn,1)
        report=service.inspect_campaign(conn,1,raw,10**7)
        assert report["name"]=="Adventure" and report["counts"]["maps"]==1
        assert service.target_digest(conn,1)==digest
    assert before==sorted(str(p) for p in maps.rglob("*"))


def test_preview_binding(env,monkeypatch):
    db,maps,raw=env
    with db.connect() as conn:
        token=service.preview_token(conn,1,1,raw)
        service.verify_preview(conn,1,1,raw,token)
        for cid,uid,body,signed in [(2,1,raw,token),(1,2,raw,token),(1,1,raw+b"x",token),(1,1,raw,token+"x"),(1,1,raw,"")]:
            with pytest.raises(ValueError):service.verify_preview(conn,cid,uid,body,signed)
        conn.execute("UPDATE campaigns SET description='changed' WHERE id=1")
        with pytest.raises(ValueError):service.verify_preview(conn,1,1,raw,token)
        token=service.preview_token(conn,1,1,raw)
        now=service.time.time()
        monkeypatch.setattr(service.time,"time",lambda:now+901)
        with pytest.raises(ValueError):service.verify_preview(conn,1,1,raw,token)


def test_recovery_restorable(env,tmp_path):
    db,maps,raw=env
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        name=service.save_recovery(conn,1,maps,tmp_path/"recovery",10**7)
        path=tmp_path/"recovery"/name
        assert service.inspect_campaign(conn,1,path.read_bytes(),10**7)["name"]=="Adventure"
        assert path.stat().st_mode & 0o777==0o600


def test_bad_image_no_changes(env):
    db,maps,raw=env
    out=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(out,"w") as dest:
        for name in source.namelist():
            dest.writestr(name,b"not an image" if name.startswith("images/") else source.read(name))
    with db.connect() as conn:
        digest=service.target_digest(conn,1)
        with pytest.raises(ValueError):service.inspect_campaign(conn,1,out.getvalue(),10**7)
        assert service.target_digest(conn,1)==digest


@pytest.mark.parametrize("kind",["missing","extra","duplicate","schema"])
def test_invalid_structure(env,kind):
    db,maps,raw=env
    out=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(out,"w") as dest:
        for name in source.namelist():
            if kind=="missing" and name.startswith("images/"):continue
            body=source.read(name)
            if kind=="schema" and name=="campaign.json":
                data=json.loads(body);data["schema"]=999;body=json.dumps(data).encode()
            dest.writestr(name,body)
        if kind=="extra":dest.writestr("../unexpected",b"x")
        if kind=="duplicate":
            with pytest.warns(UserWarning):dest.writestr("campaign.json",source.read("campaign.json"))
    with db.connect() as conn:
        with pytest.raises((ValueError,KeyError)):service.inspect_campaign(conn,1,out.getvalue(),10**7)


def test_recovery_failure_keeps_campaign(env,tmp_path):
    db,maps,raw=env
    (maps/"1/a.png").unlink()
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        digest=service.target_digest(conn,1)
        with pytest.raises(OSError):service.save_recovery(conn,1,maps,tmp_path/"recovery",10**7)
        assert service.target_digest(conn,1)==digest
    assert not (tmp_path/"recovery").exists()


def test_recovery_limit_failure(env,tmp_path):
    db,maps,raw=env
    with db.connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        with pytest.raises(ValueError):service.save_recovery(conn,1,maps,tmp_path/"recovery",1)
    assert not (tmp_path/"recovery").exists()


def test_preview_restart(env,monkeypatch):
    db,maps,raw=env
    with db.connect() as conn:
        token=service.preview_token(conn,1,1,raw)
        monkeypatch.setattr(service,"_PREVIEW_KEY",b"another process")
        with pytest.raises(ValueError):service.verify_preview(conn,1,1,raw,token)
