// Read-only design/draft overview; never mutates walls or reveals runtime state.
(function(host) {
  function overviewRows(walls,links) {
    const P=host.LGPortalDraft,routes=links || P.linksFor(walls),incoming=new Map();
    for(const [key,dest] of routes) {
      const [index,side]=key.split(":").map(Number),w=walls[index];
      if(!w||w[4]!=="portal"||!["entry","both"].includes(w[6]?.sides?.[side]?.role))continue;
      const targetKey=`${dest.index}:${dest.side}`;if(!incoming.has(targetKey))incoming.set(targetKey,[]);
      incoming.get(targetKey).push(`Section ${index+1} ${P.sideName(w,side,true)}`);
    }
    const names={door:"Normal",locked_door:"Locked",unlocked_door:"Unlocked",secret:"Secret (undiscovered)"};
    return P.portals(walls).flatMap(({w,i})=>{
      const list=w[6]?.sides || P.blank().sides;
      return list.map((s,k)=>{
        const isEntry=["entry","both"].includes(s.role),dest=routes.get(`${i}:${k}`),target=dest&&walls[dest.index];
        return {section:i+1,side:P.sideName(w,k),role:s.role,
          state:isEntry?(names[s.kind]||"Normal"):s.role==="exit"?"Ordinary Exit":s.role==="none"?"Inactive":"Unconfigured",
          after:isEntry&&s.kind==="secret"?(names[s.after||"door"]||s.after):"—",
          to:isEntry?(target?.[4]==="portal"?`Section ${dest.index+1} ${P.sideName(target,dest.side,true)}`:"Not paired"):"—",
          from:(incoming.get(`${i}:${k}`)||[]).join(", ")||"—"};
      });
    });
  }
  host.LGPortalOverview={rows:overviewRows};if(typeof module!=="undefined")module.exports=host.LGPortalOverview;
  host.LGPortalOverview.mount=function({dialog,body,caption,close}) {
    const floating=host.LGFloatingDialog(dialog,document.getElementById("portal-overview-move"),document.getElementById("portal-overview-center"));
    close.onclick=()=>dialog.close();
    dialog.addEventListener("keydown",event=>event.stopPropagation());
    return {open(walls,links,pending=false) {
      body.replaceChildren();const rows=overviewRows(walls,links);
      for(const row of rows) {
        const tr=document.createElement("tr");
        for(const value of [row.section,row.side,row.role,row.state,row.after,row.to,row.from]) {
          const td=document.createElement("td");td.textContent=String(value);tr.appendChild(td);
        }
        body.appendChild(tr);
      }
      caption.textContent=rows.length?`${pending?"Pending popup edits":"Current wall-editor draft"}: authored initial states, not live discovery/locks. ${rows.length/2} portal sections.`:"No Portal elements in the current draft.";
      floating.open();close.focus();
    }};
  };
})(typeof window!=="undefined"?window:globalThis);
