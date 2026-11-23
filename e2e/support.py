"""Journey helpers: every action goes through the real UI unless noted."""
import io
import json
import re
import uuid
from urllib.parse import urlsplit

from PIL import Image
from playwright.sync_api import expect

RED, BLUE, BLACK = (200, 30, 30), (30, 60, 200), (0, 0, 0)
WIDTH, HEIGHT = 400, 200
# Two rooms split at x=200, as a Foundry scene (image pixels, no padding).
WALLS = [[10, 10, 390, 10], [390, 10, 390, 190], [390, 190, 10, 190], [10, 190, 10, 10], [200, 10, 200, 190]]


def unique(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def map_png(colour=RED):
    buffer = io.BytesIO()
    Image.new("RGB", (WIDTH, HEIGHT), colour).save(buffer, "PNG")
    return buffer.getvalue()


def walls_json():
    scene = {"name": "Two rooms", "width": WIDTH, "height": HEIGHT, "padding": 0, "grid": {"size": 100},
             "walls": [{"c": c, "move": 20, "sight": 20} for c in WALLS]}
    return json.dumps(scene).encode()


class Watch:
    """Console messages and uncaught errors from every page, for failure reports."""

    def __init__(self):
        self.lines, self.errors = [], []

    def attach(self, label, page):
        page.on("console", lambda message: self.lines.append(f"[{label}] {message.type}: {message.text}"))
        page.on("pageerror", lambda error: (self.errors.append(f"[{label}] {error}"),
                                            self.lines.append(f"[{label}] pageerror: {error}")))


def path_of(page):
    return urlsplit(page.url).path


def login(page, url, username, password, next_path=None):
    page.goto(f"{url}/login" + (f"?next={next_path}" if next_path else ""))
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    page.locator('button[type="submit"]').click()
    page.wait_for_load_state()


def flash_ok(page):
    expect(page.locator(".flash-ok")).to_be_visible()


class Admin:
    def __init__(self, page, url):
        self.page, self.url = page, url

    def create_campaign(self, name):
        self.page.goto(f"{self.url}/")
        form = self.page.locator('form[action="/campaigns"]')
        form.locator('input[name="name"]').fill(name)
        form.locator('button[type="submit"]').click()
        self.page.wait_for_url(re.compile(r"/campaigns/\d+"))
        return int(re.search(r"/campaigns/(\d+)", self.page.url).group(1))

    def api(self, method, path, body=None):
        """JSON call with this browser session, as the editors' own scripts make it."""
        token = self.page.evaluate("document.querySelector('meta[name=csrf-token]').content")
        response = self.page.request.fetch(f"{self.url}{path}", method=method, data=body,
                                           headers={"X-CSRF-Token": token, "Origin": self.url})
        assert response.ok, f"{method} {path}: {response.status} {response.text()}"
        return response.json()

    def import_map(self, cid, name, colour=RED):
        self.page.goto(f"{self.url}/campaigns/{cid}")
        form = self.page.locator(f'form[action="/campaigns/{cid}/maps"]')
        form.locator('input[name="image"]').set_input_files(
            {"name": "map.png", "mimeType": "image/png", "buffer": map_png(colour)})
        form.locator('input[name="walls"]').set_input_files(
            {"name": "walls.json", "mimeType": "application/json", "buffer": walls_json()})
        form.locator('input[name="name"]').fill(name)
        form.locator('button[type="submit"]').click()
        self.page.wait_for_url(re.compile(r"/maps/\d+"))
        return int(re.search(r"/maps/(\d+)", self.page.url).group(1))

    def create_viewer(self, cid, username, password):
        self.page.goto(f"{self.url}/campaigns/{cid}")
        self.page.get_by_text("Create a new viewer account").click()
        form = self.page.locator(f'form[action="/campaigns/{cid}/viewers/create"]')
        form.locator('input[name="username"]').fill(username)
        form.locator('input[name="password"]').fill(password)
        form.locator('button[type="submit"]').click()
        flash_ok(self.page)

    def show_map(self, cid, mid):
        self.page.goto(f"{self.url}/campaigns/{cid}")
        # Map names sit in rename inputs (values, not text), so find rows by map id.
        row = lambda: self.page.locator("tr", has=self.page.locator(f'form[action="/maps/{mid}/rename"]'))
        row().locator("form[data-map-display]").get_by_role("button", name="Show").click()
        expect(self.page.locator(".flash-ok")).to_contain_text("Viewer screen updated")
        expect(row().locator(".pill-live")).to_be_visible()

    def open_map(self, mid):
        self.page.goto(f"{self.url}/maps/{mid}")
        self.page.wait_for_function(f"document.querySelector('#map-img').naturalWidth === {WIDTH}")
        expect(self.page.locator("#busy")).to_be_hidden()
        self.mid = mid

    def click_map(self, x, y=HEIGHT / 2):
        box = self.page.locator("#map-img").bounding_box()
        self.page.mouse.click(box["x"] + box["width"] * x / WIDTH, box["y"] + box["height"] * y / HEIGHT)

    def fog(self, action, x, y=HEIGHT / 2):
        """Reveal or hide the area at image (x, y) with a real click in the fog editor."""
        self.page.locator("#fog-panel").evaluate("el => { el.open = true; }")
        self.page.locator(f'input[name="mode"][value="{action}"]').check()
        box = self.page.locator("#map-img").bounding_box()
        with self.page.expect_response(lambda r: urlsplit(r.url).path == f"/api/maps/{self.mid}/{action}"
                                       and r.request.method == "POST") as pending:
            self.page.mouse.click(box["x"] + box["width"] * x / WIDTH, box["y"] + box["height"] * y / HEIGHT)
        assert pending.value.status == 200, pending.value.text()
        expect(self.page.locator("#busy")).to_be_hidden()

    def undo(self):
        with self.page.expect_response(lambda r: urlsplit(r.url).path == f"/api/maps/{self.mid}/undo"
                                       and r.request.method == "POST") as pending:
            self.page.locator("#btn-undo").click()
        assert pending.value.status == 200, pending.value.text()
        expect(self.page.locator("#busy")).to_be_hidden()


class Player:
    def __init__(self, page, url, cid):
        self.page, self.url, self.cid = page, url, cid

    def first_login(self, username, temporary, password):
        """Forced change from a direct map link continues to the map (I1)."""
        login(self.page, self.url, username, temporary, next_path=f"/c/{self.cid}")
        expect(self.page).to_have_url(re.compile(r"/account"))
        self.page.locator('input[name="current_password"]').fill(temporary)
        self.page.locator('input[name="new_password"]').fill(password)
        self.page.locator('input[name="confirm_password"]').fill(password)
        self.page.locator('form[action="/account"] button[type="submit"]').click()
        expect(self.page).to_have_url(re.compile(rf"/c/{self.cid}$"))
        self.expect_live()

    def expect_live(self):
        expect(self.page.locator("#conn-dot")).to_have_class(re.compile(r"\bon\b"))

    def expect_pixels(self, name, points, tolerance=0):
        """Wait until the installed image shows these colours (exactly, or within tolerance)."""
        self.page.wait_for_function("""({name, points, width, height, tolerance}) => {
          const image = document.querySelector('#map'), stage = document.querySelector('#stage');
          if (stage.hidden || document.querySelector('#map-name').textContent !== name ||
              !image.complete || image.naturalWidth !== width) return false;
          const canvas = document.createElement('canvas'); canvas.width = width; canvas.height = height;
          const context = canvas.getContext('2d'); context.drawImage(image, 0, 0);
          return points.every(([x, y, rgb]) => {
            const pixel = context.getImageData(x, y, 1, 1).data;
            return rgb.every((value, i) => Math.abs(pixel[i] - value) <= tolerance);
          });
        }""", arg={"name": name, "width": WIDTH, "height": HEIGHT, "tolerance": tolerance,
                   "points": [[x, y, list(rgb)] for (x, y), rgb in points]}, timeout=15_000)
        expect(self.page.locator("#sync-status")).to_have_text("Up to date")


class Table:
    """A campaign with one two-room map shown to one player who has changed their password."""

    def __init__(self, server, actors, tolerance=0):
        self.server = server
        self.campaign, self.map_name = unique("Campaign"), unique("Map")
        self.username, self.password = unique("player"), "player-password-1"
        self.dm = Admin(actors("dm"), server.admin)
        login(self.dm.page, server.admin, "superadmin", "e2e-superadmin-password")
        expect(self.dm.page).not_to_have_url(re.compile(r"/login"))
        self.cid = self.dm.create_campaign(self.campaign)
        self.mid = self.dm.import_map(self.cid, self.map_name)
        self.dm.create_viewer(self.cid, self.username, "temporary-pass-1")
        self.dm.show_map(self.cid, self.mid)
        self.player = Player(actors("player"), server.viewer, self.cid)
        self.player.first_login(self.username, "temporary-pass-1", self.password)
        self.player.expect_pixels(self.map_name, [((100, 100), BLACK), ((300, 100), BLACK)], tolerance)
        self.dm.open_map(self.mid)
