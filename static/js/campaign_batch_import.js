/* Batch import: one progress line, automatic Apply, explicit per-map mapping. */
(function () {
  "use strict";
  const panel = document.getElementById("campaign-batch-import");
  if (!panel) return;
  const api = window.LGApi, cid = panel.dataset.campaignId;
  const sourceUrl = `/api/campaigns/${cid}/wall-sources`;
  const rows = document.getElementById("batch-assignment-rows");
  const status = document.getElementById("batch-status");
  const imagesInput = document.getElementById("batch-map-files");
  const wallsInput = document.getElementById("batch-wall-files");
  const apply = document.getElementById("batch-apply-walls");
  const oldLog = document.getElementById("batch-import-results");
  if (oldLog) oldLog.remove();
  const names = new Intl.Collator(undefined, {numeric:true, sensitivity:"base"});
  let sources = [], busy = false, timer = null;
  const maps = new Map();
  function message(text, temporary = false) {
    clearTimeout(timer); status.textContent = text;
    if (temporary) timer = setTimeout(() => {status.textContent = "";}, 4000);
  }
  function placeholder(select, text) {select.replaceChildren(new Option(text, ""));}
  function choice(row) {
    return row.source.value === row.loaded && row.scene.value !== "" ?
      row.scenes.find(s => String(s.index) === row.scene.value) : null;
  }
  function controls() {
    panel.setAttribute("aria-busy", String(busy));
    for (const el of panel.querySelectorAll("button,input,select")) el.disabled = busy;
    for (const row of maps.values()) {
      row.source.disabled = busy || !sources.length;
      row.scene.disabled = busy || !row.scenes.length || row.loaded !== row.source.value;
    }
    apply.disabled = busy || ![...maps.values()].some(choice);
  }
  async function run(fn) {
    if (busy) return;
    busy = true; clearTimeout(timer); controls();
    try {await fn();} catch (error) {message(error.message || String(error), true);}
    finally {busy = false; controls();}
  }
  function clear(row) {
    row.scenes = []; row.loaded = ""; placeholder(row.scene, "Choose a wall set"); row.result.textContent = "";
  }
  function populate(row) {
    const previous = row.source.value;
    placeholder(row.source, "Choose a saved source");
    for (const s of sources) row.source.add(new Option(`${s.filename} (${s.scene_count} wall sets) [#${s.id}]`, String(s.id)));
    if (sources.some(s => String(s.id) === previous)) row.source.value = previous;
    else clear(row);
  }
  async function refresh() {
    const data = await api.get(sourceUrl);
    sources = [...data.sources].sort((a,b) => names.compare(a.filename,b.filename) || a.id-b.id);
    for (const row of maps.values()) populate(row);
  }
  async function inspect(row) {
    clear(row); const id = row.source.value; if (!id) return;
    row.result.textContent = "Loading wall sets...";
    try {
      const data = await api.get(`/api/maps/${row.id}/wall-sources/${id}`);
      if (row.source.value !== id) return;
      row.scenes = [...data.scenes].sort((a,b) => names.compare(a.name,b.name) || a.index-b.index);
      row.loaded = id;
      for (const s of row.scenes) row.scene.add(new Option(`${s.name} — ${s.walls} walls [${s.index+1}]`, String(s.index)));
      row.result.textContent = row.scenes.length ? "Choose a wall set." : "No wall sets found.";
    } catch(error) {row.result.textContent = error.message; throw error;}
  }
  function addMap(map) {
    if (maps.has(Number(map.id))) return;
    const row = {id:Number(map.id), name:map.name, scenes:[], loaded:"",
      source:document.createElement("select"), scene:document.createElement("select"),
      align:document.createElement("input"), result:document.createElement("span")};
    row.align.type = "checkbox"; row.align.checked = true;
    row.source.setAttribute("aria-label", `Wall source for ${map.name}`);
    row.scene.setAttribute("aria-label", `Wall set for ${map.name}`);
    row.align.setAttribute("aria-label", `Auto-align ${map.name}`);
    const link = document.createElement("a"); link.href = `/maps/${row.id}`; link.textContent = `${map.name} [#${row.id}]`;
    const tr = document.createElement("tr"); tr.dataset.mapId = row.id;
    for (const el of [link,row.source,row.scene,row.align,row.result]) {
      const td = document.createElement("td"); td.append(el); tr.append(td);
    }
    clear(row); populate(row); rows.append(tr); maps.set(row.id,row);
    row.source.addEventListener("change", () => run(() => inspect(row)));
    row.scene.addEventListener("change", () => {row.result.textContent = choice(row) ? "Selected; not applied yet." : ""; controls();});
    controls();
  }
  async function uploadImage(file) {
    const form = new FormData(); form.append("image",file);
    const token = document.querySelector('meta[name="csrf-token"]').content; form.append("csrf_token",token);
    let response;
    try {response = await fetch(`/campaigns/${cid}/maps`, {method:"POST", body:form,
      credentials:"same-origin", redirect:"follow", headers:{"X-CSRF-Token":token}});}
    catch (_) {throw new Error("Upload result unknown; check the campaign before retrying to avoid duplicates.");}
    const url = new URL(response.url,location.href), id = url.pathname.match(/^\/maps\/(\d+)\/?$/);
    if (response.redirected && id && url.origin === location.origin) return {
      id:Number(id[1]), name:file.name.replace(/\.[^.]+$/,"") || "Battle map", warning:!response.ok};
    throw new Error(url.searchParams.get("err") || `Upload failed (HTTP ${response.status}); check the campaign before retrying.`);
  }
  document.getElementById("batch-upload").addEventListener("submit", event => {
    event.preventDefault(); const images = [...imagesInput.files], walls = [...wallsInput.files];
    if (!images.length && !walls.length) {message("Choose map images, wall files, or both.",true); return;}
    run(async () => {
      let imageOk=0, wallOk=0, failed=0, warnings=0, number=0;
      const total=images.length+walls.length;
      for (const file of walls) {
        message(`Importing ${++number}/${total}: ${file.name}`);
        try {const form=new FormData();form.append("file",file);await api.post(sourceUrl,form);wallOk++;}
        catch (_) {failed++;}
      }
      for (const file of images) {
        message(`Importing ${++number}/${total}: ${file.name}`);
        try {const map=await uploadImage(file);addMap(map);imageOk++;if(map.warning)warnings++;}
        catch (_) {failed++;}
      }
      imagesInput.value="";wallsInput.value="";
      let refreshFailed=false;
      try {await refresh();} catch (_) {refreshFailed=true;}
      message(`Import complete: ${imageOk} maps, ${wallOk} wall sources imported; ${failed} failed, ${warnings} editor warnings.` +
        (refreshFailed ? " Source refresh failed; use Refresh saved wall sources." : "") +
        (failed ? " Check the campaign before retrying failed files." : ""),true);
    });
  });
  document.getElementById("batch-refresh-sources").addEventListener("click",()=>run(async()=>{
    await refresh();message("Saved wall sources refreshed.",true);
  }));
  apply.addEventListener("click",()=>{
    const pending=[...maps.values()].filter(choice).map(row=>({row,item:choice(row),source:Number(row.source.value),align:row.align.checked}));
    if (!pending.length || busy) return;
    run(async()=>{
      let ok=0,failed=0;
      for(const p of pending){
        p.row.result.textContent="Applying...";
        try{
          const data=await api.post(`/api/maps/${p.row.id}/walls/from-source`,{
            source_id:p.source,scene_index:p.item.index,use_scene_calibration:p.align,use_pack_image:false});
          p.row.result.textContent=`Applied ${data.imported} walls from ${data.scene}.`;p.row.scene.value="";ok++;
        }catch(error){p.row.result.textContent=error.message;failed++;}
      }
      message(`Wall assignments complete: ${ok} applied, ${failed} failed.`,true);
    });
  });
  window.addEventListener("beforeunload",event=>{if(busy){event.preventDefault();event.returnValue="";}});
  run(async()=>{
    for(const map of JSON.parse(document.getElementById("batch-existing-maps").textContent))addMap(map);
    await refresh();message("");
  });
})();
