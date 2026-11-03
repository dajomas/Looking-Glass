"""Focused browser regression; requires Playwright with Chromium installed.
Run: python python/tests/check_upload_busy_browser.py
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        pending = []
        release = asyncio.Event()
        async def route(request_route):
            if request_route.request.method == "POST":
                pending.append(request_route.request.post_data_buffer)
                await release.wait()
                await request_route.fulfill(status=200, body="Done")
            else:
                await request_route.fulfill(status=200, body="<html><body></body></html>")
        await page.route("https://looking-glass.test/**", route)
        await page.goto("https://looking-glass.test/")
        await page.set_content('''<iframe name="result" hidden></iframe>
<form id="native" method="post" action="/upload" target="result" enctype="multipart/form-data">
<input type="hidden" name="csrf_token" value="csrf-kept">
<input type="file" name="image" required><button name="action" value="import">Import</button></form>
<form id="custom"><input type="file"><button>Custom</button></form>
<form id="cancel" data-confirm="Really?"><input type="file"><button>Cancel test</button></form>''')
        await page.add_script_tag(content=(ROOT/"static/js/common.js").read_text())
        await page.add_script_tag(content=(ROOT/"static/js/upload_busy.js").read_text())
        await page.locator('#native button').click()
        assert await page.locator('#native').get_attribute('aria-busy') is None
        await page.locator('#native input[type=file]').set_input_files({"name":"map.png","mimeType":"image/png","buffer":b"file-content-kept"})
        await page.locator('#native button').click()
        await page.wait_for_function("document.querySelector('#native').getAttribute('aria-busy')==='true'")
        assert await page.locator('#native button').inner_text() == 'Processing…'
        assert await page.locator('#native [role=status]').is_visible()
        await page.evaluate("document.querySelector('#native').requestSubmit()")
        await page.locator('#native button').click(force=True)
        await page.wait_for_timeout(150)
        assert len(pending)==1
        body=pending[0]
        for value in (b'csrf-kept',b'file-content-kept',b'name="action"',b'import'):
            assert value in body, value
        await page.evaluate("document.querySelector('#custom').addEventListener('submit',e=>e.preventDefault())")
        await page.locator('#custom button').click()
        assert await page.locator('#custom').get_attribute('aria-busy') is None
        page.once('dialog',lambda dialog: dialog.dismiss())
        await page.locator('#cancel button').click()
        assert await page.locator('#cancel').get_attribute('aria-busy') is None
        await page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))")
        assert await page.locator('#native').get_attribute('aria-busy') is None
        assert await page.locator('#native button').inner_text()=='Import'
        assert await page.locator('#native button').get_attribute('aria-disabled') is None
        release.set()
        await browser.close()
        return ['native validation', 'immediate visible busy state', 'duplicate click/submit blocked',
                'file + CSRF + named submitter preserved', 'custom form skipped',
                'cancelled confirmation skipped', 'back-forward restoration']

if __name__=='__main__':
    print(asyncio.run(main()))
