// Separate wall editor. Draft coordinates are image pixels, never viewport pixels.
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const id = window.LG_MAP.id, url = `/api/maps/${id}/wall-editor`;
  const vp = $("wall-viewport"), stage = $("wall-stage"), svg = $("wall-overlay"), img = $("wall-image");
  const kinds = new Set(["wall", "door", "secret", "window", "invisible", "ethereal"]);
  let state = null, walls = [], saved = "[]", start = null, undo = [], redo = [], busy = false;
  let wallWidth = 2;
  const pz = new PanZoom(vp, stage, { onTap, onChange: render });
  LGWallAppearance(id, (width) => {
    wallWidth = width;
    svg.style.setProperty("--wall-width", String(width));
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
    const paths = new Map();
    for (const [x1, y1, x2, y2, rawKind] of walls) {
      const kind = kinds.has(rawKind) ? rawKind : "wall";
      if (!paths.has(kind)) paths.set(kind, []);
      paths.get(kind).push(`M${x1} ${y1}L${x2} ${y2}`);
    }
    svg.replaceChildren();
    for (const [kind, lines] of paths) {
      const path = document.createElementNS(svg.namespaceURI, "path");
      path.setAttribute("class", `w-${kind}`); path.setAttribute("d", lines.join(""));
      path.style.strokeWidth = `${wallWidth}px`;
      svg.appendChild(path);
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
    walls.splice(change.index, before ? 1 : 0, ...(after ? [after.slice()] : []));
  }
  function mutate(change) {
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
  function snapped(x, y) {
    let pt = { x, y }, best = 10 / pz.scale;
    if ($("snap-ends").checked) {
      for (const w of walls) for (const [a, b] of [[w[0], w[1]], [w[2], w[3]]]) {
        const dist = Math.hypot(x - a, y - b);
        if (dist <= best) { best = dist; pt = { x: a, y: b }; }
      }
    }
    return pt;
  }
  function onTap(x, y) {
    if (busy || !state || x < 0 || y < 0 || x > state.width || y > state.height) return;
    const tool = $("wall-tool").value, kind = $("wall-kind").value;
    if (tool === "add") {
      const pt = snapped(x, y);
      if (!start) { start = pt; render(); status("Choose the end of the segment; Escape cancels."); return; }
      if (Math.hypot(pt.x - start.x, pt.y - start.y) < 0.001) { status("Choose a different endpoint.", true); return; }
      mutate({ index: walls.length, before: null, after: [start.x, start.y, pt.x, pt.y, kind, kind !== "ethereal"] });
    } else {
      const index = nearest(x, y);
      if (index < 0) { status("Click within 10 screen pixels of a wall."); return; }
      const before = walls[index].slice();
      mutate({ index, before, after: tool === "remove" ? null : [...before.slice(0, 4), kind, kind !== "ethereal"] });
    }
    status("Draft changed. Save applies the walls; Download does not.");
  }
  function body() {
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
    pz.fit(); render(); $("wall-retry").hidden = true; status("Ready. Click two endpoints to add a wall.");
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
  $("wall-undo").onclick = () => { if (busy || !undo.length) return; const c = undo.pop(); apply(c, false); redo.push(c); start = null; render(); };
  $("wall-redo").onclick = () => { if (busy || !redo.length) return; const c = redo.pop(); apply(c, true); undo.push(c); start = null; render(); };
  $("wall-tool").onchange = $("wall-kind").onchange = () => { start = null; render(); };
  $("wall-reload").onclick = () => { if (dirty() && !confirm("Discard unsaved wall edits and reload? Download first to keep a copy.")) return; run(load); };
  $("wall-retry").onclick = () => run(load);
  $("wall-zoom-in").onclick = () => pz.zoomCenter(1.25); $("wall-zoom-out").onclick = () => pz.zoomCenter(0.8); $("wall-fit").onclick = () => pz.fit();
  window.addEventListener("beforeunload", (e) => { if (dirty()) { e.preventDefault(); e.returnValue = ""; } });
  window.addEventListener("keydown", (e) => {
    if (/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) return;
    if (e.key === "Escape") { start = null; render(); }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") { e.preventDefault(); $(e.shiftKey ? "wall-redo" : "wall-undo").click(); }
    if (e.key.toLowerCase() === "f") pz.fit();
  });
  run(async () => { try { await load(); } catch (e) { $("wall-retry").hidden = false; throw e; } });
})();
