/* Campaign-scoped source library. Uploaded names are always text, not HTML. */
(function () {
  "use strict";
  const panel = document.getElementById("saved-wall-library");
  if (!panel || !window.LG_MAP) return;
  const api = window.LGApi;
  const mapUrl = `/api/maps/${window.LG_MAP.id}`;
  const sourcesUrl = `/api/campaigns/${window.LG_MAP.campaign_id}/wall-sources`;
  const source = document.getElementById("saved-source");
  const scene = document.getElementById("saved-scene");
  const info = document.getElementById("saved-scene-info");
  const status = document.getElementById("source-status");
  const apply = document.getElementById("source-apply");
  const remove = document.getElementById("source-delete");
  const file = document.getElementById("source-file");
  let sources = [], scenes = [], busy = false;

  function placeholder(select, label) { select.replaceChildren(new Option(label, "")); }
  function clearScenes() {
    scenes = [];
    placeholder(scene, "Choose a wall set");
    info.textContent = "";
  }
  function controls() {
    for (const el of panel.querySelectorAll("button, input, select")) el.disabled = busy;
    source.disabled = busy || !sources.length;
    scene.disabled = busy || !scenes.length;
    apply.disabled = busy || !source.value || scene.value === "";
    remove.disabled = busy || !source.value;
  }
  async function run(task) {
    if (busy) return;
    busy = true; controls(); status.textContent = "Working...";
    try { await task(); }
    catch (error) { status.textContent = error.message || String(error); }
    finally { busy = false; controls(); }
  }
  async function refresh(selected = "") {
    clearScenes(); sources = []; placeholder(source, "Choose a saved source");
    const data = await api.get(sourcesUrl);
    sources = data.sources;
    for (const item of sources) {
      source.add(new Option(`${item.filename} (${item.scene_count} wall sets) [#${item.id}]`, String(item.id)));
    }
    if (sources.some(item => String(item.id) === String(selected))) {
      source.value = String(selected); await inspect();
    }
    status.textContent = sources.length ? "Choose a source and wall set." : "No saved sources yet.";
  }
  async function inspect() {
    clearScenes();
    if (!source.value) { status.textContent = "Choose a saved source."; return; }
    const data = await api.get(`${mapUrl}/wall-sources/${source.value}`);
    scenes = data.scenes;
    for (const item of scenes) {
      scene.add(new Option(`${item.name} — ${item.walls} walls, ${item.doors} doors [${item.index + 1}]`, String(item.index)));
    }
    status.textContent = "Choose the wall set to apply. No walls have been changed.";
  }
  source.addEventListener("change", () => run(inspect));
  scene.addEventListener("change", () => {
    const item = scenes.find(s => String(s.index) === scene.value);
    info.textContent = item ? `${item.scene_width || "?"} × ${item.scene_height || "?"} source pixels; ` +
      `suggested offset ${item.calibration.offset_x}, ${item.calibration.offset_y}; ` +
      `scale ${item.calibration.scale_x.toFixed(4)}, ${item.calibration.scale_y.toFixed(4)}` : "";
    controls();
  });
  document.getElementById("source-save").addEventListener("submit", event => {
    event.preventDefault(); if (!file.files.length) return;
    run(async () => {
      const form = new FormData(); form.append("file", file.files[0]);
      const data = await api.post(sourcesUrl, form);
      file.value = ""; await refresh(data.source.id);
      status.textContent = "Source saved. Choose a wall set, then apply it to this map.";
    });
  });
  document.getElementById("source-refresh").addEventListener("click", () => run(() => refresh()));
  apply.addEventListener("click", () => {
    const item = scenes.find(s => String(s.index) === scene.value);
    if (!item || !source.value) return;
    if (!window.confirm(`Replace this map's walls with "${item.name}"? Existing fog actions will be replayed against the new walls; blank the player screen first if necessary.`)) return;
    const body = {source_id: Number(source.value), scene_index: item.index,
      use_scene_calibration: document.getElementById("saved-auto-align").checked};
    run(async () => {
      await api.post(`${mapUrl}/walls/from-source`, body); window.location.reload();
    });
  });
  remove.addEventListener("click", () => {
    const item = sources.find(s => String(s.id) === source.value);
    if (!item || !window.confirm(`Delete saved source "${item.filename}"? Walls already applied to maps will remain.`)) return;
    run(async () => { await api.del(`${sourcesUrl}/${item.id}`); await refresh(); });
  });
  clearScenes(); run(() => refresh());
})();
