/* DM-only controls. Ordinary fog clicks never break an illusion. */
(function () {
  "use strict";
  window.LGDoubleReveal = function ({mapId, run, reload}) {
    const $ = id => document.getElementById(id), base = `/api/maps/${mapId}/double-reveal`;
    let data = null, selected = null, generation = 0, pending = false, lastVersion = "";
    const stamp = () => ({cache_token:data.cache_token,walls_version:data.walls_version,
      fog_version:data.fog_version,image_revision:data.image_revision});
    const selectMode = $("double-select"), mask = $("double-room-mask");
    function show(result, point) {
      data = result;
      if (point) selected = result.selected;
      else if (selected) selected = data.rooms.find(r=>r.area_key===selected.area_key) || {...selected,revision:0,true_active:0,destination_map_id:null};
      const title = selected ? (selected.name || `Room at ${Math.round(selected.x)}, ${Math.round(selected.y)}`) : "Select a room on the map.";
      $("double-status").textContent = `${data.image_revision ? "Alternate image ready." : "Upload an alternate image first."} ${title}` +
        (selected ? ` — ${selected.revision ? (selected.true_active ? "True appearance" : "Initial appearance") : "Not configured"}; ${selected.revealed ? "visible" : "hidden by fog"}.` : "");
      $("double-room-form").hidden = !selected;
      $("double-enabled").checked = !!selected?.revision;
      $("double-destination").replaceChildren(new Option("No destination", ""), ...data.maps.map(m=>new Option(m.name,String(m.id))));
      $("double-destination").value = selected?.destination_map_id ? String(selected.destination_map_id) : "";
      $("double-true").disabled = !selected?.revision || !!selected?.true_active || !selected?.valid_geometry;
      $("double-initial").disabled = !selected?.revision || !selected?.true_active || !selected?.valid_geometry;
      $("double-travel").disabled = !selected?.revision || !selected?.true_active || !selected?.revealed || !selected?.destination_map_id || data.active_map_id!==mapId || !selected?.valid_geometry;
      $("double-undo").disabled = !data.can_undo;
      $("double-room-list").replaceChildren();
      for (const r of data.rooms) {
        const row = document.createElement("div"), button = document.createElement("button");
        button.type="button";
        button.textContent = `${r.name || `Room ${Math.round(r.x)}, ${Math.round(r.y)}`}: ${r.true_active ? "true" : "initial"}${r.valid_geometry ? "" : " — geometry changed (inactive)"}`;
        button.onclick=()=>run(()=>select(r.x,r.y)); button.disabled=!r.valid_geometry;
        row.append(button);
        if (!r.valid_geometry) {
          const remove=document.createElement("button");remove.type="button";remove.textContent="Remove stale configuration";
          remove.onclick=()=>{if(confirm("Remove this stale room configuration and its appearance history?")) mutate(()=>LGApi.del(`${base}/rooms/${r.area_key}`,stamp()));};
          row.append(remove);
        }
        $("double-room-list").append(row);
      }
      if (selected && selected.valid_geometry && selectMode.checked) {
        mask.src=`${base}/room-mask?x=${selected.x}&y=${selected.y}&v=${data.walls_version}`;mask.hidden=false;
      } else mask.hidden=true;
    }
    async function refresh(point=null) {
      const gen=++generation;
      const result=await LGApi.get(point ? `${base}/room?x=${point.x}&y=${point.y}` : base);
      if(gen===generation) show(result,point);
    }
    async function select(x,y) {await refresh({x,y});}
    function mutate(fn) {
      return run(async()=>{
        if(!data)return;
        ++generation;pending=true;
        try {show(await fn());await reload();}
        catch(error) {await refresh().catch(()=>{});throw error;}
        finally {pending=false;}
      });
    }
    $("double-image-form").onsubmit=event=>{
      event.preventDefault();
      if(data?.image_revision && !confirm("Replace the alternate image? Rooms already using true appearance will immediately use the replacement artwork."))return;
      mutate(async()=>{
        const file=$("double-image-file").files[0];if(!file)throw Error("Choose an image first.");
        const body=new FormData();body.append("file",file);
        Object.entries(stamp()).forEach(([k,v])=>body.append(k,String(v)));
        const result=await LGApi.post(`${base}/image`,body);$("double-image-file").value="";return result;
      });
    };
    $("double-save").onclick=()=>{
      if(!selected)return;
      const enabled=$("double-enabled").checked;
      if(!enabled && selected.revision && !confirm("Disable double reveal for this room? It will return to its initial artwork and its appearance history will be removed."))return;
      mutate(()=>LGApi.post(`${base}/room`,{...stamp(),x:selected.x,y:selected.y,revision:selected.revision,
        enabled,destination_map_id:Number($("double-destination").value)||null}));
    };
    function appearance(active) {
      if(!selected)return;
      mutate(()=>LGApi.post(`${base}/appearance`,{...stamp(),area_key:selected.area_key,revision:selected.revision,true_active:active}));
    }
    $("double-true").onclick=()=>appearance(true);
    $("double-initial").onclick=()=>appearance(false);
    $("double-undo").onclick=()=>mutate(()=>LGApi.post(`${base}/undo`,stamp()));
    $("double-refresh").onclick=()=>run(()=>refresh());
    $("double-travel").onclick=()=>{
      if(!selected?.destination_map_id || !confirm(`Show ${data.maps.find(m=>m.id===selected.destination_map_id)?.name || "destination map"} to players? Its current fog and appearance states will be preserved.`))return;
      run(async()=>{
        const result=await LGApi.post(`${base}/travel`,{...stamp(),area_key:selected.area_key,revision:selected.revision,expected_active_map_id:data.active_map_id});
        location.href=result.editor_url;
      });
    };
    selectMode.onchange=()=>{
      if(selectMode.checked) $("room-select-mode").checked=false;
      if(data)show(data); else run(()=>refresh());
    };
    $("room-select-mode").addEventListener("change",()=>{if($("room-select-mode").checked){selectMode.checked=false;mask.hidden=true;}});
    mask.onerror=()=>{mask.hidden=true;};
    return {
      selecting:()=>selectMode.checked,
      select,
      refresh: state=>{
        const version=`${state.cache_token}-${state.walls_version}-${state.fog_version}-${Number(state.is_active)}`;
        if(pending || version===lastVersion)return;
        if(data && data.walls_version!==state.walls_version){selected=null;mask.hidden=true;}
        lastVersion=version;
        refresh().catch(error=>{lastVersion="";$("double-status").textContent=error.message;});
      }
    };
  };
})();
