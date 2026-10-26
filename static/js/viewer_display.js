// Player display: shows the server-composited fogged map and updates live via WebSocket.
(function () {
  "use strict";
  const CID = window.LG_CAMPAIGN;
  const $ = (id) => document.getElementById(id);
  const vp = $("viewport"), stage = $("stage"), mapImg = $("map");
  const waiting = $("waiting"), dot = $("conn-dot"), nameEl = $("map-name");

  const pz = new PanZoom(vp, stage, {onTap});
  // This viewer owns its resize policy, including focused-room framing.
  pz._onResize = () => {};
  const taps = new LGViewerDoubleTap();
  let version = null, refreshGeneration = 0, zoomGeneration = 0;
  let interactionGeneration = 0, remoteGeneration = 0;
  const remoteCommands = new Set();
  let revealBounds = null, currentMap = null, focusPoint = null, focusBounds = null;
  function target(bounds) {
    return currentMap ? LGViewerAreaZoom.target(bounds, currentMap.width, currentMap.height,
      pz, vp.getBoundingClientRect()) : null;
  }
  function centerReveals() {
    if (stage.hidden || !currentMap) return;
    if (revealBounds) LGViewerAreaZoom.apply(pz, target(revealBounds));
    else pz.fit();
  }
  function showOverview() {
    ++interactionGeneration;
    ++zoomGeneration; taps.cancel(); focusPoint = focusBounds = null;
    centerReveals();
  }
  function cancelLookup(clearFocus=false) {
    ++zoomGeneration; taps.cancel();
    if (clearFocus) focusPoint = focusBounds = null;
  }
  async function lookup(point, toggle) {
    const requestedVersion = version, generation = ++zoomGeneration;
    try {
      const query = new URLSearchParams({x:String(point.x),y:String(point.y),v:requestedVersion});
      const response = await fetch(`/api/c/${CID}/area-bounds?${query}`, {
        credentials:"same-origin", cache:"no-store", headers:{Accept:"application/json"}});
      if (generation !== zoomGeneration || version !== requestedVersion || stage.hidden) return;
      if (response.status === 401) {location.href="/login?next="+encodeURIComponent(location.pathname); return;}
      if (!response.ok) {await refresh(); return;}
      const result = await response.json();
      if (generation !== zoomGeneration || version !== requestedVersion || stage.hidden || result.version !== requestedVersion) return;
      if (!result.bounds) {
        if (!toggle) {focusPoint = focusBounds = null; centerReveals();}
        return;
      }
      const pose = target(result.bounds);
      if (toggle && LGViewerAreaZoom.matches(pz, pose)) {showOverview(); return;}
      focusPoint = point; focusBounds = result.bounds;
      LGViewerAreaZoom.apply(pz, pose);
    } catch (error) {
      if (generation === zoomGeneration) console.error("Room zoom lookup failed",error);
    }
  }
  function onTap(x,y,event) {
    if (stage.hidden || !currentMap || event?.button !== 0 || x<0 || y<0 || x>=pz.w || y>=pz.h) {taps.cancel(); return;}
    const cx = Number.isFinite(event.clientX) ? event.clientX : x*pz.scale;
    const cy = Number.isFinite(event.clientY) ? event.clientY : y*pz.scale;
    if (!taps.tap(cx,cy,Date.now())) return;
    const point = {x:x*currentMap.width/pz.w, y:y*currentMap.height/pz.h};
    lookup(point,true);
  }
  vp.addEventListener("pointerdown", event => {
    ++interactionGeneration;
    ++zoomGeneration;
    if (pz.spaceDown || pz.pointers.size > 1 || event.button !== 0) taps.cancel();
  });
  vp.addEventListener("pointermove", () => {if (pz.moved && pz.pointers.size) {++interactionGeneration; cancelLookup(true);}});
  vp.addEventListener("pointercancel", () => {++interactionGeneration; cancelLookup();});
  vp.addEventListener("wheel", () => {++interactionGeneration; cancelLookup(true);}, {passive:true});
  vp.addEventListener("dblclick", event => event.preventDefault());
  window.addEventListener("blur", () => {++interactionGeneration; cancelLookup();});

  let syncState = "loading", syncVersion = "blank";
  function reportSync(state, displayed) {
    syncState = state; syncVersion = displayed;
    const online = ws && ws.readyState === 1;
    const label = $("sync-status");
    if (label) label.textContent = online ? ({ready:"Up to date",loading:"Loading",failed:"Display failed"}[state] || "Connected") : "Reconnecting";
    if (online) {
      try {ws.send(JSON.stringify({type:"viewer-status",state,version:displayed}));} catch (_) {}
    }
  }
  async function refresh() {
    const generation = ++refreshGeneration;
    try {
    const resp = await fetch(`/api/c/${CID}/state`, { credentials: "same-origin", cache: "no-store", headers: { Accept: "application/json" } });
    if (generation !== refreshGeneration) return;
    if (resp.status === 401) { reportSync("failed",syncVersion); location.href = "/login?next=" + encodeURIComponent(location.pathname); return; }
    if (!resp.ok) { reportSync("failed",syncVersion); cancelLookup(true); stage.hidden = true; waiting.hidden = false; $("waiting-text").textContent = "This campaign is no longer available."; return; }
    const s = await resp.json();
    if (generation !== refreshGeneration) return;
    if (!s.map) {
      cancelLookup(true); version = null; currentMap = revealBounds = null;
      stage.hidden = true; waiting.hidden = false; nameEl.textContent = "";
      $("waiting-text").textContent = "The Dungeon Master is preparing the scene…";
      reportSync("ready","blank");
      return;
    }
    if (s.map.version === version) {reportSync("ready",version); return;}
    reportSync("loading",s.map.version);
    const mapChanged = !version || version.split("-")[0] !== s.map.version.split("-")[0];
    // Preload so the swap is seamless (no flash of fog on every reveal).
    const next = new Image();
    next.src = s.map.image_url;
    let decodeTimeout;
    try {
      await Promise.race([next.decode(), new Promise((_,reject) => {
        decodeTimeout = setTimeout(() => reject(new Error("Display image timeout")),30000);
      })]);
    } finally {clearTimeout(decodeTimeout);}
    if (generation !== refreshGeneration) return;
    const hasNewAreas = !mapChanged && LGViewerHasNewAreas(currentMap,s.map);
    mapImg.src = next.src;
    cancelLookup(mapChanged || hasNewAreas);
    version = s.map.version;
    currentMap = s.map;
    nameEl.textContent = s.map.name;
    waiting.hidden = true; stage.hidden = false;
    pz.setContentSize(next.naturalWidth, next.naturalHeight);
    revealBounds = s.map.revealed_bounds || null;
    if (focusPoint && !mapChanged) {focusBounds = null; await lookup(focusPoint,false);}
    else centerReveals();
    if (generation === refreshGeneration) reportSync("ready",version);
    } catch (error) {
      if (generation === refreshGeneration) {reportSync("failed",syncVersion); console.error("Viewer refresh failed",error);}
    }
  }

  async function remoteZoom(msg) {
    if (typeof msg.command_id !== "string" || !msg.command_id || msg.command_id.length>128 ||
        typeof msg.version !== "string" || !msg.point ||
        !Number.isFinite(msg.point.x) || !Number.isFinite(msg.point.y) || remoteCommands.has(msg.command_id)) return;
    remoteCommands.add(msg.command_id);
    if (remoteCommands.size>64) remoteCommands.delete(remoteCommands.values().next().value);
    const generation = ++remoteGeneration, interaction = interactionGeneration;
    cancelLookup();
    if (msg.version !== version || stage.hidden) await refresh();
    if (generation !== remoteGeneration || interaction !== interactionGeneration ||
        stage.hidden || msg.version !== version) return;
    // Reuse the unchanged local double-click path, including authorized current-area lookup.
    await lookup({x:msg.point.x,y:msg.point.y},true);
  }

  let ws = null, retry = 1000, pingTimer = null, lastMessage = 0;
  function connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${proto}://${location.host}/ws/c/${CID}`);
    ws = socket;
    socket.onopen = () => {
      if (ws !== socket) return;
      dot.classList.add("on"); retry = 1000; lastMessage = Date.now();
      reportSync(syncState,syncVersion); refresh();
      clearInterval(pingTimer);
      pingTimer = setInterval(() => {
        if (ws !== socket || socket.readyState !== 1) return;
        if (Date.now()-lastMessage > 65000) {socket.close(); return;}
        try {socket.send("ping"); reportSync(syncState,syncVersion);} catch (_) {socket.close();}
      },25000);
    };
    socket.onmessage = ev => {
      if (ws !== socket) return;
      lastMessage = Date.now();
      let msg; try {msg = JSON.parse(ev.data);} catch (_) {return;}
      if (!msg || typeof msg !== "object") return;
      if (msg.type === "refresh") refresh();
      if (msg.type === "viewer-zoom") remoteZoom(msg).catch(console.error);
    };
    socket.onerror = () => {if (ws === socket) socket.close();};
    socket.onclose = ev => {
      if (ws !== socket) return;
      dot.classList.remove("on"); clearInterval(pingTimer);
      reportSync(syncState,syncVersion);
      if (ev.code === 4401 || ev.code === 4403 || ev.code === 4404) {refresh(); setTimeout(connect,10000); return;}
      setTimeout(connect,retry); retry = Math.min(retry*2,15000);
    };
  }

  $("btn-fit").onclick = showOverview;
  $("btn-full").onclick = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen());
  window.addEventListener("keydown", (e) => { if (e.key.toLowerCase() === "f") $("btn-fit").click(); });
  // Auto-hide HUD when idle
  let hudT; const hud = $("hud");
  const wake = () => { hud.classList.remove("idle"); clearTimeout(hudT); hudT = setTimeout(() => hud.classList.add("idle"), 3000); };
  ["pointermove", "pointerdown", "keydown"].forEach((ev) => window.addEventListener(ev, wake));
  wake();

  let resizeTimer;
  window.addEventListener("resize", () => {++interactionGeneration; clearTimeout(resizeTimer); resizeTimer=setTimeout(() => {
    cancelLookup();
    if (!stage.hidden && focusBounds) LGViewerAreaZoom.apply(pz,target(focusBounds));
    else {focusPoint = null; centerReveals();}
  },180);});
  stage.hidden = true;
  refresh().catch(console.error);
  connect();
  setInterval(() => refresh().catch(() => {}), 40000); // safety net if a WS message is missed
})();
