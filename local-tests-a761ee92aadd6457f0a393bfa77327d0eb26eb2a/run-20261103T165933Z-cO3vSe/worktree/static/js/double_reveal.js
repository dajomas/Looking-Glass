/* DM-only controls. Plain fog clicks never break an illusion; Ctrl-primary is explicit. */
(function () {
  "use strict";
  window.LGDoubleReveal = function ({mapId, run, reload, fogMode=()=>true, scale=()=>1}) {
    const $ = id => document.getElementById(id), base = `/api/maps/${mapId}/double-reveal`;
    let data = null, selected = null, generation = 0, pending = false, lastVersion = "";
    const stamp = () => ({cache_token:data.cache_token,walls_version:data.walls_version,
      fog_version:data.fog_version,image_revision:data.image_revision});
    const selectMode = $("double-select"), mask = $("double-room-mask");
    const markers = window.LGDoubleRevealMarkers
      ? new window.LGDoubleRevealMarkers($("double-fog-markers"), $("double-fog-legend")) : null;
    let quickUntil=0;
    function redraw() { markers?.draw(data, !selectMode.checked && fogMode(), scale()); }
    function leaveSelection() { selectMode.checked=false; mask.hidden=true; redraw(); }
    $("double-done").onclick=()=>{
      leaveSelection();
      const roomMode=$("room-select-mode");
      if(roomMode.checked) {roomMode.checked=false;roomMode.dispatchEvent(new Event("change",{bubbles:true}));}
      $("double-reveal-panel").open=false;$("fog-panel").open=true;
      document.querySelector('input[name="mode"]:checked')?.focus();
      redraw();
    };
    $("double-reveal-panel").addEventListener("toggle",()=>{if(!$("double-reveal-panel").open)leaveSelection();});
    document.querySelectorAll('input[name="mode"]').forEach(input=>input.addEventListener("change",leaveSelection));
    // Called inside the editor's run() lock; never nest run()/mutate() here.
    async function quickAction(x,y) {
      if(selectMode.checked || !fogMode() || pending || Date.now()<quickUntil)return;
      if(!data)throw Error("Room markers are loading. Try again shortly.");
      const before=data;
      ++generation;pending=true;
      try {
        const fresh=await LGApi.get(`${base}/room?x=${x}&y=${y}`), room=fresh.selected;
        const known=before.rooms.find(r=>r.area_key===room?.area_key);
        show(fresh);
        if(!room?.revision || !room.valid_geometry)throw Error("No valid Double Reveal room here.");
        if(!known || known.revision!==room.revision || known.destination_map_id!==room.destination_map_id ||
            !!known.true_active!==!!room.true_active || before.cache_token!==fresh.cache_token ||
            before.walls_version!==fresh.walls_version || before.fog_version!==fresh.fog_version ||
            before.image_revision!==fresh.image_revision || before.active_map_id!==fresh.active_map_id)
          throw Error("Room state changed. Markers refreshed; Ctrl-click again.");
        const body={...stamp(),area_key:room.area_key,revision:room.revision};
        if(!room.true_active) {
          show(await LGApi.post(`${base}/appearance`,{...body,true_active:true}));
          // A rapid Ctrl double-click must not reveal and then travel accidentally.
          quickUntil=Date.now()+600;
          await reload();
          return;
        }
        if(!room.destination_map_id)throw Error("True appearance is already revealed; no destination is assigned.");
        if(!room.revealed)throw Error("Reveal the room's fog before using its destination.");
        if(fresh.active_map_id!==mapId)throw Error("Show this source map to players before using its destination.");
        const name=fresh.maps.find(m=>m.id===room.destination_map_id)?.name || "destination map";
        if(!confirm(`Show ${name} to players? Its current fog and appearance states will be preserved.`))return;
        const result=await LGApi.post(`${base}/travel`,{...body,expected_active_map_id:fresh.active_map_id});
        location.href=result.editor_url;
      } catch(error) {
        await refresh().catch(()=>{});
        await reload().catch(()=>{});
        throw error;
      } finally {pending=false;redraw();}
    }
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
      redraw();
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
      if(selectMode.checked) {
        $("double-reveal-panel").open=true;
        const roomMode=$("room-select-mode");
        if(roomMode.checked) {roomMode.checked=false;roomMode.dispatchEvent(new Event("change",{bubbles:true}));}
      }
      redraw();
      if(data)show(data); else run(()=>refresh());
    };
    $("room-select-mode").addEventListener("change",()=>{if($("room-select-mode").checked)leaveSelection();redraw();});
    mask.onerror=()=>{mask.hidden=true;};
    return {
      selecting:()=>selectMode.checked,
      quickAction, redraw, leaveSelection,
      select,
      refresh: state=>{
        const version=`${state.cache_token}-${state.walls_version}-${state.fog_version}-${Number(state.is_active)}`;
        if(pending)return;
        if(version===lastVersion){redraw();return;}
        markers?.draw(null,false,scale());
        if(data && data.walls_version!==state.walls_version){selected=null;mask.hidden=true;}
        lastVersion=version;
        refresh().catch(error=>{lastVersion="";$("double-status").textContent=error.message;});
      }
    };
  };
})();
