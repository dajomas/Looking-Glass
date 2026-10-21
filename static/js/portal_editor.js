// One atomic draft transaction per pair edit. No autosave or viewer write capability.
window.LGPortalEditor = function({getWalls,getBusy,mutate,render,status,viewport}) {
  const $=id=>document.getElementById(id), dialog=$("portal-dialog"), a=$("portal-a"), b=$("portal-b");
  let originalPair=null;
  function options(select,selected) {
    select.replaceChildren();
    getWalls().forEach((w,i)=>{
      if(originalPair ? w[6]?.pair!==originalPair : !!w[6]?.pair)return;
      const opt=document.createElement("option");opt.value=i;opt.textContent=`Wall ${i+1} (${w[4]})`;select.appendChild(opt);
    });
    select.value=String(selected);
  }
  function showSides() {
    $("portal-sides").replaceChildren();
    [a,b].forEach((sel,end)=>{
      const w=getWalls()[Number(sel.value)];
      for(let side=0;side<2;side++) {
        const config=w?.[6]?.sides?.[side] || {role:end===0?(side===0?"entry":"none"):(side===0?"exit":"none"),kind:"door",after:"door",exit:0};
        const field=document.createElement("fieldset"),legend=document.createElement("legend");
        legend.textContent=`${end===0?"A":"B"} / Wall ${Number(sel.value)+1}, side ${side+1}`;field.appendChild(legend);
        for(const [key,label,values] of [
          ["role","Role",["entry","exit","both","none"]],
          ["kind","Entry initial type",["door","locked_door","unlocked_door","secret"]],
          ["after","Secret Entry becomes",["door","locked_door","unlocked_door"]],
          ["exit","Destination side on other element",[0,1]]]) {
          const lab=document.createElement("label"),input=document.createElement("select");
          lab.textContent=label;input.id=`portal-${end}-${side}-${key}`;
          values.forEach(v=>{const opt=document.createElement("option");opt.value=v;opt.textContent=key==="exit"?String(v+1):v.replaceAll("_"," ");input.appendChild(opt);});
          input.value=String(config[key] ?? (key==="exit"?0:"door"));lab.appendChild(input);field.appendChild(lab);
        }
        const sync=()=>{
          const role=$(`portal-${end}-${side}-role`).value,entry=["entry","both"].includes(role);
          for(const key of ["kind","after","exit"]) $(`portal-${end}-${side}-${key}`).disabled=!entry;
          $(`portal-${end}-${side}-after`).disabled=!entry || $(`portal-${end}-${side}-kind`).value!=="secret";
        };
        $("portal-sides").appendChild(field);
        $(`portal-${end}-${side}-role`).onchange=sync;$(`portal-${end}-${side}-kind`).onchange=sync;sync();
      }
    });
    render();
  }
  $("portal-configure").onclick=()=>{
    if(getBusy())return;
    const walls=getWalls();
    if(walls.length<2){status("Draw at least two elements before configuring a portal.",true);return;}
    originalPair=null;a.replaceChildren();
    walls.forEach((w,i)=>{const o=document.createElement("option");o.value=i;o.textContent=`Wall ${i+1} (${w[4]})`;a.appendChild(o);});
    a.value=String(Math.max(0,walls.findIndex(w=>w[4]==="portal")));
    selectA();$("portal-error").textContent="";dialog.showModal();a.focus();
  };
  function selectA() {
    const walls=getWalls(),i=Number(a.value),w=walls[i];originalPair=w?.[6]?.pair || null;
    const mate=originalPair?walls.findIndex((v,j)=>j!==i && v[6]?.pair===originalPair):-1;
    options(b,mate>=0?mate:walls.findIndex((v,j)=>j!==i && !v[6]?.pair));showSides();
  }
  a.onchange=selectA;b.onchange=showSides;
  function configs() {
    return [0,1].map(end=>[0,1].map(side=>{
      const val=key=>$(`portal-${end}-${side}-${key}`).value;
      const role=val("role");
      return ["entry","both"].includes(role)?{role,kind:val("kind"),after:val("after"),exit:Number(val("exit"))}:{role};
    }));
  }
  $("portal-form").onsubmit=event=>{
    event.preventDefault();
    const ai=Number(a.value),bi=Number(b.value),walls=getWalls();
    try {
      if(!a.value || !b.value || ai===bi || !walls[ai] || !walls[bi])throw Error("Choose two different elements.");
      const sides=configs(),used=new Set();let entries=0;
      sides.forEach((list,end)=>{
        if(list.filter(s=>s.role==="none").length>1)throw Error("At most one None side is allowed per element.");
        list.forEach(s=>{if(["entry","both"].includes(s.role)) {
          entries++;if(!["exit","both"].includes(sides[1-end][s.exit].role))throw Error("Each Entry must target an Exit/Both side on the other element.");
          used.add(`${1-end}:${s.exit}`);
        }});
      });
      if(!entries)throw Error("Configure at least one Entry and Exit.");
      sides.forEach((list,end)=>list.forEach((s,i)=>{if(["exit","both"].includes(s.role)&&!used.has(`${end}:${i}`))throw Error("Every Exit needs an incoming Entry.");}));
      const after=structuredClone(walls),pair=originalPair || Array.from(crypto.getRandomValues(new Uint8Array(16)),v=>v.toString(16).padStart(2,"0")).join("");
      [ai,bi].forEach((index,end)=>{after[index]=[...after[index].slice(0,4),"portal",true,{pair,end:end===0?"a":"b",sides:sides[end]}];});
      if(JSON.stringify(after)!==JSON.stringify(walls))mutate({batch:true,before:structuredClone(walls),after});
      dialog.close();status("Portal pair updated in draft. Save wall set to persist.");
    } catch(e) {$("portal-error").textContent=e.message;}
  };
  $("portal-remove").onclick=()=>{
    if(!originalPair){$("portal-error").textContent="Select an existing pair in Element A first.";return;}
    const before=structuredClone(getWalls()),after=before.map(w=>w[6]?.pair===originalPair?[...w.slice(0,4),"wall",true]:structuredClone(w));
    mutate({batch:true,before,after});dialog.close();status("Pair removed from draft; both elements are normal walls. Undo restores the pair.");
  };
  $("portal-cancel").onclick=()=>dialog.close();dialog.addEventListener("close",()=>viewport.focus());
  dialog.addEventListener("keydown",e=>e.stopPropagation());
};
