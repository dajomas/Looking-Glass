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

  const pz = new PanZoom(vp, stage, { onTap, onChange: () => svg.style.setProperty("--sw", (2 / pz.scale).toFixed(3)) });

  // ------------------------------------------------------------------ UI helpers
  let toastTimer = null;
  function toast(msg, kind = "info", ms = 3500) {
    toastEl.textContent = msg;
    toastEl.className = `toast show toast-${kind}`;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (toastEl.className = "toast"), ms);
  }
  function setBusy(on) { busy = on; busyEl.hidden = !on; }
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
      let k = kind;
      if (!blocks || ((kind === "door" || kind === "secret") && !c.doors_block)) k = "passive";
      const a = (x1 - c.offset_x) * c.scale_x, b = (y1 - c.offset_y) * c.scale_y;
      const d = (x2 - c.offset_x) * c.scale_x, e = (y2 - c.offset_y) * c.scale_y;
      (paths[k] ||= []).push(`M${a.toFixed(1)} ${b.toFixed(1)}L${d.toFixed(1)} ${e.toFixed(1)}`);
    }
    svg.innerHTML = Object.entries(paths)
      .map(([k, segs]) => `<path class="w-${k}" d="${segs.join("")}"/>`).join("");
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
    const im = new Image();
    im.src = `/api/maps/${MAP_ID}/fog.png?v=${key}`;
    await im.decode();
    maskImg = im; maskKey = key;
    drawFog();
  }

  function applyState(s) {
    const first = state === null;
    state = s;
    if (first) img.src = `/api/maps/${MAP_ID}/image?v=${s.cache_token}`;
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
    renderWalls();
    $("wall-count").textContent = s.walls.length;
    $("wall-source").textContent = s.walls_source || (s.walls.length ? "" : "- import a Foundry wall file to enable area reveal");
    $("op-count").textContent = s.op_count;
    updateLive(s);
    loadMask().catch((e) => toast("Fog mask failed: " + e.message, "error"));
  }

  function updateLive(s) {
    const live = $("live-state");
    live.textContent = s.is_active ? "Live on viewer screen" : "Not shown";
    live.className = "pill " + (s.is_active ? "pill-live" : "");
    $("btn-show").disabled = s.is_active;
    $("live-viewers").textContent = `${s.live_viewers} player screen${s.live_viewers === 1 ? "" : "s"} connected`;
  }

  // ------------------------------------------------------------------ actions
  function onTap(x, y) {
    if (!state || x < 0 || y < 0 || x > state.width || y > state.height) return;
    const m = mode();
    run(async () => {
      const res = await LGApi.post(`/api/maps/${MAP_ID}/${m}`, { x, y });
      applyState(res);
      const pct = (res.area_fraction * 100).toFixed(1);
      if (res.leak_warning) {
        toast(`That area covers ${pct}% of the map - the walls may have a gap. Ctrl+Z to undo.`, "warn", 7000);
      } else if (!state.walls.length) {
        toast("No walls imported: the whole map counts as one area.", "warn");
      } else {
        toast(`${m === "reveal" ? "Revealed" : "Hidden"} area (${pct}% of map)`);
      }
    });
  }

  const simple = (path, msg) => run(async () => { applyState(await LGApi.post(`/api/maps/${MAP_ID}/${path}`)); toast(msg); });

  $("btn-undo").onclick = () => simple("undo", "Undone");
  $("btn-reveal-all").onclick = () => simple("reveal-all", "Whole map revealed");
  $("btn-reset").onclick = () => { if (confirm("Cover the whole map in fog again?")) simple("reset", "Fog reset"); };

  async function setActive(mapId) {
    let fogAction = null;
    if (mapId !== null) {
      fogAction = await window.LGChooseFog(state ? state.name : "this map");
      if (!fogAction) return;
    }
    await run(async () => {
      await LGApi.post(`/api/campaigns/${CAMPAIGN_ID}/active`, { map_id: mapId, fog_action: fogAction });
      applyState(await LGApi.get(`/api/maps/${MAP_ID}`));
      toast(mapId ? "Now showing this map to players" : "Viewer screen blanked");
    });
  }
  $("btn-show").onclick = () => setActive(MAP_ID);
  $("btn-blank").onclick = () => setActive(null);

  $("fog-opacity").oninput = drawFog;
  $("show-preview").onchange = drawFog;
  $("show-walls").onchange = (e) => (svg.style.display = e.target.checked ? "" : "none");
  $("map-switch").onchange = (e) => (location.href = `/maps/${e.target.value}`);
  $("zoom-in").onclick = () => pz.zoomCenter(1.25);
  $("zoom-out").onclick = () => pz.zoomCenter(0.8);
  $("zoom-fit").onclick = () => pz.fit();

  // ------------------------------------------------------------------ walls import
  $("wall-file").onchange = () => run(async () => {
    const f = $("wall-file").files[0];
    const pick = $("scene-pick"), sel = $("scene-select");
    sel.innerHTML = ""; pick.hidden = true;
    if (!f) return;
    const fd = new FormData(); fd.append("file", f);
    const res = await LGApi.post(`/api/maps/${MAP_ID}/walls/inspect`, fd);
    for (const s of res.scenes) {
      const o = document.createElement("option");
      o.value = s.index;
      o.textContent = `${s.name} - ${s.walls} walls, ${s.doors} doors`;
      sel.appendChild(o);
    }
    pick.hidden = res.scenes.length < 2;
    const s = res.scenes[0];
    toast(`${res.scenes.length} scene(s) found (${s.format}). First: ${s.walls} walls.`);
  });

  $("wall-import").onsubmit = (ev) => {
    ev.preventDefault();
    const f = $("wall-file").files[0];
    if (!f) return;
    if (state.walls.length && !confirm("Replace the existing walls? Fog will be recalculated.")) return;
    run(async () => {
      const fd = new FormData();
      fd.append("file", f);
      fd.append("scene_index", $("scene-select").value || "0");
      fd.append("use_scene_calibration", $("use-scene-cal").checked ? "true" : "false");
      const res = await LGApi.post(`/api/maps/${MAP_ID}/walls`, fd);
      applyState(res);
      toast(`Imported ${res.imported} walls from "${res.scene}"`);
    });
  };

  $("btn-clear-walls").onclick = () => {
    if (!confirm("Remove all walls from this map?")) return;
    run(async () => { applyState(await LGApi.del(`/api/maps/${MAP_ID}/walls`)); toast("Walls cleared"); });
  };

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
  img.onload = () => { if (state) pz.fit(); };
  run(async () => applyState(await LGApi.get(`/api/maps/${MAP_ID}`)));
  setInterval(async () => {
    try {
      const s = await LGApi.get(`/api/maps/${MAP_ID}`);
      if (s.fog_version !== state.fog_version || s.walls_version !== state.walls_version) applyState(s);
      else updateLive(s);
    } catch (_) { /* ignore */ }
  }, 15000);
})();
