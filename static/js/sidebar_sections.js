// Fog-editor peer sections form an accordion; nested controls and legend are independent.
(()=>{
 "use strict";
 const sidebar=document.getElementById("sidebar");if(!sidebar)return;
 const panels=[...sidebar.querySelectorAll('details[name="fog-editor-panels"]')];
 // Markup supplies the initial closed state. This fallback also works without native name support.
 for(const panel of panels)panel.addEventListener("toggle",()=>{
  if(panel.open)for(const other of panels)if(other!==panel&&other.open)other.open=false;
 });
})();
