// Separate wall editor. Draft coordinates are image pixels, never viewport pixels.
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const id = window.LG_MAP.id, url = `/api/maps/${id}/wall-editor`;
  const vp = $("wall-viewport"), stage = $("wall-stage"), svg = $("wall-overlay"), img = $("wall-image");
  const kinds = new Set(["wall", "door", "locked_door", "unlocked_door", "secret", "portal", "window", "invisible", "ethereal"]);
  const editDialog = $("wall-edit-dialog"), editForm = $("wall-edit-form"), editError = $("wall-edit-error");
  const coordinateFields = ["wall-edit-x1", "wall-edit-y1", "wall-edit-x2", "wall-edit-y2"].map($);
  let editing = null;
  // A popup opened on pointerup may receive the later contextmenu event itself.
  // Capture on the document so both viewport and modal events are cancelled.
  document.addEventListener("contextmenu", (event) => {
    if (vp.contains(event.target) || editDialog.contains(event.target)) event.preventDefault();
  }, { capture: true });
  let state = null, walls = [], saved = "[]", start = null, undo = [], redo = [], busy = false;
  let wallWidth = 2, dragging = null;
  const JOIN = 0.5;  // image px: endpoints this close form one corner
  const pz = new PanZoom(vp, stage, { secondaryTap: true, onTap, onDragStart, onChange: render });
  LGWallAppearance(id, (width) => {
    wallWidth = width;
    render();
  });
  const snapshot = () => JSON.stringify(walls);
  const dirty = () => snapshot() !== saved;
  function status(text, error = false) { $("wall-status").textContent = text; $("wall-status").dataset.error = String(error); }
  function setBusy(on) { busy = on; $("wall-tools").disabled = on || !state; $("wall-retry").disabled = on; }
  async function run(fn) {
    if (busy) return;
    setBusy(true);
    try { await fn(); } catch (e) { status(e.message, true); }
    finally { setBusy(false); }
  }
  function render() {
    if (!state) return;
    // Same screen-pixel sizing as the fog editor: stage zoom scales this back up.
    const baseWidth = wallWidth / pz.scale;
    svg.style.setProperty("--wall-width", String(baseWidth));
    const paths = new Map();
    for (const [x1, y1, x2, y2, rawKind] of walls) {
      const kind = kinds.has(rawKind) ? rawKind : "wall";
      if (!paths.has(kind)) paths.set(kind, []);
      paths.get(kind).push(`M${x1} ${y1}L${x2} ${y2}`);
    }
    svg.replaceChildren();
    // Keep every label above every wall stroke, including later portal elements.
    const labelLayer = document.createElementNS(svg.namespaceURI, "g");
    labelLayer.setAttribute("class", "portal-label-layer");
    for (const [kind, lines] of paths) {
      const path = document.createElementNS(svg.namespaceURI, "path");
      path.setAttribute("class", `w-${kind}`); path.setAttribute("d", lines.join(""));
      const multiplier = ["door", "secret", "locked_door", "unlocked_door"].includes(kind) ? 2 : 1;
      path.style.strokeWidth = `${baseWidth * multiplier}px`;
      path.style.vectorEffect = "none";
      svg.appendChild(path);
    }
    walls.forEach((w,index) => {
      if (w[4] !== "portal") return;
      const dx=w[2]-w[0],dy=w[3]-w[1],len=Math.hypot(dx,dy)||1;
      [-1,1].forEach((sign,i) => {
        const side=w[6]?.sides?.[i];
        if(side && !["none","unconfigured"].includes(side.role)) {
          const path=document.createElementNS(svg.namespaceURI,"path"),offset=2/pz.scale;
          const kind=["entry","both"].includes(side.role)?side.kind:"door";
          path.setAttribute("class",`portal-side p-${kind}`);
          path.setAttribute("d",`M${w[0]-sign*dy/len*offset} ${w[1]+sign*dx/len*offset}L${w[2]-sign*dy/len*offset} ${w[3]+sign*dx/len*offset}`);
          path.style.strokeWidth=`${baseWidth}px`;svg.appendChild(path);
        }
        const text=document.createElementNS(svg.namespaceURI,"text");
        text.setAttribute("x",(w[0]+w[2])/2-sign*dy/len*22/pz.scale);
        text.setAttribute("y",(w[1]+w[3])/2+sign*dx/len*22/pz.scale);
        text.setAttribute("font-size",12/pz.scale);
        text.setAttribute("class","portal-label-text");
        text.setAttribute("text-anchor","middle");text.textContent=`${index+1}.${LGPortalDraft.sideName(w,i,true)}`;
        const label = document.createElementNS(svg.namespaceURI,"g");
        label.setAttribute("class","portal-label");
        const background = document.createElementNS(svg.namespaceURI,"rect");
        background.setAttribute("class","portal-label-background");
        label.append(background,text);labelLayer.appendChild(label);
      });
    });
    svg.appendChild(labelLayer);
    // Measure actual glyph bounds after attachment; padding/radius remain screen-pixel sized.
    for (const label of labelLayer.children) {
      const background = label.firstElementChild, text = label.lastElementChild;
      const box = text.getBBox(), padX = 4/pz.scale, padY = 2.5/pz.scale;
      background.setAttribute("x",box.x-padX);background.setAttribute("y",box.y-padY);
      background.setAttribute("width",box.width+2*padX);background.setAttribute("height",box.height+2*padY);
      background.setAttribute("rx",3/pz.scale);background.setAttribute("ry",3/pz.scale);
    }
    if (start) {
      const circle = document.createElementNS(svg.namespaceURI, "circle");
      circle.setAttribute("cx", start.x); circle.setAttribute("cy", start.y);
      circle.setAttribute("r", 5 / pz.scale); circle.setAttribute("class", "wall-start"); svg.appendChild(circle);
    }
    $("wall-count").textContent = `${walls.length} segments${dirty() ? " — unsaved changes" : " — saved"}`;
    $("wall-undo").disabled = !undo.length; $("wall-redo").disabled = !redo.length;
  }
  function apply(change, forward) {
    const before = forward ? change.before : change.after, after = forward ? change.after : change.before;
    if (change.batch) { walls = structuredClone(after); return; }
    walls.splice(change.index, before ? 1 : 0, ...(after ? [structuredClone(after)] : []));
  }
  function mutate(change) {
    if (!change.batch && change.after?.[4] === "portal" && change.before?.[4] !== "portal") {
      change.after[6] = LGPortalDraft.blank();
    }
    undo.push(change); redo = []; if (undo.length > 1000) undo.shift();
    apply(change, true); start = null; render();
  }
  function nearest(x, y) {
    let index = -1, best = 10 / pz.scale;
    walls.forEach(([ax, ay, bx, by], i) => {
      const dx = bx - ax, dy = by - ay;
      const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy || 1)));
      const dist = Math.hypot(x - ax - t * dx, y - ay - t * dy);
      if (dist <= best) { best = dist; index = i; }
    });
    return index;
  }
  function imagePoint(x, y) {
    return { x: Math.max(0, Math.min(state.width, x)), y: Math.max(0, Math.min(state.height, y)) };
  }
  function imageCoordinates(coords) {
    const a = imagePoint(coords[0], coords[1]), b = imagePoint(coords[2], coords[3]);
    return [a.x, a.y, b.x, b.y];
  }
  function snapped(x, y, exclude = null) {
    const point = imagePoint(x, y);
    let pt = point, best = 10 / pz.scale;
    if ($("snap-ends").checked) {
      for (const [i, w] of walls.entries()) for (const [end, a, b] of [[0, w[0], w[1]], [1, w[2], w[3]]]) {
        if (exclude?.has(`${i}:${end}`)) continue;  // never snap a dragged endpoint to itself
        const candidate = imagePoint(a, b);
        const dist = Math.hypot(point.x - candidate.x, point.y - candidate.y);
        if (dist <= best) { best = dist; pt = candidate; }
      }
    }
    return pt;
  }
  // Endpoints within 10 screen px; all joined ends move together unless detached.
  function endpointsNear(x, y, detach) {
    let best = 10 / pz.scale, hit = null;
    walls.forEach((w, i) => [0, 1].forEach((end) => {
      const dist = Math.hypot(x - w[end * 2], y - w[end * 2 + 1]);
      if (dist <= best) { best = dist; hit = { i, end, x: w[end * 2], y: w[end * 2 + 1] }; }
    }));
    if (!hit) return [];
    if (detach) return [[hit.i, hit.end]];
    const ends = [];
    walls.forEach((w, i) => {
      const d = [0, 1].map((end) => Math.hypot(w[end * 2] - hit.x, w[end * 2 + 1] - hit.y));
      const end = i === hit.i ? hit.end : d[0] <= d[1] ? 0 : 1;  // at most one end per wall
      if (d[end] <= JOIN) ends.push([i, end]);
    });
    return ends;
  }
  function onDragStart(x, y, event) {
    if (busy || dragging || editDialog.open || $("portal-dialog").open || !state) return null;
    // Left mouse/pen only: Ctrl-click edits, and one-finger touch keeps panning.
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.pointerType === "touch") return null;
    const ends = endpointsNear(x, y, event.altKey);
    if (!ends.length) return null;
    const before = structuredClone(walls), moving = new Set(ends.map(([i, end]) => `${i}:${end}`));
    const [i0, e0] = ends[0], origin = { x: walls[i0][e0 * 2], y: walls[i0][e0 * 2 + 1] };
    const place = (px, py) => {
      const pt = snapped(px, py, moving);
      for (const [i, end] of ends) { walls[i][end * 2] = pt.x; walls[i][end * 2 + 1] = pt.y; }
      return pt;
    };
    const handler = {
      move(px, py) {
        place(px, py); render();
        status(`Moving ${ends.length === 1 ? "an endpoint" : `${ends.length} joined endpoints`}; release to place, Escape cancels.`);
      },
      end(px, py) {
        const pt = place(px, py), after = structuredClone(walls), pending = start;
        dragging = null; walls = before;
        if (pt.x === origin.x && pt.y === origin.y) { render(); status("Endpoint not moved."); return; }
        if (ends.some(([i]) => after[i][0] === after[i][2] && after[i][1] === after[i][3])) {
          render(); status("The two endpoints of a wall must differ.", true); return;
        }
        mutate({ batch: true, before, after });
        start = pending; render();
        status(`Moved ${ends.length === 1 ? "an endpoint" : `${ends.length} joined endpoints`} in draft. Save applies the walls; Download does not.`);
      },
      cancel() {
        if (dragging !== handler) return;
        dragging = null; walls = before; render();
      },
    };
    dragging = handler;
    return handler;
  }
  vp.addEventListener("pointermove", (event) => {
    if (event.buttons || !state || dragging || event.pointerType === "touch") return;
    const pt = pz.toImage(event.clientX, event.clientY);
    vp.classList.toggle("endpoint-hover", !event.ctrlKey && endpointsNear(pt.x, pt.y, true).length > 0);
  });
  vp.addEventListener("pointerleave", () => vp.classList.remove("endpoint-hover"));
  function onTap(x, y, event) {
    if (busy || editDialog.open || $("portal-dialog").open || !state || !Number.isFinite(x) || !Number.isFinite(y)) return;
    // Secondary tap or Ctrl-primary tap edits from any tool; PanZoom filters drags.
    if (event?.button === 2 || (event?.button === 0 && event.ctrlKey)) {
      const index = nearest(x, y);
      if (index < 0) { status("Right-click or Ctrl+left-click within 10 screen pixels of a wall to edit it."); return; }
      openWallEdit(index);
      return;
    }
    const tool = $("wall-tool").value, kind = $("wall-kind").value;
    if (tool === "add") {
      const pt = snapped(x, y);
      if (!start) { start = pt; render(); status("Choose the end of the segment; Escape cancels."); return; }
      if (Math.hypot(pt.x - start.x, pt.y - start.y) < 0.001) { status("Choose a different endpoint.", true); return; }
      mutate({ index: walls.length, before: null, after: [start.x, start.y, pt.x, pt.y, kind, kind !== "ethereal"] });
    } else {
      const index = nearest(x, y);
      if (index < 0) { status("Click within 10 screen pixels of a wall."); return; }
      if (tool === "edit") { openWallEdit(index); return; }
      const before = walls[index].slice();
      if (before[4] === "portal" && before[6]?.pair) { status("Use Portal configuration to remove the pair before deleting or retyping an element.",true); return; }
      mutate({ index, before, after: tool === "remove" ? null : [...before.slice(0, 4), kind, kind !== "ethereal"] });
    }
    status("Draft changed. Save applies the walls; Download does not.");
  }
  function openWallEdit(index) {
    if (busy || editDialog.open || !walls[index]) return;
    const before = walls[index].slice();
    editing = { index, before };
    start = null;
    render();
    const coords = imageCoordinates(before);
    coordinateFields.forEach((input, i) => {
      input.value = String(coords[i]); input.min = "0";
      input.max = String(i % 2 === 0 ? state.width : state.height);
      input.removeAttribute("aria-invalid");
    });
    $("wall-edit-clamp-note").hidden = coords.every((value, i) => value === before[i]);
    $("wall-edit-kind").value = before[4];
    $("secret-after").value = before[6]?.after || "door";
    $("secret-after-label").hidden = before[4] !== "secret";
    $("wall-edit-title").textContent = `Edit wall ${index + 1}`;
    editError.textContent = ""; editError.hidden = true;
    editDialog.showModal();
    coordinateFields[0].focus();
    coordinateFields[0].select();
  }
  function editFailure(message, input) {
    editError.textContent = message; editError.hidden = false;
    if (input) { input.setAttribute("aria-invalid", "true"); input.focus(); }
  }
  editForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!editing || busy || !state) return;
    editError.hidden = true;
    coordinateFields.forEach(input => input.removeAttribute("aria-invalid"));
    const entered = coordinateFields.map(input => input.valueAsNumber);
    const invalid = entered.findIndex(value => !Number.isFinite(value));
    if (invalid >= 0) {
      editFailure("Enter all four coordinates as finite numbers.", coordinateFields[invalid]);
      return;
    }
    const coords = imageCoordinates(entered);
    coordinateFields.forEach((input, i) => { input.value = String(coords[i]); });
    if (coords.some((value, i) => value !== entered[i])) $("wall-edit-clamp-note").hidden = false;
    if (coords[0] === coords[2] && coords[1] === coords[3]) {
      editFailure("The two endpoints must differ after moving outside points to the image edge.", coordinateFields[2]);
      return;
    }
    const kind = $("wall-edit-kind").value;
    if (!kinds.has(kind)) { editFailure("Choose a supported wall type.", $("wall-edit-kind")); return; }
    const { index, before } = editing;
    if (!walls[index] || JSON.stringify(walls[index]) !== JSON.stringify(before)) {
      editFailure("The selected wall changed. Cancel and select it again.");
      return;
    }
    // Moving an imported wall must not silently enable a passive segment.
    const blocks = kind === "ethereal" ? false : kind === before[4] ? before[5] : true;
    if (before[4] === "portal" && before[6]?.pair && kind !== "portal") {
      editFailure("Remove the portal pair in Portal configuration before changing its type."); return;
    }
    const after = [...coords, kind, blocks];
    if (kind === before[4] && before[6]) after.push(structuredClone(before[6]));
    if (kind === "secret" && ($("secret-after").value !== "door" || before[6])) after[6] = {after: $("secret-after").value};
    if (JSON.stringify(after) === JSON.stringify(before)) {
      editDialog.close(); status("No changes made."); return;
    }
    mutate({ index, before, after });
    editDialog.close();
    status("Wall updated in draft. Save wall set applies it; Download does not.");
  });
  $("wall-edit-cancel").onclick = () => editDialog.close();
  editDialog.addEventListener("close", () => {
    if (!editDialog.open) { editing = null; vp.focus(); }
  });
  // Preserve native input undo and dialog Escape handling, not viewport shortcuts.
  editDialog.addEventListener("keydown", (event) => {
    event.stopPropagation();
    if (event.key !== "Tab") return;
    const first = coordinateFields[0], last = $("wall-edit-cancel");
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault(); first.focus();
    }
  });
  $("wall-edit-kind").addEventListener("change", () => { $("secret-after-label").hidden = $("wall-edit-kind").value !== "secret"; });
  function body() {
    LGPortalDraft.validate(walls);
    const ppg = Number($("pixels-per-grid").value);
    if (!Number.isFinite(ppg) || ppg <= 0 || ppg > 1e7) throw new Error("Enter a positive pixels-per-grid value (up to 10000000).");
    return { walls_version: state.walls_version, cache_token: state.cache_token, walls, pixels_per_grid: ppg };
  }
  async function load() {
    const next = await LGApi.get(url), artwork = new Image();
    artwork.src = `/api/maps/${id}/image?v=${encodeURIComponent(next.image_version)}`;
    await artwork.decode();
    state = next; walls = next.walls.map((w) => w.slice()); saved = snapshot(); start = null; undo = []; redo = [];
    img.src = artwork.src; pz.setContentSize(next.width, next.height); svg.setAttribute("viewBox", `0 0 ${next.width} ${next.height}`);
    pz.fit(); render(); $("wall-retry").hidden = true;
    status("Ready. Click two endpoints to add a wall, or drag an endpoint to move it (Alt detaches it from a corner).");
  }
  $("wall-save").onclick = () => run(async () => {
    const next = await LGApi.post(url, body());
    state = next; walls = next.walls.map((w) => w.slice()); saved = snapshot(); start = null; undo = []; redo = []; render();
    status(`Saved ${walls.length} walls and reusable UVTT source #${next.source_id}.`);
  });
  $("wall-download").onclick = () => run(async () => {
    const draft = { ...body(), width: state.width, height: state.height, image_version: state.image_version, include_image: $("include-image").checked };
    const response = await fetch(`${url}/export`, { method: "POST", credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": document.querySelector('meta[name="csrf-token"]').content }, body: JSON.stringify(draft) });
    if (!response.ok) { const error = await response.json().catch(() => null); throw new Error(error?.error || `Export failed (${response.status}).`); }
    const objectUrl = URL.createObjectURL(await response.blob()), link = document.createElement("a");
    link.href = objectUrl; link.download = `map-${id}-walls.uvtt`; document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60000); status("UVTT downloaded. Download does not save or apply your edits.");
  });
  $("wall-undo").onclick = () => { if (busy || dragging || !undo.length) return; const c = undo.pop(); apply(c, false); redo.push(c); start = null; render(); };
  $("wall-redo").onclick = () => { if (busy || dragging || !redo.length) return; const c = redo.pop(); apply(c, true); undo.push(c); start = null; render(); };
  $("wall-tool").onchange = $("wall-kind").onchange = () => { start = null; render(); };
  $("wall-reload").onclick = () => { if (dirty() && !confirm("Discard unsaved wall edits and reload? Download first to keep a copy.")) return; run(load); };
  $("wall-retry").onclick = () => run(load);
  $("wall-zoom-in").onclick = () => pz.zoomCenter(1.25); $("wall-zoom-out").onclick = () => pz.zoomCenter(0.8); $("wall-fit").onclick = () => pz.fit();
  window.addEventListener("beforeunload", (e) => { if (dirty()) { e.preventDefault(); e.returnValue = ""; } });
  window.addEventListener("keydown", (e) => {
    if (editDialog.open || $("portal-dialog").open || /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) return;
    if (dragging) {
      if (e.key === "Escape" && pz.cancelDrag()) status("Endpoint move cancelled.");
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") e.preventDefault();
      return;
    }
    if (e.key === "Escape") { start = null; render(); }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") { e.preventDefault(); $(e.shiftKey ? "wall-redo" : "wall-undo").click(); }
    if (e.key.toLowerCase() === "f") pz.fit();
  });
  LGPortalEditor({getWalls:()=>walls, getBusy:()=>busy, mutate, render, status, viewport:vp});
  run(async () => { try { await load(); } catch (e) { $("wall-retry").hidden = false; throw e; } });
})();
