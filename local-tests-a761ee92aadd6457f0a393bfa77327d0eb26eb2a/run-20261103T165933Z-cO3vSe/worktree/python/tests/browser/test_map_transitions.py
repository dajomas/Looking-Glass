"""Browser smoke tests use mocked HTTP; run with local Playwright Chromium."""
from test_portal_tools import admin
from playwright.sync_api import expect


def test_place_and_reposition_keeps_draft(admin):
    page,posts,data=admin
    page.locator("#map-passages-panel > summary").click()
    page.locator("#transition-add").click()
    point=page.evaluate("()=>{const p=window.testPZ,r=document.getElementById('viewport').getBoundingClientRect();return {x:r.left+p.x+100*p.scale,y:r.top+p.y+100*p.scale};}")
    page.mouse.click(point["x"],point["y"])
    expect(page.locator("#transition-editor")).to_be_visible()
    assert abs(float(page.locator("#tr-x").input_value())-100)<2 and not posts
    page.locator("#tr-name").fill("Upper ladder");page.locator("#tr-place").click()
    page.mouse.click(point["x"]+5,point["y"]+5)
    expect(page.locator("#tr-name")).to_have_value("Upper ladder")
    assert not posts
    page.locator("#tr-close").click()


def test_escape_cancels_placement(admin):
    page,posts,data=admin
    page.locator("#map-passages-panel > summary").click()
    page.locator("#transition-add").click();page.keyboard.press("Escape")
    expect(page.locator("#transition-status")).to_contain_text("cancelled")
    assert not posts
