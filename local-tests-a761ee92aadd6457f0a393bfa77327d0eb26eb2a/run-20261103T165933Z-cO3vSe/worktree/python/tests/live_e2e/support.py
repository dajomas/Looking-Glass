"""Setup uses authenticated real HTTP; tested fog gestures use the actual UI."""
import io
import json
import re
from PIL import Image
from playwright.sync_api import expect


class Session:
    def __init__(self, dm, player, admin_url, viewer_url):
        self.dm, self.player = dm, player
        self.admin_url, self.viewer_url = admin_url, viewer_url
        self.page_errors = []
        for name, page in (("dm", dm), ("player", player)):
            page.on("pageerror", lambda error, name=name: self.page_errors.append(f"{name}: {error}"))

    def login(self, page, url, username, password):
        from urllib.parse import urlsplit

        page.goto(url + "/login")
        page.locator('input[name="username"]').fill(username)
        page.locator('input[name="password"]').fill(password)
        page.locator('button[type="submit"]').click()
        page.wait_for_url(lambda url: "/login" not in urlsplit(url).path)

    def form(self, path, fields):
        response = self.dm.request.post(self.admin_url + path,
            form={"csrf_token": self.csrf, **fields}, max_redirects=0)
        assert response.status == 303, (response.status, response.text())
        location = response.headers["location"]
        assert "error=" not in location, location
        return location

    def post(self, path, payload):
        # fetch runs in the authenticated DM page, with production CSRF/cookies.
        result = self.dm.evaluate("""async ({path,payload}) => {
          const response = await fetch(path, {method:'POST',
            headers:{'Content-Type':'application/json',
              'X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content},
            body:JSON.stringify(payload)});
          return {status:response.status, body:await response.json()};
        }""", {"path": path, "payload": payload})
        assert result["status"] == 200 and result["body"].get("ok"), result
        return result["body"]

    def setup(self):
        self.login(self.dm, self.admin_url, "live-dm", "live-dm-password")
        self.csrf = self.dm.locator('meta[name="csrf-token"]').get_attribute("content")
        location = self.form("/campaigns", {"name":"Live E2E"})
        self.cid = int(re.search(r"/campaigns/(\d+)", location).group(1))
        self.a = self.upload("Red map", (200, 30, 30))
        self.b = self.upload("Green map", (30, 200, 30))
        self.form(f"/campaigns/{self.cid}/viewers/add", {"user_id":"2"})
        self.activate(self.a)
        self.open_editor(self.a)
        self.login(self.player, self.viewer_url, "live-player", "live-player-password")
        self.player.goto(f"{self.viewer_url}/c/{self.cid}")
        expect(self.player.locator("#conn-dot")).to_have_class(re.compile(r"\bon\b"), timeout=10000)
        self.expect_pixels("Red map", (0,0,0), (0,0,0))

    def upload(self, name, color):
        buffer = io.BytesIO()
        Image.new("RGB", (400,200), color).save(buffer, "PNG")
        walls = [[10,10,390,10],[390,10,390,190],[390,190,10,190],
                 [10,190,10,10],[200,10,200,190]]
        scene = {"name":"Two rooms", "width":400,"height":200,"padding":0,
                 "grid":{"size":100}, "walls":[{"c":c,"move":20,"sight":20} for c in walls]}
        response = self.dm.request.post(f"{self.admin_url}/campaigns/{self.cid}/maps",
            multipart={"csrf_token":self.csrf,"name":name,
              "image":{"name":"map.png","mimeType":"image/png","buffer":buffer.getvalue()},
              "walls":{"name":"walls.json","mimeType":"application/json","buffer":json.dumps(scene).encode()}},
            max_redirects=0)
        assert response.status == 303, response.text()
        location = response.headers["location"]
        match = re.search(r"/maps/(\d+)", location)
        assert match, location
        return int(match.group(1))

    def activate(self, mid):
        return self.post(f"/api/campaigns/{self.cid}/active", {"map_id":mid,"fog_action":"restore"})

    def open_editor(self, mid):
        self.dm.goto(f"{self.admin_url}/maps/{mid}")
        self.dm.wait_for_function("document.querySelector('#map-img').naturalWidth === 400")
        expect(self.dm.locator("#busy")).to_be_hidden()
        self.mid = mid

    def gesture(self, action, x=100):
        panel = self.dm.locator("#fog-panel")
        panel.evaluate("el => el.open = true")
        self.dm.locator(f'input[name="mode"][value="{action}"]').check()
        rect = self.dm.locator("#map-img").bounding_box()
        with self.dm.expect_response(lambda response: response.url.split('?')[0].endswith(
                f"/api/maps/{self.mid}/{action}") and response.request.method == "POST") as pending:
            self.dm.mouse.click(rect["x"] + rect["width"]*x/400,
                                rect["y"] + rect["height"]*.5)
        assert pending.value.status == 200, pending.value.text()
        expect(self.dm.locator("#busy")).to_be_hidden()

    def undo(self):
        with self.dm.expect_response(lambda response: response.url.endswith(
                f"/api/maps/{self.mid}/undo") and response.request.method == "POST") as pending:
            self.dm.locator("#btn-undo").click()
        assert pending.value.status == 200, pending.value.text()
        expect(self.dm.locator("#busy")).to_be_hidden()

    def state(self):
        response = self.player.request.get(f"{self.viewer_url}/api/c/{self.cid}/state")
        assert response.status == 200, response.text()
        return response.json()

    def expect_pixels(self, name, left, right):
        # Draw the image actually installed by production viewer JS, not a fresh
        # test-side image fetch. Pixel checks also detect server-side fog leaks.
        self.player.wait_for_function("""({name,left,right}) => {
          const image=document.querySelector('#map'), stage=document.querySelector('#stage');
          if(stage.hidden || document.querySelector('#map-name').textContent!==name ||
             !image.complete || image.naturalWidth!==400) return false;
          const c=document.createElement('canvas');c.width=400;c.height=200;
          const ctx=c.getContext('2d');ctx.drawImage(image,0,0);
          return [[100,left],[300,right]].every(([x,rgb]) => {
            const px=ctx.getImageData(x,100,1,1).data;
            return rgb.every((v,i)=>px[i]===v);
          });
        }""", arg={"name":name,"left":list(left),"right":list(right)}, timeout=10000)
        expect(self.player.locator("#sync-status")).to_have_text("Up to date", timeout=10000)
