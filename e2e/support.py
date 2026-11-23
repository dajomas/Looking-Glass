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


# The same two rooms with a door in the divider (Foundry: door 1, ds 2 = locked).
def door_walls(locked=False):
    door = {"door": 1, "ds": 2 if locked else 0}
    return [*WALLS[:4], [200, 10, 200, 80], ([200, 80, 200, 120], door), [200, 120, 200, 190]]


def walls_json(walls=WALLS):
    entries = []
    for wall in walls:
        coords, extra = (wall if isinstance(wall, tuple) else (wall, {}))
        entries.append({"c": coords, "move": 20, "sight": 20, **extra})
    scene = {"name": "Two rooms", "width": WIDTH, "height": HEIGHT, "padding": 0, "grid": {"size": 100},
             "walls": entries}
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

    def import_map(self, cid, name, colour=RED, walls=WALLS, walls_file=None):
        """Import through the campaign form; walls=None imports the image only."""
        self.page.goto(f"{self.url}/campaigns/{cid}")
        form = self.page.locator(f'form[action="/campaigns/{cid}/maps"]')
        form.locator('input[name="image"]').set_input_files(
            {"name": "map.png", "mimeType": "image/png", "buffer": map_png(colour)})
        if walls_file is not None:
            form.locator('input[name="walls"]').set_input_files(str(walls_file))
        elif walls is not None:
            form.locator('input[name="walls"]').set_input_files(
                {"name": "walls.json", "mimeType": "application/json", "buffer": walls_json(walls)})
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

    def show_map(self, cid, mid, choice=None):
        """Show a map; choice answers the Restore/Reset dialog for maps with saved reveals."""
        self.page.goto(f"{self.url}/campaigns/{cid}")
        # Map names sit in rename inputs (values, not text), so find rows by map id.
        row = lambda: self.page.locator("tr", has=self.page.locator(f'form[action="/maps/{mid}/rename"]'))
        row().locator("form[data-map-display]").get_by_role("button", name="Show").click()
        if choice is not None:
            dialog = self.page.locator("#map-display-dialog")
            expect(dialog).to_be_visible()
            label = {"restore": "Restore saved reveals", "reset": "Reset fog and show map"}[choice]
            dialog.get_by_role("button", name=label).click()
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

    def save_room_note(self, x, name, markdown, y=HEIGHT / 2):
        """Name a room and save Markdown notes through the Room notes panel."""
        self.page.locator("#room-select-mode").check()
        # The panel loads after a server round trip: unnamed rooms open the editor
        # by themselves, named rooms open in read mode. Wait for the lookup, then
        # for exactly one of the two panels, then act on whichever it is.
        with self.page.expect_response(lambda r: urlsplit(r.url).path.endswith("/room-at")):
            self.click_map(x, y)
        form = self.page.locator("#room-form")
        expect(self.page.locator("#room-form:not([hidden]), #room-read:not([hidden])")).to_have_count(1)
        if not form.is_visible():
            self.page.locator("#room-edit").click()
        expect(form).to_be_visible()
        self.page.locator("#room-name").fill(name)
        self.page.locator("#room-markdown").fill(markdown)
        form.get_by_role("button", name="Save room").click()
        expect(self.page.locator("#room-title")).to_have_text(name)
        self.page.locator("#room-select-mode").uncheck()

    def arrow_point(self):
        """Image coordinates of the centre of the drawn door arrows (opaque pixels)."""
        self.page.wait_for_function("""() => { const a = document.querySelector('#door-arrows');
            return a && !a.hidden && a.complete && a.naturalWidth > 0; }""")
        point = self.page.evaluate("""(width) => {
          const image = document.querySelector('#door-arrows');
          const canvas = document.createElement('canvas');
          canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
          const context = canvas.getContext('2d'); context.drawImage(image, 0, 0);
          const data = context.getImageData(0, 0, canvas.width, canvas.height).data;
          let sx = 0, sy = 0, n = 0;
          for (let y = 0; y < canvas.height; y++) for (let x = 0; x < canvas.width; x++)
            if (data[(y * canvas.width + x) * 4 + 3] > 200) { sx += x; sy += y; n++; }
          return n ? [(sx / n + 0.5) * width / canvas.width, (sy / n + 0.5) * width / canvas.width] : null;
        }""", WIDTH)
        assert point, "no door arrow is drawn"
        return point

    def door(self, x, y, gesture):
        """Single or double click on a managed door arrow; returns the server's door action."""
        box = self.page.locator("#map-img").bounding_box()
        target = (box["x"] + box["width"] * x / WIDTH, box["y"] + box["height"] * y / HEIGHT)
        with self.page.expect_response(lambda r: urlsplit(r.url).path.endswith("/door-action")
                                       and r.request.method == "POST") as pending:
            if gesture == "double":
                self.page.mouse.dblclick(*target)
            else:
                self.page.mouse.click(*target)
        assert pending.value.status == 200, pending.value.text()
        expect(self.page.locator("#busy")).to_be_hidden()
        return pending.value.json()["door_action"]

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

    def map_width(self):
        return self.page.locator("#map").bounding_box()["width"]

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

    def __init__(self, server, actors, tolerance=0, walls=WALLS):
        self.server = server
        self.campaign, self.map_name = unique("Campaign"), unique("Map")
        self.username, self.password = unique("player"), "player-password-1"
        self.dm = Admin(actors("dm"), server.admin)
        login(self.dm.page, server.admin, "superadmin", "e2e-superadmin-password")
        expect(self.dm.page).not_to_have_url(re.compile(r"/login"))
        self.cid = self.dm.create_campaign(self.campaign)
        self.mid = self.dm.import_map(self.cid, self.map_name, walls=walls)
        self.dm.create_viewer(self.cid, self.username, "temporary-pass-1")
        self.dm.show_map(self.cid, self.mid)
        self.player = Player(actors("player"), server.viewer, self.cid)
        self.player.first_login(self.username, "temporary-pass-1", self.password)
        self.player.expect_pixels(self.map_name, [((100, 100), BLACK), ((300, 100), BLACK)], tolerance)
        self.dm.open_map(self.mid)
