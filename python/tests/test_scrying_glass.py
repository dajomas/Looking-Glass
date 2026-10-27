import io
import json
from urllib.error import HTTPError, URLError
from http.cookiejar import Cookie
from unittest.mock import patch
import pytest
from looking_glass.services import scrying_glass as sg
from looking_glass.config import load_settings

def catalog():
    return {"campaigns": [{"id": "3", "name": "Crypt", "setups": ["goblin-guardroom", "default"]}]}

def config():
    return {"enabled": True, "base_url": "https://sg.example:8443", "username": "dm", "password": "secret"}

@pytest.mark.parametrize("name,expected", [(" Goblin Guardroom ", "goblin-guardroom"), ("The King's Chamber", "the-king-s-chamber"), ("é", ""), ("A"*90, "a"*80)])
def test_slug(name, expected):
    assert sg.setup_slug(name) == expected

def test_matching_and_accessibility():
    assert sg.match_catalog(catalog(), "Crypt", "Goblin Guardroom")["matched"]
    assert sg.match_catalog(catalog(), " Crypt ", "Goblin Guardroom")["matched"]
    assert sg.match_catalog(catalog(), "crypt", "Goblin Guardroom")["status"] == "campaign_not_accessible"
    assert sg.match_catalog(catalog(), "Crypt", "Other")["status"] == "setup_not_found"
    assert sg.match_catalog(catalog(), "Crypt", "é")["status"] == "invalid_room_name"
    data=catalog();data["campaigns"]*=2
    assert sg.match_catalog(data, "Crypt", "Goblin Guardroom")["status"] == "ambiguous_campaign"

@pytest.mark.parametrize("payload", [{}, {"campaigns": [None]}, {"campaigns": [{"id": "3", "name": "Crypt", "setups": "bad"}]}])
def test_invalid_catalog(payload):
    with pytest.raises(sg.LookupError):sg.match_catalog(payload, "Crypt", "Room")

def test_disabled_and_unnamed_make_no_request():
    with patch.object(sg, "fetch_catalog", side_effect=AssertionError("network")):
        assert sg.lookup({}, "Crypt", "Room")["status"] == "disabled"
        assert sg.lookup(config(), "Crypt", " ")["status"] == "unnamed_room"

@pytest.mark.parametrize("url", ["file:///etc/passwd", "http://user:pass@host", "https://host/path", "https://host?secret=1", "https://host:bad", "https://host/#x"])
def test_reject_invalid_origins(url):
    cfg=config();cfg["base_url"]=url
    with pytest.raises(sg.LookupError):sg.options(cfg)

def test_environment_password_and_startup_validation(monkeypatch):
    monkeypatch.setenv("LG_SCRYING_GLASS_PASSWORD", "envsecret")
    cfg=config();result=sg.options(cfg)
    assert result.password == "envsecret" and "envsecret" not in repr(result)
    assert load_settings(overrides={"scrying_glass":cfg}).section("scrying_glass")["enabled"]
    cfg["timeout_seconds"]=float("nan")
    with pytest.raises(sg.LookupError):sg.options(cfg)

def fake_factory(mode, calls):
    def factory(*handlers):
        jar=next(h.cookiejar for h in handlers if hasattr(h,"cookiejar"))
        class Response(io.BytesIO):
            pass
        class Opener:
            def open(self, req, timeout):
                calls.append((req.full_url, req.get_method(), req.data))
                if len(calls)==1:
                    if mode=="bad_login":return Response(b"login failed")
                    if mode=="network":raise URLError("sensitive upstream details")
                    jar.set_cookie(Cookie(0,"session","token",None,False,"sg.example",False,False,"/",True,True,None,True,None,None,{},False))
                    location="https://evil.example" if mode=="redirect" else "/"
                    raise HTTPError(req.full_url,303,"redirect",{"Location":location},io.BytesIO())
                if mode=="denied":raise HTTPError(req.full_url,403,"secret",{},io.BytesIO())
                if mode=="invalid":return Response(b"not-json")
                if mode=="large":return Response(b"x"*(sg.MAX_RESPONSE+1))
                return Response(json.dumps(catalog()).encode())
        return Opener()
    return factory

def test_login_cookie_and_catalog_only():
    calls=[]
    assert sg.fetch_catalog(sg.options(config()),fake_factory("ok",calls))==catalog()
    assert [x[:2] for x in calls]==[("https://sg.example:8443/login","POST"),("https://sg.example:8443/api/campaigns","GET")]
    assert b"password=secret" in calls[0][2]

@pytest.mark.parametrize("mode", ["bad_login","network","redirect","denied","invalid","large"])
def test_safe_remote_errors(mode):
    calls=[]
    with pytest.raises(sg.LookupError) as exc:sg.fetch_catalog(sg.options(config()),fake_factory(mode,calls))
    assert "secret" not in str(exc.value) and "token" not in str(exc.value)
    assert len(calls)<=2
