// Draft-only single-section editor. Pair topology is unchanged on the server.
(function(host) {
  "use strict";
  const clone=value=>structuredClone(value), entry=s=>["entry","both"].includes(s.role), exit=s=>["exit","both"].includes(s.role);
  const blank=()=>({sides:[{role:"unconfigured"},{role:"unconfigured"}]});
  const config=w=>w[6] || blank();
  function sides(w) {return clone(config(w).sides || blank().sides);}
  function portals(rows) {return rows.map((w,i)=>({w,i})).filter(({w})=>w[4]==="portal");}
  // Presentation only: stored sides/routes remain the existing 0/1 indices.
  function sideName(w,index,short=false) {
    if(index!==0 && index!==1)throw Error("Invalid portal side index.");
    const dx=w[2]-w[0],dy=w[3]-w[1];
    if(!Number.isFinite(dx)||!Number.isFinite(dy)||(dx===0&&dy===0))return "Unknown";
    const angle=(Math.atan2(dy,dx)*180/Math.PI+360)%360;
    const heading=(Math.floor((angle+22.5+1e-10)/45)+(index===1?4:0))%8;
    const codes=["N","NE","E","SE","S","SW","W","NW"];
    const names=["North","North-East","East","South-East","South","South-West","West","North-West"];
    return short?codes[heading]:`${names[heading]} (${codes[heading]})`;
  }
  const selectableExit=s=>exit(s)||["unconfigured","none"].includes(s.role);
  function selectExit(rows,links,key,dest) {
    const [i,k]=key.split(":").map(Number),source=rows[i],target=rows[dest.index];
    if(source?.[4]!=="portal"||![0,1].includes(k)||!entry(config(source).sides?.[k]||{}))throw Error("Select an Entry/Both source first.");
    if(dest.index===i||target?.[4]!=="portal"||![0,1].includes(dest.side))throw Error("Choose an Exit side on another portal section.");
    const list=sides(target);
    if(!selectableExit(list[dest.side]))throw Error("Entry-only destination sides cannot be selected; configure the target as Both first.");
    if((config(source).pair||config(target).pair)&&config(source).pair!==config(target).pair)throw Error("Unpair before choosing another partner.");
    for(const [otherKey,other] of links) {
      if(otherKey===key)continue;
      const [j,side]=otherKey.split(":").map(Number);
      if(!entry(config(rows[j]).sides?.[side]||{}))continue;
      if((j===i&&other.index!==dest.index)||(other.index===i&&j!==dest.index)||
         (j===dest.index&&other.index!==i)||(other.index===dest.index&&j!==i))throw Error("A portal pair has two sections only. Unpair before choosing another partner.");
    }
    if(["unconfigured","none"].includes(list[dest.side].role))roleChange(list,dest.side,"exit");
    target[6]={...config(target),sides:list};
    links.set(key,{index:dest.index,side:dest.side});
  }
  function roleChange(list,index,role) {
    const old=list[index];
    list[index]=entry({role})?{role,kind:old.kind || "door",after:old.after || "door",...(Number.isInteger(old.exit)?{exit:old.exit}:{})}:{role};
    if(role!=="unconfigured" && list[1-index].role==="unconfigured")list[1-index]={role:"none"};
    return list;
  }
  function linksFor(rows) {
    const links=new Map();
    for(const {w,i} of portals(rows)) {
      const p=config(w),mate=rows.findIndex((v,j)=>j!==i && v[4]==="portal" && p.pair && v[6]?.pair===p.pair);
      sides(w).forEach((s,k)=>{if(entry(s) && mate>=0 && Number.isInteger(s.exit))links.set(`${i}:${k}`,{index:mate,side:s.exit});});
    }
    return links;
  }
  function build(rows,links,makeId) {
    const out=clone(rows),partners=new Map();
    for(const {w,i} of portals(out)) {
      const p=config(w);
      if(p.pair) {
        const mates=portals(out).filter(v=>v.i!==i && v.w[6]?.pair===p.pair);
        if(mates.length!==1)throw Error("Existing portal pair is incomplete; reset its configuration first.");
        partners.set(i,mates[0].i);
      }
      w[6]={...p,sides:sides(w)};
    }
    for(const [key,dest] of links) {
      const [i,k]=key.split(":").map(Number),w=out[i];
      if(w?.[4]!=="portal" || !entry(w[6].sides[k]))continue;
      if(dest.index===i || out[dest.index]?.[4]!=="portal" || ![0,1].includes(dest.side))throw Error("Choose an Exit side on another portal section.");
      const target=out[dest.index],list=target[6].sides;
      if(["unconfigured","none"].includes(list[dest.side].role))roleChange(list,dest.side,"exit");
      if(!exit(list[dest.side]))throw Error("The destination side must be Exit or Both. Configure it first.");
      if((partners.has(i)&&partners.get(i)!==dest.index)||(partners.has(dest.index)&&partners.get(dest.index)!==i))throw Error("A portal pair has two sections only. Unpair before choosing another partner.");
      partners.set(i,dest.index);partners.set(dest.index,i);w[6].sides[k].exit=dest.side;
    }
    for(const {w,i} of portals(out)) {
      const p=w[6],mate=partners.get(i);
      if(mate===undefined) {delete p.pair;delete p.end;continue;}
      if(i>mate)continue;
      const q=out[mate][6],same=p.pair && p.pair===q.pair;
      const id=same?p.pair:makeId();
      const end=same && ["a","b"].includes(p.end)?p.end:"a";
      p.pair=q.pair=id;p.end=end;q.end=end==="a"?"b":"a";
    }
    // An Entry without a selection must not silently retain its previous route.
    for(const {w,i} of portals(out))w[6].sides.forEach((s,k)=>{if(entry(s)&&!links.has(`${i}:${k}`))delete s.exit;});
    return out;
  }
  function validate(rows) {
    const groups=new Map();
    for(const {w,i} of portals(rows)) {
      const p=config(w),list=sides(w);
      if(list.length!==2 || list.some(s=>!["entry","exit","both","none"].includes(s.role)))throw Error(`Portal section ${i+1} still has an unconfigured side.`);
      if(list.filter(s=>s.role==="none").length>1)throw Error(`Portal section ${i+1} may have at most one None side.`);
      if(!p.pair || !["a","b"].includes(p.end))throw Error(`Portal section ${i+1} is not paired. Configure an Entry destination first.`);
      for(const s of list)if(entry(s)&&(![0,1].includes(s.exit)||!["door","locked_door","unlocked_door","secret"].includes(s.kind)||!["door","locked_door","unlocked_door"].includes(s.after || "door")))throw Error(`Portal section ${i+1} needs valid Entry states and an Exit destination.`);
      if(!groups.has(p.pair))groups.set(p.pair,[]);groups.get(p.pair).push({w,i});
    }
    for(const group of groups.values()) {
      if(group.length!==2 || new Set(group.map(v=>v.w[6].end)).size!==2)throw Error("Each portal pair needs exactly two sections.");
      const used=new Set();let count=0;
      group.forEach(({w,i})=>{const other=group.find(v=>v.i!==i);w[6].sides.forEach(s=>{if(entry(s)) {
        count++;if(!exit(other.w[6].sides[s.exit]))throw Error("An Entry targets a side that is not Exit/Both.");used.add(`${other.i}:${s.exit}`);
      }});});
      if(!count)throw Error("A portal pair needs an Entry and Exit.");
      group.forEach(({w,i})=>w[6].sides.forEach((s,k)=>{if(exit(s)&&!used.has(`${i}:${k}`))throw Error(`Exit on portal section ${i+1}, ${sideName(w,k)} needs an incoming Entry.`);}));
    }
    return true;
  }
  const api={blank,portals,roleChange,linksFor,build,validate,sideName,selectableExit,selectExit};host.LGPortalDraft=api;
  if(typeof module!=="undefined")module.exports=api;
  host.LGPortalEditor=function({getWalls,getBusy,mutate,status,viewport}) {
    const $=id=>document.getElementById(id),dialog=$("portal-dialog"),select=$("portal-section");
    let local=null,links=null,original=null;
    const uuid=()=>Array.from(crypto.getRandomValues(new Uint8Array(16)),v=>v.toString(16).padStart(2,"0")).join("");
    const current=()=>Number(select.value);
    function addOptions(input,items,value,placeholder) {
      input.replaceChildren();
      if(placeholder){const o=document.createElement("option");o.value="";o.textContent=placeholder;input.appendChild(o);}
      items.forEach(([v,text,disabled])=>{const o=document.createElement("option");o.value=String(v);o.textContent=text;o.disabled=!!disabled;input.appendChild(o);});
      input.value=value===undefined?"":String(value);
    }
    function field(parent,id,label,items,value) {
      const lab=document.createElement("label"),input=document.createElement("select");lab.textContent=label;input.id=id;
      addOptions(input,items,value);lab.appendChild(input);parent.appendChild(lab);return input;
    }
    function panel() {
      $("portal-sides").replaceChildren();const i=current(),list=local[i][6].sides;
      list.forEach((s,k)=>{
        const box=document.createElement("fieldset"),legend=document.createElement("legend");legend.textContent=`Portal section ${i+1} — ${sideName(local[i],k)}`;box.appendChild(legend);
        const role=field(box,`portal-side-${k}-role`,"Role",["unconfigured","entry","exit","both","none"].map(v=>[v,v==="unconfigured"?"Unconfigured":v[0].toUpperCase()+v.slice(1)]),s.role);
        role.onchange=()=>{roleChange(list,k,role.value);if(!entry(list[k]))links.delete(`${i}:${k}`);panel();};
        if(entry(s)) {
          const kind=field(box,`portal-side-${k}-kind`,"Entry initial type",["door","locked_door","unlocked_door","secret"].map(v=>[v,v.replaceAll("_"," ")]),s.kind);
          kind.onchange=()=>{s.kind=kind.value;panel();};
          if(s.kind==="secret") {
            const after=field(box,`portal-side-${k}-after`,"Secret Entry becomes",["door","locked_door","unlocked_door"].map(v=>[v,v.replaceAll("_"," ")]),s.after||"door");after.onchange=()=>s.after=after.value;
          }
          const dest=links.get(`${i}:${k}`),target=field(box,`portal-side-${k}-destination`,"Paired Exit portal section",[],undefined);
          const partner=portals(local).find(v=>v.i!==i && local[i][6].pair && v.w[6]?.pair===local[i][6].pair)?.i;
          addOptions(target,portals(local).filter(v=>v.i!==i).map(v=>[v.i,`Portal section ${v.i+1}`,partner!==undefined?v.i!==partner:!!v.w[6]?.pair]),dest?.index,"Choose portal section…");
          const destSide=field(box,`portal-side-${k}-exit`,"Paired Exit side",[],undefined);
          function refreshSides(index,value) {
            addOptions(destSide,index===undefined?[]:local[index][6].sides.map((v,j)=>[j,`${sideName(local[index],j)} — ${v.role}${["unconfigured","none"].includes(v.role)?" (changes to Exit)":""}`,!selectableExit(v)]),value,"Choose Exit side…");
            destSide.disabled=index===undefined;
          }
          refreshSides(dest?.index,dest?.side);
          target.onchange=()=>{links.delete(`${i}:${k}`);refreshSides(target.value===""?undefined:Number(target.value));};
          destSide.onchange=()=>{
            if(target.value===""||destSide.value===""){links.delete(`${i}:${k}`);return;}
            try {
              selectExit(local,links,`${i}:${k}`,{index:Number(target.value),side:Number(destSide.value)});
              $("portal-error").textContent="";panel();
            }catch(error){$("portal-error").textContent=error.message;}
          };
        }
        $("portal-sides").appendChild(box);
      });
    }
    $("portal-configure").onclick=()=>{
      if(getBusy())return;
      original=clone(getWalls());local=clone(original);
      const all=portals(local);if(!all.length){status("Add a Portal element before opening Portal configuration.",true);return;}
      all.forEach(({w})=>w[6]={...config(w),sides:sides(w)});links=linksFor(local);
      addOptions(select,all.map(v=>[v.i,`Portal section ${v.i+1}`]),all[0].i);$("portal-error").textContent="";panel();dialog.showModal();select.focus();
    };
    select.onchange=panel;
    $("portal-form").onsubmit=event=>{
      event.preventDefault();if(getBusy()||!local)return;
      try {
        if(JSON.stringify(getWalls())!==JSON.stringify(original))throw Error("The wall draft changed. Cancel and reopen configuration.");
        const after=build(local,links,uuid);
        if(JSON.stringify(after)!==JSON.stringify(original))mutate({batch:true,before:original,after});
        let complete=true;try{validate(after);}catch(_){complete=false;}
        dialog.close();status(complete?"Portal configuration applied to draft. Save wall set to persist.":"Portal draft updated. Finish unconfigured sides, pairing and routes before Save or Download.");
      }catch(e){$("portal-error").textContent=e.message;}
    };
    $("portal-remove").onclick=()=>{
      if(!local)return;
      const i=current(),pair=local[i][6]?.pair;
      const reset=new Set(portals(local).filter(v=>v.i===i || (pair&&v.w[6]?.pair===pair)).map(v=>v.i));
      for(const j of reset)local[j][6]=blank();
      for(const [key,value] of links)if(reset.has(Number(key.split(":")[0]))||reset.has(value.index))links.delete(key);
      $("portal-error").textContent="Configuration reset in this popup; Apply to draft to keep it. Paired sections are reset together and remain Portal elements.";panel();
    };
    $("portal-cancel").onclick=()=>dialog.close();dialog.addEventListener("close",()=>{local=null;links=null;original=null;viewport.focus();});
    dialog.addEventListener("keydown",event=>event.stopPropagation());
  };
})(typeof window!=="undefined"?window:globalThis);
