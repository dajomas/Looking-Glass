"""Chromium UI via intercepted transport to authenticated in-process HTTP.

Uses real templates/scripts/SQLite/geometry and real API handlers. The proxy
uses the existing DM TestClient session, not real browser-cookie login or live
listeners. A one-record page-size fixture exercises paging cheaply.
"""
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_web import env
from test_room_note_archive_web import (
    flow, detach, save, recover, recovery_body, ok, archives, note_only_guard, MARKDOWN,
)


@pytest.fixture
def workspace(flow,browser):
    source=detach(flow)
    context=browser.new_context()
    page=context.new_page()
    requests=[]
    decisions=[]
    errors=[]
    page.on("pageerror",lambda error:errors.append(str(error)))
    page.on("dialog",lambda dialog:dialog.accept() if decisions and decisions.pop(0) else dialog.dismiss())
    def proxy(route):
        request=route.request
        url=urlsplit(request.url)
        if url.netloc!="recovery.test":
            route.abort();return
        path=url.path+("?"+url.query if url.query else "")
        if request.method=="POST":requests.append(path)
        headers={key:value for key,value in request.headers.items() if key in ("content-type","x-csrf-token","accept")}
        response=flow.dm.request(request.method,path,content=request.post_data,headers=headers,follow_redirects=False)
        body=response.content
        if url.path.endswith("/room-note-recovery") and response.status_code==200:
            body=response.text.replace('data-page-size="50"','data-page-size="1"').encode()
        returned={key:value for key,value in response.headers.items() if key not in ("content-length","content-encoding","transfer-encoding","connection","set-cookie")}
        route.fulfill(status=response.status_code,headers=returned,body=body)
    page.route("**/*",proxy)
    path=f"http://recovery.test/maps/{flow.mid}/room-note-recovery"
    try:
        yield page,source,requests,decisions,errors,path
    finally:
        context.close()


def inspect_target(page):
    page.locator("#recovery-x").fill("100")
    page.locator("#recovery-y").fill("50")
    page.get_by_role("button",name="Inspect target room").click()
    expect(page.locator("#recovery-status")).to_contain_text("Target inspected")


def test_explicit_cancel_and_recovery_preserve_archive_and_viewer(flow,workspace):
    page,source,requests,decisions,errors,path=workspace
    before=note_only_guard(flow)
    flow.publications.clear()
    page.goto(path)
    page.locator(f"[data-archive-id='{source['id']}']").click()
    expect(page.locator("#recovery-source")).to_have_text(MARKDOWN)
    assert page.locator("#recovery-source script").count()==0
    expect(page.locator("#recovery-apply")).to_be_disabled()
    inspect_target(page)
    decisions.append(False)
    page.locator("#recovery-apply").click()
    assert not any(url.endswith("/recover") for url in requests)
    decisions.append(True)
    page.locator("#recovery-apply").click()
    expect(page.locator("#recovery-status")).to_contain_text("Recovered. Source archive retained")
    expect(page.locator("#recovery-target-markdown")).to_have_text(MARKDOWN)
    assert archives(flow)==[source]
    assert note_only_guard(flow)==before and flow.publications==[]
    assert errors==[]


def test_stale_recovery_preserves_preview_and_requires_explicit_reinspection(flow,workspace):
    page,source,requests,decisions,errors,path=workspace
    save(flow,"Existing","Reviewed target")
    page.goto(path)
    page.locator(f"[data-archive-id='{source['id']}']").click()
    inspect_target(page)
    page.locator("#recovery-apply").click()
    expect(page.locator("#recovery-status")).to_contain_text("Check replacement confirmation")
    assert not any(url.endswith("/recover") for url in requests)
    page.locator("#recovery-replace").check()
    save(flow,"Concurrent","New saved target")
    decisions.append(True)
    page.locator("#recovery-apply").click()
    expect(page.locator("#recovery-status")).to_contain_text("Recovery was not acknowledged")
    expect(page.locator("#recovery-target-markdown")).to_have_text("Reviewed target")
    expect(page.locator("#recovery-source")).to_have_text(MARKDOWN)
    expect(page.locator("#recovery-apply")).to_be_disabled()
    assert sum(url.endswith("/room-at") for url in requests)==1
    assert sum(url.endswith("/recover") for url in requests)==1
    inspect_target(page)
    expect(page.locator("#recovery-target-markdown")).to_have_text("New saved target")
    expect(page.locator("#recovery-replace")).not_to_be_checked()
    page.locator("#recovery-replace").check()
    decisions.append(True)
    page.locator("#recovery-apply").click()
    expect(page.locator("#recovery-status")).to_contain_text("Recovered. Source archive retained")
    replaced=next(row for row in archives(flow) if row["reason"]=="recovery_replacement")
    assert (replaced["name"],replaced["markdown"])==("Concurrent","New saved target")
    assert errors==[]


def test_pagination_preserves_selected_source_and_makes_no_recovery_request(flow,workspace):
    page,source,requests,decisions,errors,path=workspace
    for index in range(2):
        save(flow,f"Target {index}",f"Replacement {index}")
        ok(recover(flow,source,recovery_body(flow,overwrite=True)))
    page.goto(path)
    page.locator("[data-archive-id]").first.click()
    selected=page.locator("#recovery-source").text_content()
    page.locator("#recovery-more").click()
    expect(page.locator("[data-archive-id]")).to_have_count(2)
    page.locator("#recovery-more").click()
    expect(page.locator("[data-archive-id]")).to_have_count(3)
    expect(page.locator("#recovery-more")).to_be_hidden()
    assert page.locator("#recovery-source").text_content()==selected
    assert not any(url.endswith("/recover") for url in requests)
    assert errors==[]
