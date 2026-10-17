// Player display: shows the server-composited fogged map and updates live via WebSocket.
(function () {
  "use strict";
  const CID = window.LG_CAMPAIGN;
  const $ = (id) => document.getElementById(id);
  const vp = $("viewport"), stage = $("stage"), mapImg = $("map");
  const waiting = $("waiting"), dot = $("conn-dot"), nameEl = $("map-name");

  const pz = new PanZoom(vp, stage, {});
  let version = null;
  let refreshGeneration = 0;
  let userMoved = false;
  let revealBounds = null;
  function centerReveals() {
    if (!revealBounds) {pz.fit(); return;}
    const box = vp.getBoundingClientRect();
    const sx = mapImg.naturalWidth / revealBounds.imageWidth;
    const sy = mapImg.naturalHeight / revealBounds.imageHeight;
    const b = revealBounds;
    pz.scale = Math.max(pz.minScale, Math.min(pz.maxScale,
      0.90 * Math.min(box.width / Math.max(1,b.width*sx), box.height / Math.max(1,b.height*sy))));
    pz.x = box.width/2 - (b.x+b.width/2)*sx*pz.scale;
    pz.y = box.height/2 - (b.y+b.height/2)*sy*pz.scale;
    pz.apply();
  }
  vp.addEventListener("pointerdown", () => (userMoved = true));
  vp.addEventListener("wheel", () => (userMoved = true), { passive: true });

  async function refresh() {
    const generation = ++refreshGeneration;
    const resp = await fetch(`/api/c/${CID}/state`, { credentials: "same-origin", cache: "no-store", headers: { Accept: "application/json" } });
    if (generation !== refreshGeneration) return;
    if (resp.status === 401) { location.href = "/login?next=" + encodeURIComponent(location.pathname); return; }
    if (!resp.ok) { stage.hidden = true; waiting.hidden = false; $("waiting-text").textContent = "This campaign is no longer available."; return; }
    const s = await resp.json();
    if (generation !== refreshGeneration) return;
    if (!s.map) {
      version = null;
      stage.hidden = true; waiting.hidden = false; nameEl.textContent = "";
      return;
    }
    if (s.map.version === version) return;
    const mapChanged = !version || version.split("-")[0] !== s.map.version.split("-")[0];
    // Preload so the swap is seamless (no flash of fog on every reveal).
    const next = new Image();
    next.src = s.map.image_url;
    await next.decode();
    if (generation !== refreshGeneration) return;
    mapImg.src = next.src;
    version = s.map.version;
    nameEl.textContent = s.map.name;
    waiting.hidden = true; stage.hidden = false;
    pz.setContentSize(next.naturalWidth, next.naturalHeight);
    revealBounds = s.map.revealed_bounds ? {...s.map.revealed_bounds, imageWidth:s.map.width, imageHeight:s.map.height} : null;
    userMoved = false; centerReveals();
  }

  let ws = null, retry = 1000, pingTimer = null;
  function connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/ws/c/${CID}`);
    ws.onopen = () => { dot.classList.add("on"); retry = 1000; refresh(); pingTimer = setInterval(() => ws.send("ping"), 25000); };
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "refresh") refresh().catch(console.error);
    };
    ws.onclose = (ev) => {
      dot.classList.remove("on"); clearInterval(pingTimer);
      if (ev.code === 4401 || ev.code === 4403 || ev.code === 4404) { refresh(); setTimeout(connect, 10000); return; }
      setTimeout(connect, retry); retry = Math.min(retry * 2, 15000);
    };
  }

  $("btn-fit").onclick = () => { userMoved = false; centerReveals(); };
  $("btn-full").onclick = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen());
  window.addEventListener("keydown", (e) => { if (e.key.toLowerCase() === "f") $("btn-fit").click(); });
  // Auto-hide HUD when idle
  let hudT; const hud = $("hud");
  const wake = () => { hud.classList.remove("idle"); clearTimeout(hudT); hudT = setTimeout(() => hud.classList.add("idle"), 3000); };
  ["pointermove", "pointerdown", "keydown"].forEach((ev) => window.addEventListener(ev, wake));
  wake();

  let resizeTimer;
  window.addEventListener("resize", () => {clearTimeout(resizeTimer); resizeTimer=setTimeout(centerReveals,180);});
  stage.hidden = true;
  refresh().catch(console.error);
  connect();
  setInterval(() => refresh().catch(() => {}), 40000); // safety net if a WS message is missed
})();
