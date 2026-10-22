(()=>{
 "use strict";
 const status=document.getElementById("transitions-overview-status"),host=document.getElementById("transitions-overview");
 async function refresh(){try{
  const data=await LGApi.get(`/api/campaigns/${window.LG_TRANSITIONS_CAMPAIGN}/transitions`);host.replaceChildren();
  for(const item of data.endpoints){
   const row=document.createElement("p"),a=document.createElement("a");a.href=`/maps/${item.map_id}`;a.textContent=`${item.map_name}: ${item.name}`;row.append(a);
   row.append(document.createTextNode(` → ${item.broken?"BROKEN LINK":item.destination_id?data.maps.find(m=>m.id===item.destination_map_id)?.name+": "+item.destination_name:"No outgoing connection"} (${item.kind}; ${item.current_visibility}; ${item.current_availability})`));host.append(row);
  }status.textContent=`${data.endpoints.length} passage endpoints.`;
 }catch(e){status.textContent=e.message;}}
 document.getElementById("transitions-refresh").onclick=refresh;
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",refresh);else refresh();
})();
