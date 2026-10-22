// DM-only cross-map navigation. Viewer markers are server-composited.
window.LGMapTransitions=(()=>{
 "use strict";
 const codes={stairs:"S",ladder:"L",hole:"H",portal:"P",climb:"C",custom:"X"},$=id=>document.getElementById(id);
 function option(select,value,text){const o=document.createElement("option");o.value=value;o.textContent=text;select.append(o);}
 function mount({mapId,campaignId,scale,dimensions,onSaved,cancelGestures}){
  const base=`/api/campaigns/${campaignId}`,dialog=$("transition-editor"),td=$("transition-travel");
  let data=null,current=null,placing=false,locked=false,preview=null,travelRequest=null;
  const status=t=>$("transition-status").textContent=t;
  async function guard(fn,error="transition-error"){
   if(locked)return;locked=true;
   const controls=[...document.querySelectorAll("#transition-editor button,#transition-travel button,#transition-add,#transition-reset")],before=controls.map(x=>x.disabled);
   controls.forEach(x=>x.disabled=true);$(error).textContent="";
   try{await fn();}catch(e){$(error).textContent=e.message;status(e.message);}
   finally{controls.forEach((x,i)=>x.disabled=before[i]);locked=false;}
  }
  function draw(){
   const svg=$("transition-markers"),d=dimensions();if(!data||!d)return;
   svg.setAttribute("viewBox",`0 0 ${d.width} ${d.height}`);svg.replaceChildren();
   const ns="http://www.w3.org/2000/svg",size=12/scale();
   for(const item of data.endpoints.filter(e=>e.map_id===mapId)){
    const g=document.createElementNS(ns,"g"),c=document.createElementNS(ns,"circle"),t=document.createElementNS(ns,"text");
    c.setAttribute("cx",item.x);c.setAttribute("cy",item.y);c.setAttribute("r",size);c.setAttribute("fill",item.current_visibility==="secret"?"#8227a1":item.current_visibility==="admin"?"#555":"#174b72");
    c.setAttribute("stroke",item.broken?"#ff5555":"white");c.setAttribute("stroke-width",2/scale());
    t.setAttribute("x",item.x);t.setAttribute("y",item.y);t.setAttribute("text-anchor","middle");t.setAttribute("dominant-baseline","central");t.setAttribute("font-size",14/scale());t.setAttribute("fill","white");t.textContent=codes[item.kind];g.append(c,t);svg.append(g);
   }
  }
  function render(){
   const list=$("transition-list");list.replaceChildren();
   for(const item of data.endpoints.filter(e=>e.map_id===mapId)){
    const b=document.createElement("button");b.type="button";b.textContent=`${codes[item.kind]} ${item.name} — ${item.current_visibility} / ${item.current_availability}${item.broken?" [BROKEN LINK]":!item.destination_id?" [unlinked]":""}`;b.onclick=()=>open(item);list.append(b);
   }
   const m=data.maps.find(m=>m.id===mapId);
   if(m){$("transition-viewer-markers").checked=!!m.viewer_transition_markers;$("transition-viewer-labels").checked=!!m.viewer_transition_labels;}draw();
  }
  async function reload(){data=await LGApi.get(`${base}/transitions`);render();return data;}
  function fillDestinations(selected){const s=$("tr-destination");s.replaceChildren();option(s,"","No outgoing connection");for(const e of data.endpoints.filter(e=>String(e.map_id)===$("tr-map").value))option(s,e.id,e.name);s.value=selected||"";}
  function fillMaps(destination){const s=$("tr-map");s.replaceChildren();option(s,"","Choose another map");for(const m of data.maps.filter(m=>m.id!==mapId))option(s,m.id,m.name);const dest=data.endpoints.find(e=>e.id===destination);if(dest)s.value=String(dest.map_id);fillDestinations(destination);}
  function read(){return {map_id:mapId,name:$("tr-name").value,player_label:$("tr-label").value,kind:$("tr-kind").value,x:Number($("tr-x").value),y:Number($("tr-y").value),visibility:$("tr-visibility").value,availability:$("tr-availability").value,destination_id:$("tr-destination").value||null,arrival:$("tr-arrival").value,notes:$("tr-notes").value,revision:current?.revision||null,return_link:$("tr-return").checked};}
  function open(item){
   cancelGestures();current=item||null;placing=false;$("transition-error").textContent="";
   const d=dimensions(),v=item||{name:"New passage",player_label:"",kind:"stairs",x:d.width/2,y:d.height/2,visibility:"discovered",availability:"usable",arrival:"area",notes:""};
   for(const k of ["name","kind","x","y","visibility","availability","arrival","notes"])$("tr-"+k).value=v[k];
   $("tr-label").value=v.player_label;$("tr-return").checked=false;fillMaps(v.destination_id);
   $("tr-runtime").hidden=!item;$("tr-delete").hidden=!item;$("tr-save-runtime").hidden=!item;$("tr-open").disabled=$("tr-travel").disabled=!item?.destination_id;
   $("tr-current-visibility").value=item?.runtime_visibility||"";$("tr-current-availability").value=item?.runtime_availability||"";
   if(!dialog.open)dialog.showModal();
  }
  async function saved(result){data=result;render();await onSaved();}
  $("transition-add").onclick=()=>{if(!data||!dimensions())return;open(null);dialog.close();cancelGestures();current=null;placing=true;status("Click the map to place a passage; Escape cancels.");};
  $("tr-place").onclick=()=>{cancelGestures();placing=true;dialog.close();status("Click the new location; Escape cancels.");};
  $("tr-close").onclick=()=>dialog.close();$("tr-map").onchange=()=>fillDestinations(null);
  $("tr-kind").onchange=()=>{if(!current)$("tr-availability").value=$("tr-kind").value==="climb"?"approval":"usable";};
  $("tr-create-destination").onclick=()=>{const id=Number($("tr-map").value);if(!id){$("transition-error").textContent="Choose a destination map first.";return;}window.open(`/maps/${id}?create_transition=1`,"_blank","noopener");$("transition-error").textContent="Create and save the endpoint in the new tab, then Reload destinations here.";};
  $("tr-reload-destinations").onclick=()=>guard(async()=>{const chosen=$("tr-destination").value;await reload();fillDestinations(chosen);});
  $("transition-form").onsubmit=e=>{e.preventDefault();guard(async()=>{await saved(await LGApi.post(`${base}/transitions${current?"/"+current.id:""}`,read()));dialog.close();status("Endpoint saved.");});};
  $("tr-save-runtime").onclick=()=>guard(async()=>{if(!current)return;const id=current.id;await saved(await LGApi.post(`${base}/transitions/${id}/runtime`,{revision:current.revision,visibility:$("tr-current-visibility").value||null,availability:$("tr-current-availability").value||null}));open(data.endpoints.find(e=>e.id===id));});
  $("tr-delete").onclick=()=>{if(!current||!confirm("Delete this endpoint? Incoming links will be marked broken."))return;guard(async()=>{await saved(await LGApi.del(`${base}/transitions/${current.id}?revision=${current.revision}`));dialog.close();});};
  $("transition-reset").onclick=()=>{if(!confirm("Reset passage session states on this map? Fog and authored settings are unchanged."))return;guard(async()=>{await saved(await LGApi.post(`/api/maps/${mapId}/transitions/reset`));});};
  for(const id of ["transition-viewer-markers","transition-viewer-labels"])$(id).onchange=()=>guard(async()=>{try{await saved(await LGApi.post(`/api/maps/${mapId}/transition-markers`,{enabled:$("transition-viewer-markers").checked,labels:$("transition-viewer-labels").checked}));}catch(e){render();throw e;}});
  $("tr-open").onclick=()=>{
   if(locked||!current?.destination_id)return;
   const sourceId=current.id,sourceRevision=current.revision,destinationId=current.destination_id;
   const tab=window.open("about:blank","_blank");
   if(tab)tab.opener=null;
   let navigated=false;
   return guard(async()=>{
    try{
     await reload();
     const source=data.endpoints.find(e=>e.id===sourceId);
     const dest=data.endpoints.find(e=>e.id===destinationId);
     if(!source||source.revision!==sourceRevision||source.destination_id!==destinationId||!dest)throw Error("Passage destination changed. Close and reopen this endpoint.");
     const map=data.maps.find(m=>m.id===dest.map_id);
     if(!map)throw Error("Destination map is no longer available.");
     const action=await window.LGChooseFog(map.name,dest.map_id,{includeCurrentReveals:true});
     if(!action){status("Destination display cancelled; no map was changed.");return;}
     await LGApi.post(`${base}/active`,{map_id:dest.map_id,fog_action:action});
     const url=`/maps/${dest.map_id}`;
     if(tab&&!tab.closed)tab.location.href=url;
     else location.href=url; // Popups blocked/closed: navigate this admin tab instead.
     navigated=true;dialog.close();status("Destination shown in admin and on viewer screens.");
     await reload();await onSaved();
    }finally{if(!navigated&&tab&&!tab.closed)tab.close();}
   });
  };
  $("tr-travel").onclick=()=>guard(async()=>{
   await reload();current=data.endpoints.find(e=>e.id===current?.id);if(!current)throw Error("Endpoint deleted; reload.");
   if(data.active_map_id!==mapId)throw Error("Show this source map to players before travelling.");
   preview=await LGApi.get(`${base}/transitions/${current.id}/preview`);
   $("tr-travel-summary").textContent=`${current.name} → ${preview.destination_map_name} / ${preview.destination_name}. ${preview.arrival==="area"?"Reveal "+(preview.fraction*100).toFixed(1)+"% of the destination map.":"Preserve destination fog."} State: ${preview.source_visibility}, ${preview.source_state}.`;
   $("tr-approve").checked=false;$("tr-approve").required=preview.needs_override;$("tr-large").checked=false;$("tr-large").required=preview.warning;$("tr-large-label").hidden=!preview.warning;$("tr-travel-error").textContent="";
   travelRequest={source_endpoint_id:current.id,expected_active_map_id:data.active_map_id,source_revision:preview.source_revision,destination_revision:preview.destination_revision,destination_version:preview.destination_version,request_id:window.crypto?.randomUUID?.()||`${Date.now()}-${Math.random().toString(36).slice(2)}`};
   dialog.close();td.showModal();
  });
  $("tr-cancel-travel").onclick=()=>{td.close();travelRequest=null;};
  $("transition-travel-form").onsubmit=e=>{e.preventDefault();guard(async()=>{const result=await LGApi.post(`${base}/travel`,{...travelRequest,override:$("tr-approve").checked,allow_large_reveal:$("tr-large").checked});location.href=result.admin_url;},"tr-travel-error");};
  window.addEventListener("keydown",e=>{if(e.key==="Escape"&&placing){placing=false;status("Placement cancelled.");}});
  const refresh=()=>{if(!locked&&!dialog.open&&!td.open&&!placing)reload().catch(e=>status(e.message));};
  reload().then(()=>{if(new URLSearchParams(location.search).has("create_transition"))$("transition-add").click();}).catch(e=>status(e.message));
  setInterval(refresh,15000);window.addEventListener("focus",refresh);
  return {draw,tap(x,y,event){if(!data||locked||event?.button!==0)return false;if(placing){if(!dialog.open)dialog.showModal();$("tr-x").value=x.toFixed(2);$("tr-y").value=y.toFixed(2);placing=false;status("Location selected. Save to apply.");return true;}const hit=data.endpoints.filter(e=>e.map_id===mapId).reverse().find(e=>Math.hypot(e.x-x,e.y-y)*scale()<=14);if(hit){open(hit);return true;}return false;}};
 }
 return {mount};
})();
