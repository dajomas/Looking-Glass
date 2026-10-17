/* Campaign uploads and explicit per-map wall assignment; existing endpoints only. */
(function () {
  "use strict";
  const panel = document.getElementById("campaign-batch-import");
  if (!panel) return;
  const api = window.LGApi;
  const cid = panel.dataset.campaignId;
  const sourceUrl = `/api/campaigns/${cid}/wall-sources`;
  const rows = document.getElementById("batch-assignment-rows");
  const status = document.getElementById("batch-status");
  const results = document.getElementById("batch-import-results");
  const mapFiles = document.getElementById("batch-map-files");
  const wallFiles = document.getElementById("batch-wall-files");
  const applyButton = document.getElementById("batch-apply-walls");
  const names = new Intl.Collator(undefined, {numeric: true, sensitivity: "base"});
  const assignments = new Map();
  let sources = [], busy = false;

  function placeholder(select, label) { select.replaceChildren(new Option(label, "")); }
  function selected(row) {
    if (row.inspectedSource !== row.source.value || row.scene.value === "") return null;
    return row.scenes.find(item => String(item.index) === row.scene.value) || null;
  }
  function controls() {
    panel.setAttribute("aria-busy", String(busy));
    for (const element of panel.querySelectorAll("input, select, button")) element.disabled = busy;
    for (const row of assignments.values()) {
      row.source.disabled = busy || !sources.length;
      row.scene.disabled = busy || !row.scenes.length || row.inspectedSource !== row.source.value;
    }
    applyButton.disabled = busy || ![...assignments.values()].some(selected);
  }
  async function run(task) {
    if (busy) return;
    busy = true; controls();
    try { await task(); }
    catch (error) { status.textContent = error.message || String(error); }
    finally { busy = false; controls(); }
  }
  function clearScene(row) {
    row.scenes = []; row.inspectedSource = "";
    placeholder(row.scene, "Choose a wall set");
    row.result.textContent = "";
  }
  function populateSources(row) {
    const previous = row.source.value;
    placeholder(row.source, "Choose a saved source");
    for (const item of sources) {
      row.source.add(new Option(`${item.filename} (${item.scene_count} wall sets) [#${item.id}]`, String(item.id)));
    }
    if (sources.some(item => String(item.id) === previous)) row.source.value = previous;
    else clearScene(row);
  }
  async function refreshSources() {
    const data = await api.get(sourceUrl);
    sources = [...data.sources].sort((a, b) => names.compare(a.filename, b.filename) || a.id - b.id);
    for (const row of assignments.values()) populateSources(row);
  }
  async function inspect(row) {
    clearScene(row);
    const sourceId = row.source.value;
    if (!sourceId) return;
    row.result.textContent = "Loading wall sets...";
    try {
      const data = await api.get(`/api/maps/${row.id}/wall-sources/${sourceId}`);
      if (row.source.value !== sourceId) return;
      row.scenes = [...data.scenes].sort((a, b) => names.compare(a.name, b.name) || a.index - b.index);
      row.inspectedSource = sourceId;
      for (const item of row.scenes) {
        row.scene.add(new Option(`${item.name} — ${item.walls} walls [${item.index + 1}]`, String(item.index)));
      }
      row.result.textContent = row.scenes.length ? "Choose a wall set; not applied yet." : "No wall sets found.";
    } catch (error) {
      row.result.textContent = error.message;
      throw error;
    }
  }
  function addMap(map) {
    if (assignments.has(Number(map.id))) return;
    const tr = document.createElement("tr"); tr.dataset.mapId = map.id;
    const row = {id: Number(map.id), name: map.name, source: document.createElement("select"),
      scene: document.createElement("select"), align: document.createElement("input"),
      result: document.createElement("span"), scenes: [], inspectedSource: ""};
    const link = document.createElement("a"); link.href = `/maps/${row.id}`; link.textContent = `${row.name} [#${row.id}]`;
    row.source.setAttribute("aria-label", `Wall source for ${row.name}`);
    row.scene.setAttribute("aria-label", `Wall set for ${row.name}`);
    row.align.type = "checkbox"; row.align.checked = true;
    row.align.setAttribute("aria-label", `Auto-align ${row.name}`);
    for (const element of [link, row.source, row.scene, row.align, row.result]) {
      const td = document.createElement("td"); td.append(element); tr.append(td);
    }
    clearScene(row); populateSources(row); rows.append(tr); assignments.set(row.id, row);
    row.source.addEventListener("change", () => run(() => inspect(row)));
    row.scene.addEventListener("change", () => {row.result.textContent = selected(row) ? "Selected; not applied yet." : ""; controls();});
    controls();
  }
  function log(filename, message) {
    const li = document.createElement("li"); li.textContent = `${filename}: ${message}`; results.append(li);
  }
  async function uploadMap(file) {
    const form = new FormData(); form.append("image", file);
    const token = document.querySelector('meta[name="csrf-token"]').content;
    form.append("csrf_token", token);
    let response;
    try {
      response = await fetch(`/campaigns/${cid}/maps`, {method: "POST", body: form,
        credentials: "same-origin", headers: {"X-CSRF-Token": token}, redirect: "follow"});
    } catch (_) {
      throw new Error("Upload result unknown after connection failure. Check the campaign before retrying to avoid duplicates.");
    }
    const url = new URL(response.url, window.location.href);
    const match = url.pathname.match(/^\/maps\/(\d+)\/?$/);
    if (response.redirected && match && url.origin === window.location.origin) {
      // The server created the map before redirecting; do not re-upload if its editor then fails.
      return {id: Number(match[1]), name: file.name.replace(/\.[^.]+$/, "") || "Battle map",
        warning: response.ok ? "" : `Map created, but editor returned HTTP ${response.status}; check the server log.`};
    }
    if (url.pathname === "/login") throw new Error("Session expired. Sign in and reload before retrying.");
    throw new Error(url.searchParams.get("err") || `Map import failed (HTTP ${response.status}); check the campaign before retrying.`);
  }
  document.getElementById("batch-upload").addEventListener("submit", event => {
    event.preventDefault();
    const images = [...mapFiles.files], walls = [...wallFiles.files];
    if (!images.length && !walls.length) {status.textContent = "Choose map images, wall files, or both."; return;}
    run(async () => {
      let succeeded = 0, failed = 0;
      for (const file of walls) {
        status.textContent = `Saving wall source: ${file.name}`;
        try {
          const form = new FormData(); form.append("file", file);
          const data = await api.post(sourceUrl, form);
          log(file.name, `saved wall source #${data.source.id}`); succeeded++;
        } catch (error) {log(file.name, error.message); failed++;}
      }
      for (const file of images) {
        status.textContent = `Importing map: ${file.name}`;
        try {
          const map = await uploadMap(file); addMap(map);
          log(file.name, `created map #${map.id}${map.warning ? "; " + map.warning : ""}`); succeeded++;
        } catch (error) {log(file.name, error.message); failed++;}
      }
      mapFiles.value = ""; wallFiles.value = "";
      const summary = `Import complete: ${succeeded} succeeded, ${failed} failed. Choose wall assignments below. Reselect only failed files to retry.`;
      try {await refreshSources(); status.textContent = summary;}
      catch (error) {status.textContent = `${summary} Source list refresh failed: ${error.message}. Use Refresh saved wall sources.`;}
    });
  });
  document.getElementById("batch-refresh-sources").addEventListener("click", () => run(async () => {
    await refreshSources(); status.textContent = "Saved wall sources refreshed. Newly imported maps are available below; reload the page to discover maps added in another tab.";
  }));
  applyButton.addEventListener("click", () => {
    const pending = [...assignments.values()].filter(selected).map(row => ({row, item: selected(row),
      sourceId: Number(row.source.value), autoAlign: row.align.checked}));
    if (!pending.length || busy) return;
    const list = pending.map(p => `${p.row.name} → ${p.item.name}`).join("\n");
    if (!window.confirm(`Replace walls for these maps?\n${list}\n\nExisting reveals are retained and recalculated. Blank the viewer first. Map artwork is kept.`)) return;
    run(async () => {
      let succeeded = 0, failed = 0;
      for (const {row, item, sourceId, autoAlign} of pending) {
        row.result.textContent = "Applying...";
        try {
          const data = await api.post(`/api/maps/${row.id}/walls/from-source`, {
            source_id: sourceId, scene_index: item.index, use_scene_calibration: autoAlign, use_pack_image: false});
          row.result.textContent = `Applied ${data.imported} walls from ${data.scene}.`;
          row.scene.value = ""; succeeded++;
        } catch (error) {row.result.textContent = error.message; failed++;}
      }
      status.textContent = `Wall assignments complete: ${succeeded} applied, ${failed} failed. Successful assignments are deselected; failed choices remain for retry.`;
    });
  });
  window.addEventListener("beforeunload", event => {if (busy) {event.preventDefault(); event.returnValue = "";}});
  run(async () => {
    for (const map of JSON.parse(document.getElementById("batch-existing-maps").textContent)) addMap(map);
    await refreshSources();
    status.textContent = "Ready. Import files or assign saved wall sets to campaign maps.";
  });
})();
