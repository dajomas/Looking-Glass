import concurrent.futures
import pytest
from looking_glass.services import scrying_glass as sg, scrying_glass_access as access

RAW={"enabled":True,"base_url":"https://sg.example","username":"dm","password":"secret","password_env":""}
DATA={"campaigns":[{"id":"1","name":"Crypt","setups":["guard-room"]}]}

@pytest.fixture
def cached(monkeypatch):
    now=[100.0];calls=[]
    def fetch(config):
        calls.append(config.username)
        return DATA
    cache=access.CatalogCache(clock=lambda:now[0],fetcher=fetch)
    monkeypatch.setattr(access,"cache",cache)
    return cache,now,calls

def test_disabled_and_unnamed_do_not_contact_remote(cached):
    _,_,calls=cached
    assert not access.access({},"Crypt")["enabled"]
    assert access.lookup(RAW,"Crypt","")["status"]=="unnamed_room"
    assert access.lookup({},"Crypt","")["status"]=="disabled"
    assert calls==[]

def test_verify_then_match_reuses_catalog(cached):
    _,_,calls=cached
    assert access.access(RAW,"Crypt")["verified"]
    assert access.lookup(RAW,"Crypt","Guard Room")["matched"]
    assert not access.lookup(RAW,"Crypt","Other")["matched"]
    assert len(calls)==1

def test_inaccessible_campaign_blocks_matching(cached):
    assert access.access(RAW,"Other")["status"]=="campaign_not_accessible"
    result=access.lookup(RAW,"Other","Guard Room")
    assert not result["verified"] and not result["matched"]

def test_ambiguous_campaign_not_verified(cached):
    cache,_,_=cached;cache.fetcher=lambda _: {"campaigns":DATA["campaigns"]*2}
    assert access.access(RAW,"Crypt")["status"]=="ambiguous_campaign"

def test_expiry_config_identity_and_bounds(cached):
    cache,now,calls=cached
    access.access(RAW,"Crypt");now[0]+=61;access.access(RAW,"Crypt");assert len(calls)==2
    access.access({**RAW,"password":"changed"},"Crypt");assert len(calls)==3
    for i in range(12):access.access({**RAW,"username":str(i)},"Crypt")
    assert len(cache.entries)<=access.MAX_ENTRIES
    assert all("secret" not in key for key in cache.entries)

def test_failure_backoff_and_recovery(cached):
    cache,now,calls=cached
    def fail(_):
        calls.append("fail");raise sg.LookupError("unavailable")
    cache.fetcher=fail
    for _ in range(3):
        with pytest.raises(sg.LookupError):access.access(RAW,"Crypt")
    assert len(calls)==1
    now[0]+=31;cache.fetcher=lambda _:DATA
    assert access.access(RAW,"Crypt")["verified"]

def test_concurrent_requests_share_one_fetch(cached):
    _,_,calls=cached
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results=list(pool.map(lambda _:access.access(RAW,"Crypt"),range(10)))
    assert all(r["verified"] for r in results) and len(calls)==1

def test_invalid_schema_and_configuration(cached):
    cache,_,_=cached;cache.fetcher=lambda _: {"bad":True}
    with pytest.raises(sg.LookupError):access.access(RAW,"Crypt")
    with pytest.raises(sg.LookupError):access.access({**RAW,"base_url":"file:///etc/passwd"},"Crypt")
