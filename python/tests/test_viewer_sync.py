from looking_glass.services.viewer_sync import ViewerSync, display_version


def tracker():
    now=[100.0]
    return ViewerSync(lambda:now[0]),now


def test_version_and_blank():
    assert display_version(None)=="blank"
    assert display_version(dict(id=2,cache_token="token",walls_version=3,fog_version=4))=="2:token-3-4"


def test_loading_ready_stale_version_and_blank():
    hub,now=tracker();key=hub.connect(1,7,"Alice")
    snap=lambda v:hub.snapshot(1,v)["viewers"][0]["status"]
    assert snap("v1")=="connected"
    assert hub.report(key,dict(type="viewer-status",state="loading",version="v1"))
    assert snap("v1")=="loading"
    hub.report(key,dict(type="viewer-status",state="ready",version="v1"))
    assert snap("v1")=="up-to-date" and snap("v2")=="loading"
    hub.report(key,dict(type="viewer-status",state="ready",version="blank"))
    assert snap("blank")=="up-to-date" and hub.snapshot(1,"blank")["blank"]


def test_failure_disconnect_retention_and_heartbeat():
    hub,now=tracker();key=hub.connect(1,7,"Alice")
    hub.report(key,dict(type="viewer-status",state="failed",version="old"))
    assert hub.snapshot(1,"new")["viewers"][0]["status"]=="failed"
    now[0]+=66
    assert hub.snapshot(1,"new")["viewers"][0]["status"]=="reconnecting"
    hub.report(key,dict(type="viewer-status",state="ready",version="new"))
    assert hub.snapshot(1,"new")["viewers"][0]["status"]=="up-to-date"
    hub.disconnect(key)
    assert not hub.report(key,dict(type="viewer-status",state="ready",version="new"))
    assert hub.snapshot(1,"new")["viewers"][0]["status"]=="reconnecting"
    now[0]+=91
    assert hub.snapshot(1,"new")["viewers"]==[]


def test_per_tab_isolation_and_untrusted_input():
    hub,now=tracker();a=hub.connect(1,7,"Alice");b=hub.connect(1,7,"Alice");c=hub.connect(2,7,"Alice")
    assert len(hub.snapshot(1,"v")["viewers"])==2
    for bad in [None,[],{},dict(type="viewer-status",state="ready",version=[]),
                dict(type="viewer-status",state="ready",version="x"*201),
                dict(type="viewer-status",state="hacked",version="v")]:
        assert not hub.report(a,bad)
    hub.report(a,dict(type="viewer-status",state="ready",version="v"))
    assert hub.snapshot(1,"v")["counts"]["up-to-date"]==1
    assert hub.snapshot(2,"v")["counts"]["connected"]==1
    assert not hub.report("unknown",dict(type="viewer-status",state="ready",version="v"))


def test_disconnect_idempotent_and_bounded_history():
    hub,now=tracker()
    for _ in range(1030):hub.disconnect(hub.connect(1,7,"Alice"))
    assert len(hub.records)==1024
    key=hub.connect(1,7,"Alice");hub.disconnect(key);closed=hub.records[key]["closed"]
    now[0]+=1;hub.disconnect(key)
    assert hub.records[key]["closed"]==closed


def test_legacy_ping_keeps_connected_without_false_readiness():
    hub,now=tracker();key=hub.connect(1,7,"Old client")
    now[0]+=60;hub.touch(key);now[0]+=20
    assert hub.snapshot(1,"v")["viewers"][0]["status"]=="connected"
    assert hub.snapshot(1,"v")["viewers"][0]["last_report_seconds"]==20
