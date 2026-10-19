// DM fog editor: click an area enclosed by walls to reveal / hide it for the players.
(function () {
  "use strict";
  const MAP_ID = window.LG_MAP.id;
  const CAMPAIGN_ID = window.LG_MAP.campaign_id;
  const $ = (id) => document.getElementById(id);

  const vp = $("viewport"), stage = $("stage"), img = $("map-img");
  const fogCanvas = $("fog-canvas"), svg = $("walls-svg");
  const toastEl = $("toast"), busyEl = $("busy");

  let state = null;        // last payload from /api/maps/:id
  let rawWalls = [];       // walls in source coordinates (for live alignment preview)
  let maskImg = null;
  let maskKey = "";
  let busy = false;
  const arrowHit = new LGDoorArrowHit();
  const stateKey = (s) => `${s.cache_token}-${s.walls_version}-${s.fog_version}`;
  let maskGeneration = 0, imageKey = "";
  const hiddenTypes = new Set();
  const typeNames = ["wall", "door", "secret", "window", "invisible", "ethereal"];
  const visibilityKey = `lg:hidden-wall-types:${MAP_ID}`;
  try {for (const k of JSON.parse(localStorage.getItem(visibilityKey) || "[]")) hiddenTypes.add(k);} catch (_) {}
  function loadError(message) {
    const el = $("map-load-error");
    if (el) {el.textContent = message; el.hidden = !message;}
  }

  let wallWidth = 2;
  function updateWallWidth() {
    const base = wallWidth / pz.scale;
    svg.style.setProperty("--sw", String(base));
    // Apply to existing paths too: changing a preference must not wait for a wall edit.
    for (const path of svg.querySelectorAll("path")) {
      const multiplier = path.classList.contains("w-door") || path.classList.contains("w-secret") ? 2 : 1;
      path.style.strokeWidth = `${base * multiplier}px`;
    }
  }
  const pz = new PanZoom(vp, stage, { secondaryTap: true, onTap, onChange: updateWallWidth });
  LGWallAppearance(MAP_ID, (width) => { wallWidth = width; updateWallWidth(); });

  // ------------------------------------------------------------------ UI helpers
  let toastTimer = null;
  function toast(msg, kind = "info", ms = 3500) {
    toastEl.textContent = msg;
    toastEl.className = `toast show toast-${kind}`;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (toastEl.className = "toast"), ms);
  }
  function setBusy(on) { busy = on; busyEl.hidden = !on; if (state) syncDoorArrowControls(); }
  const mode = () => document.querySelector('input[name="mode"]:checked').value;

  async function run(fn) {
    if (busy) return;
    setBusy(true);
    try { return await fn(); }
    catch (err) { toast(err.message, "error", 4000); }
    finally { setBusy(false); }
  }

  // ------------------------------------------------------------------ rendering
  function cal() {
    return {
      offset_x: parseFloat($("cal-ox").value) || 0,
      offset_y: parseFloat($("cal-oy").value) || 0,
      scale_x: parseFloat($("cal-sx").value) || 1,
      scale_y: parseFloat($("cal-sy").value) || 1,
      doors_block: $("cal-doors").checked,
    };
  }

  function fillCalibration(c) {
    $("cal-ox").value = +c.offset_x.toFixed(4);
    $("cal-oy").value = +c.offset_y.toFixed(4);
    $("cal-sx").value = +c.scale_x.toFixed(6);
    $("cal-sy").value = +c.scale_y.toFixed(6);
    $("cal-doors").checked = c.doors_block;
  }

  function renderWalls() {
    const c = cal();
    const paths = {};
    for (const [x1, y1, x2, y2, kind, blocks] of rawWalls) {
      if (hiddenTypes.has(kind)) continue;
      let k = kind;
      if (!blocks || (state?.disabled_wall_types || []).includes(kind) || ((kind === "door" || kind === "secret") && !c.doors_block)) k = "passive";
      const a = (x1 - c.offset_x) * c.scale_x, b = (y1 - c.offset_y) * c.scale_y;
      const d = (x2 - c.offset_x) * c.scale_x, e = (y2 - c.offset_y) * c.scale_y;
      (paths[k] ||= []).push(`M${a.toFixed(1)} ${b.toFixed(1)}L${d.toFixed(1)} ${e.toFixed(1)}`);
    }
    svg.innerHTML = Object.entries(paths)
      .map(([k, segs]) => `<path class="w-${k}" d="${segs.join("")}"/>`).join("");
    updateWallWidth();
  }

  function drawFog() {
    if (!state) return;
    const w = state.work_width, h = state.work_height;
    if (fogCanvas.width !== w || fogCanvas.height !== h) { fogCanvas.width = w; fogCanvas.height = h; }
    const ctx = fogCanvas.getContext("2d");
    ctx.globalCompositeOperation = "source-over";
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, w, h);
    if (maskImg) {
      ctx.globalCompositeOperation = "destination-out";
      ctx.drawImage(maskImg, 0, 0, w, h);
    }
    fogCanvas.style.opacity = $("show-preview").checked ? 1 : $("fog-opacity").value;
  }

  async function loadMask() {
    const key = `${state.cache_token}-${state.walls_version}-${state.fog_version}`;
    if (key === maskKey) return;
    const generation = ++maskGeneration;
    const im = new Image();
    im.src = `/api/maps/${MAP_ID}/fog.png?v=${key}`;
    const arrows = new Image();
    arrows.src = `/api/maps/${MAP_ID}/door-arrows.png?v=${key}`;
    await Promise.all([im.decode(), arrows.decode()]);
    if (generation !== maskGeneration) return;
    arrowHit.set(arrows, key);
    maskImg = im; maskKey = key;
    $("door-arrows").src = arrows.src;
    drawFog();
  }

  function applyState(s) {
    const first = state === null;
    state = s;
    syncDoorArrowControls();
    $("door-arrows").hidden = !s.door_arrows_enabled;
    const nextImageKey = s.image_version || `${s.cache_token}-${s.width}-${s.height}`;
    if (imageKey !== nextImageKey) {imageKey = nextImageKey; img.src = `/api/maps/${MAP_ID}/image?v=${encodeURIComponent(imageKey)}`;}
    loadError("");
    if (first || s.width !== pz.w || s.height !== pz.h) {
      pz.setContentSize(s.width, s.height);
      svg.setAttribute("viewBox", `0 0 ${s.width} ${s.height}`);
      pz.fit();
    }
    // keep source coordinates so alignment changes can be previewed client-side
    const c = s.calibration;
    rawWalls = s.walls.map(([a, b, d, e, k, bl]) =>
      [a / c.scale_x + c.offset_x, b / c.scale_y + c.offset_y, d / c.scale_x + c.offset_x, e / c.scale_y + c.offset_y, k, bl]);
    fillCalibration(c);
    for (const kind of typeNames) {
      const input = document.querySelector(`[data-wall-enabled="${kind}"]`);
      if (input) input.checked = !(s.disabled_wall_types || []).includes(kind);
    }
    renderWalls();
    $("wall-count").textContent = s.walls.length;
    $("wall-source").textContent = s.walls_source || (s.walls.length ? "" : "- import a Foundry wall file to enable area reveal");
    $("op-count").textContent = s.op_count;
    updateLive(s);
    drawFog();
    loadMask().catch((e) => loadError("Fog mask could not load: " + e.message + ". Use Retry loading map."));
  }

  function updateLive(s) {
    const live = $("live-state");
    live.textContent = s.is_active ? "Live on viewer screen" : "Not shown";
    live.className = "pill " + (s.is_active ? "pill-live" : "");
    $("btn-show").disabled = s.is_active;
    if ($("offline-reveal-warning")) $("offline-reveal-warning").hidden = s.is_active;
    $("live-viewers").textContent = `${s.live_viewers} player screen${s.live_viewers === 1 ? "" : "s"} connected`;
  }

  // ------------------------------------------------------------------ actions
  function onTap(x, y, event) {
    if (!state || x < 0 || y < 0 || x > state.width || y > state.height) return;
    if (busy || maskKey !== stateKey(state)) return; // Never act on an old overlay.
    const arrow = event?.button !== 2 ? arrowHit.at(x, y, state, stateKey(state)) : null;
    const selectedMode = mode();
    const m = arrow ? "reveal" : (event?.button === 2 ? (selectedMode === "reveal" ? "hide" : "reveal") : selectedMode);
    const path = arrow ? "door-arrows/reveal" : m;
    const body = arrow ? {...arrow, cache_token: state.cache_token,
      walls_version: state.walls_version, fog_version: state.fog_version} : {x, y};
    run(async () => {
      let res;
      try { res = await LGApi.post(`/api/maps/${MAP_ID}/${path}`, body); }
      catch (error) {
        if (arrow) {
          // Never fall through into a normal hide/reveal on a stale arrow click.
          try { applyState(await LGApi.get(`/api/maps/${MAP_ID}`)); } catch (_) {}
        }
        throw error;
      }
      applyState(res);
      const pct = (res.area_fraction * 100).toFixed(1);
      if (m === "reveal" && !res.is_active) {
        toast("Warning: this map is NOT shown to players. The reveal was saved on this map only." +
          (res.leak_warning ? " The revealed area may also have a wall gap." : ""), "warn", 7000);
      } else if (res.leak_warning) {
        toast(`That area covers ${pct}% of the map - the walls may have a gap. Ctrl+Z to undo.`, "warn", 7000);
      } else if (!state.walls.length) {
        toast("No walls imported: the whole map counts as one area.", "warn");
      } else {
        toast(`${m === "reveal" ? "Revealed" : "Hidden"} area (${pct}% of map)`);
      }
    });
  }

  const simple = (path, msg) => run(async () => {
    const result = await LGApi.post(`/api/maps/${MAP_ID}/${path}`); applyState(result);
    if (path === "reveal-all" && !result.is_active) toast("Warning: this map is NOT shown to players. Reveal all was saved on this map only.", "warn", 7000);
    else toast(msg);
  });

  $("btn-undo").onclick = () => simple("undo", "Undone");
  $("btn-reveal-all").onclick = () => simple("reveal-all", "Whole map revealed");
  $("btn-reset").onclick = () => { if (confirm("Cover the whole map in fog again?")) simple("reset", "Fog reset"); };

  async function setActive(mapId) {
    return await run(async () => {
      const name = mapId === MAP_ID && state ? state.name :
        ($("map-switch").selectedOptions[0]?.textContent || "this map");
      const fogAction = mapId === null ? null : await window.LGChooseFog(name, mapId);
      if (mapId !== null && !fogAction) return false;
      await LGApi.post(`/api/campaigns/${CAMPAIGN_ID}/active`, {map_id: mapId, fog_action: fogAction});
      if (mapId === MAP_ID || mapId === null) applyState(await LGApi.get(`/api/maps/${MAP_ID}`));
      toast(mapId ? "Now showing this map to players" : "Viewer screen blanked");
      return true;
    });
  }
  $("btn-show").onclick = () => setActive(MAP_ID);
  $("btn-blank").onclick = () => setActive(null);

  function syncDoorArrowControls() {
    $("door-arrow-color").value = state.door_arrow_color;
    $("door-arrows-enabled").checked = state.door_arrows_enabled;
    $("door-arrow-color").disabled = busy || !state.door_arrows_enabled;
    $("door-arrows-enabled").disabled = busy;
  }
  async function saveDoorArrows(change) {
    if (busy || !state) { if (state) syncDoorArrowControls(); return; }
    await run(async () => {
      syncDoorArrowControls();
      applyState(await LGApi.post(`/api/maps/${MAP_ID}/door-arrows`, change));
    });
    syncDoorArrowControls();
  }
  $("door-arrow-color").onchange = () => saveDoorArrows({color: $("door-arrow-color").value});
  $("door-arrows-enabled").onchange = () => saveDoorArrows({enabled: $("door-arrows-enabled").checked});
  vp.addEventListener("pointermove", (event) => {
    const point = pz.toImage(event.clientX, event.clientY);
    const hit = state && !busy && !pz.pointers.size && arrowHit.at(point.x, point.y, state, stateKey(state));
    vp.style.cursor = hit ? "pointer" : "";
  });
  vp.addEventListener("pointerleave", () => {vp.style.cursor = "";});
  $("fog-opacity").oninput = drawFog;
  $("show-preview").onchange = drawFog;
  $("show-walls").onchange = (e) => (svg.style.display = e.target.checked ? "" : "none");
  $("map-switch").onchange = async (e) => {
    const target = Number(e.target.value);
    if (await setActive(target)) location.href = `/maps/${target}`;
    else e.target.value = String(MAP_ID);
  };
  $("zoom-in").onclick = () => pz.zoomCenter(1.25);
  $("zoom-out").onclick = () => pz.zoomCenter(0.8);
  $("zoom-fit").onclick = () => pz.fit();

  // ------------------------------------------------------------------ alignment
  ["cal-ox", "cal-oy", "cal-sx", "cal-sy", "cal-doors"].forEach((id) => $(id).addEventListener("input", renderWalls));
  document.querySelectorAll("[data-nudge]").forEach((b) => b.addEventListener("click", (e) => {
    const [dx, dy] = b.dataset.nudge.split(",").map(Number);
    const step = e.shiftKey ? 10 : 1;           // image pixels
    const c = cal();
    $("cal-ox").value = +(c.offset_x - (dx * step) / c.scale_x).toFixed(4);
    $("cal-oy").value = +(c.offset_y - (dy * step) / c.scale_y).toFixed(4);
    renderWalls();
  }));
  $("btn-cal-save").onclick = () => run(async () => {
    applyState(await LGApi.post(`/api/maps/${MAP_ID}/calibration`, cal()));
    toast("Alignment applied - areas recalculated");
  });

  // ------------------------------------------------------------------ keyboard
  window.addEventListener("keydown", (e) => {
    if (/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) return;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") { e.preventDefault(); $("btn-undo").click(); return; }
    switch (e.key.toLowerCase()) {
      case "r": document.querySelector('input[name="mode"][value="reveal"]').checked = true; break;
      case "h": document.querySelector('input[name="mode"][value="hide"]').checked = true; break;
      case "f": pz.fit(); break;
      case "+": case "=": pz.zoomCenter(1.25); break;
      case "-": pz.zoomCenter(0.8); break;
    }
  });

  // ------------------------------------------------------------------ boot
  let startupRefreshScheduled = false;
  function refreshAfterArtwork() {
    if (busy) {setTimeout(refreshAfterArtwork, 50); return;}
    run(reloadMap);
  }
  img.onload = () => {
    if (!state) {pz.setContentSize(img.naturalWidth, img.naturalHeight); svg.setAttribute("viewBox", `0 0 ${img.naturalWidth} ${img.naturalHeight}`);}
    pz.fit();
    if (!startupRefreshScheduled) {
      startupRefreshScheduled = true;
      setTimeout(refreshAfterArtwork, 0);
    }
  };
  img.onerror = () => loadError("Map artwork could not load. Check the image file/server log and use Retry loading map.");
  // Load artwork independently: a failed metadata request must not leave an empty viewport.
  img.src = `/api/maps/${MAP_ID}/image?boot=${Date.now()}`;
  async function reloadMap() {
    try {applyState(await LGApi.get(`/api/maps/${MAP_ID}`));}
    catch (error) {loadError("Map state/walls could not load: " + error.message + ". Use Retry loading map."); throw error;}
  }
  if ($("retry-map-load")) $("retry-map-load").onclick = () => run(async () => {
    imageKey = ""; await reloadMap();
  });
  for (const input of document.querySelectorAll("[data-wall-show]")) {
    input.checked = !hiddenTypes.has(input.dataset.wallShow);
    input.onchange = () => {
      const kind = input.dataset.wallShow;
      if (input.checked) hiddenTypes.delete(kind); else hiddenTypes.add(kind);
      try {localStorage.setItem(visibilityKey, JSON.stringify([...hiddenTypes]));} catch (_) {}
      renderWalls();
    };
  }
  $("apply-wall-types").onclick = () => run(async () => {
    const disabled = [...document.querySelectorAll("[data-wall-enabled]")].filter(el => !el.checked).map(el => el.dataset.wallEnabled);
    applyState(await LGApi.post(`/api/maps/${MAP_ID}/wall-types`, {disabled_wall_types: disabled}));
    toast("Wall types applied; areas recalculated");
  });
  run(reloadMap);
  setInterval(async () => {
    try {
      const s = await LGApi.get(`/api/maps/${MAP_ID}`);
      if (!state || s.fog_version !== state.fog_version || s.walls_version !== state.walls_version) applyState(s);
      else updateLive(s);
    } catch (_) { /* ignore */ }
  }, 15000);
})();
