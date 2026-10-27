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
  let portalCycle = null;
  let mapTransitions = null;
  let doubleReveal = null;
  const arrowHit = new LGDoorArrowHit();
  const doorTapQueue = new LGDoorTapQueue();
  const areaTaps = new LGAdminAreaTaps();
  const stateKey = (s) => `${s.cache_token}-${s.walls_version}-${s.fog_version}-${Number(s.door_arrows_enabled)}`;
  let maskGeneration = 0, imageKey = "";
  const hiddenTypes = new Set();
  const typeNames = ["wall", "door", "locked_door", "unlocked_door", "secret", "portal", "window", "invisible", "ethereal"];
  const visibilityKey = `lg:hidden-wall-types:${MAP_ID}`;
  try {for (const k of JSON.parse(localStorage.getItem(visibilityKey) || "[]")) hiddenTypes.add(k);} catch (_) {}
  function loadError(message) {
    const el = $("map-load-error");
    if (el) {el.textContent = message; el.hidden = !message;}
  }

  let wallWidth = 2;
  function updateWallWidth() {
    areaTaps.cancel();
    mapTransitions?.draw();
    portalCycle?.refresh();
    const base = wallWidth / pz.scale;
    svg.style.setProperty("--sw", String(base));
    // Apply to existing paths too: changing a preference must not wait for a wall edit.
    for (const path of svg.querySelectorAll("path")) {
      const multiplier = path.classList.contains("w-door") || path.classList.contains("w-secret") || path.classList.contains("w-locked_door") || path.classList.contains("w-unlocked_door") ? 2 : 1;
      path.style.strokeWidth = `${base * multiplier}px`;
    }
  }
  const pz = new PanZoom(vp, stage, { secondaryTap: true, onTap, onChange: updateWallWidth });
  LGWallAppearance(MAP_ID, (width) => { wallWidth = width; updateWallWidth(); });
  portalCycle = LGPortalCycle.mount({svg:$("portal-cycle-overlay"),slider:$("portal-cycle-seconds"),output:$("portal-cycle-value"),toggle:$("portal-cycle-enabled"),status:$("portal-cycle-status"),mapId:MAP_ID,
    view:()=>{if(!state)return null;const r=vp.getBoundingClientRect();return {x:pz.x,y:pz.y,scale:pz.scale,workScale:state.work_scale,width:r.width,height:r.height};}});

  mapTransitions = LGMapTransitions.mount({mapId:MAP_ID,campaignId:CAMPAIGN_ID,scale:()=>pz.scale,
    dimensions:()=>state?{width:state.width,height:state.height}:null,
    cancelGestures:()=>{areaTaps.cancel();doorTapQueue.cancel();},
    onSaved:async()=>applyState(await LGApi.get(`/api/maps/${MAP_ID}`))});

  // ------------------------------------------------------------------ UI helpers
  let toastTimer = null;
  function toast(msg, kind = "info", ms = 3500) {
    toastEl.textContent = msg;
    toastEl.className = `toast show toast-${kind}`;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (toastEl.className = "toast"), ms);
  }
  function setBusy(on) { busy = on; portalCycle?.setBusy(on); if (on) {doorTapQueue.cancel(); areaTaps.cancel();} busyEl.hidden = !on; if (state) syncDoorArrowControls(); }
  const mode = () => document.querySelector('input[name="mode"]:checked').value;

  async function run(fn) {
    if (busy) return;
    setBusy(true);
    try { return await fn(); }
    catch (err) { toast(err.message, "error", 4000); }
    finally { setBusy(false); }
  }

  const roomNotes = new LGRoomNotes(MAP_ID, toast);
  doubleReveal = LGDoubleReveal({mapId:MAP_ID,run,reload:reloadMap});

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
      if (!blocks || (state?.disabled_wall_types || []).includes(kind) || (["door", "secret", "locked_door", "unlocked_door", "portal"].includes(kind) && !c.doors_block)) k = ["locked_door", "unlocked_door"].includes(kind) ? kind + " passive" : "passive";
      const a = (x1 - c.offset_x) * c.scale_x, b = (y1 - c.offset_y) * c.scale_y;
      const d = (x2 - c.offset_x) * c.scale_x, e = (y2 - c.offset_y) * c.scale_y;
      (paths[k] ||= []).push(`M${a.toFixed(1)} ${b.toFixed(1)}L${d.toFixed(1)} ${e.toFixed(1)}`);
    }
    svg.innerHTML = Object.entries(paths)
      .map(([k, segs]) => `<path class="w-${k}" d="${segs.join("")}"/>`).join("");
    for (const p of state?.portal_styles || []) {
      if (hiddenTypes.has("portal")) continue;
      const dx=p.x2-p.x1,dy=p.y2-p.y1,len=Math.hypot(dx,dy)||1;
      p.sides.forEach((side,i)=>{
        if(side.role==="none")return;
        const sign=i===0?-1:1,offset=2/pz.scale;
        const path=document.createElementNS(svg.namespaceURI,"path");
        const kind=["entry","both"].includes(side.role)?side.kind:"door";
        path.setAttribute("class",`portal-side p-${kind}`);
        path.setAttribute("d",`M${p.x1-sign*dy/len*offset} ${p.y1+sign*dx/len*offset}L${p.x2-sign*dy/len*offset} ${p.y2+sign*dx/len*offset}`);
        svg.appendChild(path);
      });
    }
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
    const key = stateKey(state);
    if (key === maskKey) {portalCycle?.setState(state,true);return;}
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
    portalCycle?.setMask(arrows.src);
    portalCycle?.setState(state,true);
    drawFog();
  }

  function applyState(s) {
    const first = state === null;
    doorTapQueue.cancel(); areaTaps.cancel();
    state = s;
    roomNotes.refresh(s);
    doubleReveal?.refresh(s);
    mapTransitions?.draw();
    portalCycle?.setState(s,false);
    syncDoorArrowControls();
    $("door-arrows").hidden = !s.door_arrows_enabled;
    const nextImageKey = `${s.image_version || s.cache_token}-${s.double_reveal_image ? `${s.walls_version}-${s.fog_version}` : "original"}`;
    if (imageKey !== nextImageKey) {imageKey = nextImageKey; img.src = `/api/maps/${MAP_ID}/${s.double_reveal_image ? "double-reveal/artwork" : "image"}?v=${encodeURIComponent(imageKey)}`;}
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
    doubleReveal?.refresh(s);
    if ($("offline-reveal-warning")) $("offline-reveal-warning").hidden = s.is_active;
    $("live-viewers").textContent = `${s.live_viewers} player screen${s.live_viewers === 1 ? "" : "s"} connected`;
  }

  // ------------------------------------------------------------------ actions
  function onTap(x, y, event) {
    if (doubleReveal?.selecting()) {
      areaTaps.cancel();doorTapQueue.cancel();
      if (state && !busy && event?.button === 0 && x>=0 && y>=0 && x<state.width && y<state.height)
        run(()=>doubleReveal.select(x,y));
      return;
    }
    if (state && !busy && roomNotes.editing() && event?.button === 0) {
      areaTaps.cancel(); doorTapQueue.cancel();
      run(() => roomNotes.select(x,y,true)); return;
    }
    if (state && !busy && x>=0 && y>=0 && x<state.width && y<state.height && mapTransitions?.tap(x,y,event)) {
      areaTaps.cancel();doorTapQueue.cancel();return;
    }
    if (!state || busy || maskKey !== stateKey(state) || x<0 || y<0 || x>=state.width || y>=state.height) return;
    const alpha = arrowHit.at(x,y,state,stateKey(state));
    const door = LGManagedDoorHit(state,alpha,x,y,pz.scale,$("show-walls").checked,hiddenTypes);
    if (door || alpha || event?.button !== 0) {
      areaTaps.cancel(); performMapTap(x,y,event); return;
    }
    doorTapQueue.cancel();
    const stamp = stateKey(state), selectedMode = mode();
    const cx = Number.isFinite(event.clientX) ? event.clientX : x*pz.scale;
    const cy = Number.isFinite(event.clientY) ? event.clientY : y*pz.scale;
    areaTaps.tap(cx,cy,stamp,() => {
      if (!state || busy || stamp !== stateKey(state) || mode() !== selectedMode) return;
      performMapTap(x,y,event);
    },() => {
      if (!state || busy || stamp !== stateKey(state)) return;
      const body = {x,y,cache_token:state.cache_token,walls_version:state.walls_version,fog_version:state.fog_version};
      run(async () => {
        let result;
        try {result = await LGApi.post(`/api/maps/${MAP_ID}/viewer-zoom`,body);}
        catch(error) {try {applyState(await LGApi.get(`/api/maps/${MAP_ID}`));} catch(_) {} throw error;}
        if (result.reason === "not-revealed") toast("Only revealed areas can control viewer zoom.","warn");
        else if (!result.viewers) toast("No viewer screens are connected.","warn");
        else toast(`Zoom command sent to ${result.viewers} viewer screen${result.viewers===1 ? "" : "s"}.`);
      });
    });
  }

  function performMapTap(x, y, event) {
    if (!state || x < 0 || y < 0 || x > state.width || y > state.height) return;
    if (busy || maskKey !== stateKey(state)) return; // Never act on an old overlay.
    const alphaPoint = arrowHit.at(x, y, state, stateKey(state));
    const managed = LGManagedDoorHit(state, alphaPoint, x, y, pz.scale, $("show-walls").checked, hiddenTypes);
    if (managed?.blocked) return;
    if (managed && event?.button !== 2) {
      const stamp = stateKey(state);
      const body = {...managed, mode: mode(), tolerance: Math.min(500, 10/pz.scale), cache_token: state.cache_token,
        walls_version: state.walls_version, fog_version: state.fog_version};
      const act = (gesture) => {
        if (!state || busy || stamp !== stateKey(state)) return;
        run(async () => {
          let result;
          try { result = await LGApi.post(`/api/maps/${MAP_ID}/door-action`, {...body, gesture}); }
          catch (error) { try { applyState(await LGApi.get(`/api/maps/${MAP_ID}`)); } catch (_) {} throw error; }
          applyState(result);
          if (result.door_action === "reveal" || result.door_action === "hide") {
            toast(result.is_active ? (result.door_action === "reveal" ? "Area revealed" : "Area hidden") : "Warning: this map is NOT shown to players. Fog action saved on this map only.", result.is_active ? "info" : "warn");
          } else if (result.door_action !== "none") toast(result.door_action === "discover" ? "Secret passage discovered; fog unchanged" : result.door_action === "lock" ? "Passage locked" : "Passage unlocked; fog unchanged");
        });
      };
      doorTapQueue.tap(`${managed.hit}:${managed.wall_id}:${managed.side ?? -1}`, stamp, () => act("single"), () => act("double"));
      return;
    }
    if (managed && (managed.side >= 0 || ["locked_door","secret"].includes(managed.kind))) return;
    doorTapQueue.cancel();
    const arrow = event?.button !== 2 ? alphaPoint : null;
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
      await roomNotes.select(x,y);
      if (res.changed === false) {toast("Room selected; fog unchanged"); return;}
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
    $("locked-door-arrow-color").value = state.locked_door_arrow_color;
    $("locked-door-arrow-color").disabled = busy || !(state.door_arrows_enabled || state.viewer_door_arrows_enabled || state.viewer_portal_arrows_enabled || state.viewer_secret_arrows_enabled);
    $("door-arrows-enabled").checked = state.door_arrows_enabled;
    $("door-arrow-color").disabled = busy || !(state.door_arrows_enabled || state.viewer_door_arrows_enabled || state.viewer_portal_arrows_enabled || state.viewer_secret_arrows_enabled);
    $("door-arrows-enabled").disabled = busy;
    $("viewer-door-arrows-enabled").checked = state.viewer_door_arrows_enabled;
    $("viewer-door-arrows-enabled").disabled = busy;
    $("viewer-arrow-exceptions").hidden = !!state.viewer_door_arrows_enabled;
    for (const category of ["portal", "secret"]) {
      const control = $(`viewer-${category}-arrows-enabled`);
      control.checked = !!state[`viewer_${category}_arrows_enabled`];
      control.disabled = busy;
    }
  }
  async function saveDoorArrows(change) {
    if (busy || !state) { if (state) syncDoorArrowControls(); return; }
    await run(async () => {
      syncDoorArrowControls();
      applyState(await LGApi.post(`/api/maps/${MAP_ID}/door-arrows`, change));
    });
    syncDoorArrowControls();
  }
  $("locked-door-arrow-color").onchange = () => saveDoorArrows({locked_color: $("locked-door-arrow-color").value});
  $("door-arrow-color").onchange = () => saveDoorArrows({color: $("door-arrow-color").value});
  $("door-arrows-enabled").onchange = () => saveDoorArrows({admin_enabled: $("door-arrows-enabled").checked});
  $("viewer-door-arrows-enabled").onchange = () => saveDoorArrows({viewer_enabled: $("viewer-door-arrows-enabled").checked});
  $("viewer-portal-arrows-enabled").onchange = () => saveDoorArrows({viewer_portal_enabled: $("viewer-portal-arrows-enabled").checked});
  $("viewer-secret-arrows-enabled").onchange = () => saveDoorArrows({viewer_secret_enabled: $("viewer-secret-arrows-enabled").checked});
  vp.addEventListener("pointermove", (event) => {
    const point = pz.toImage(event.clientX, event.clientY);
    const hit = state && !busy && !pz.pointers.size && arrowHit.at(point.x, point.y, state, stateKey(state));
    vp.style.cursor = hit ? "pointer" : "";
  });
  vp.addEventListener("wheel", () => {doorTapQueue.cancel(); areaTaps.cancel();}, {passive:true});
  vp.addEventListener("pointerdown", event => {if (pz.spaceDown || pz.pointers.size>1 || event.button!==0) areaTaps.cancel();});
  vp.addEventListener("pointercancel", () => areaTaps.cancel());
  vp.addEventListener("dblclick", event => event.preventDefault());
  window.addEventListener("keydown", () => areaTaps.cancel());
  window.addEventListener("resize", () => areaTaps.cancel());
  document.querySelectorAll('input[name="mode"]').forEach(input => input.addEventListener("change",() => areaTaps.cancel()));
  $("viewer-portal-arrows-enabled").onchange = () => saveDoorArrows({viewer_portal_enabled: $("viewer-portal-arrows-enabled").checked});
  $("viewer-secret-arrows-enabled").onchange = () => saveDoorArrows({viewer_secret_enabled: $("viewer-secret-arrows-enabled").checked});
  vp.addEventListener("pointermove", () => {if (pz.moved && pz.pointers.size) {doorTapQueue.cancel(); areaTaps.cancel();}});
  window.addEventListener("blur", () => {doorTapQueue.cancel(); areaTaps.cancel();});
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
      case "r": doubleReveal?.leaveSelection(); document.querySelector('input[name="mode"][value="reveal"]').checked = true; break;
      case "h": doubleReveal?.leaveSelection(); document.querySelector('input[name="mode"][value="hide"]').checked = true; break;
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
    if (!state) pz.fit();
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
      if (!state || s.fog_version !== state.fog_version || s.walls_version !== state.walls_version ||
          s.door_arrows_enabled !== state.door_arrows_enabled || s.viewer_door_arrows_enabled !== state.viewer_door_arrows_enabled ||
          s.viewer_portal_arrows_enabled !== state.viewer_portal_arrows_enabled ||
          s.viewer_secret_arrows_enabled !== state.viewer_secret_arrows_enabled) applyState(s);
      else updateLive(s);
    } catch (_) { /* ignore */ }
  }, 15000);
})();
