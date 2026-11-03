// Admin-only presentation. This module never changes arrow hit targets or fog state.
(function(host) {
  const seconds=value=>value!==null&&value!==""&&Number.isFinite(Number(value))?Math.max(1,Math.min(15,Number(value))):5;
  class Cycle {
    constructor(clock,onChange) {this.clock=clock;this.onChange=onChange;this.routes=[];this.index=0;this.timer=null;this.delay=5;this.running=false;}
    stop() {if(this.timer!==null)this.clock.clearTimeout(this.timer);this.timer=null;this.running=false;this.onChange(null);}
    schedule() {
      if(!this.running)return;
      this.timer=this.clock.setTimeout(()=>{this.timer=null;if(!this.running)return;this.index=(this.index+1)%this.routes.length;this.onChange(this.routes[this.index]);this.schedule();},this.delay*1000);
    }
    update(routes,enabled=true,delay=5) {
      const old=this.routes[this.index]?.id,ids=this.routes.map(r=>r.id).join("|"),nextIds=routes.map(r=>r.id).join("|"),nextDelay=seconds(delay);
      const unchanged=this.running&&enabled&&routes.length>=2&&ids===nextIds&&nextDelay===this.delay;
      this.routes=routes;this.delay=nextDelay;this.index=Math.max(0,routes.findIndex(r=>r.id===old));
      if(unchanged){this.onChange(this.routes[this.index]);return;}
      this.stop();if(!enabled||routes.length<2)return;
      this.running=true;this.onChange(routes[this.index]);this.schedule();
    }
  }
  function inViewport(route,view) {
    const visible=endpoint=>{
      const points=endpoint.polygon.map(([x,y])=>[view.x+x/view.workScale*view.scale,view.y+y/view.workScale*view.scale]);
      return Math.max(...points.map(p=>p[0]))>=0&&Math.min(...points.map(p=>p[0]))<=view.width&&
             Math.max(...points.map(p=>p[1]))>=0&&Math.min(...points.map(p=>p[1]))<=view.height;
    };
    return visible(route.entry)&&visible(route.exit);
  }
  const api={Cycle,seconds,inViewport};host.LGPortalCycle=api;if(typeof module!=="undefined")module.exports=api;
  api.mount=function({svg,slider,output,toggle,status,mapId,view}) {
    let state=null,ready=false,busy=false,storage;try{storage=host.localStorage;}catch(_){}
    let preference={seconds:5,enabled:true};
    try{const p=JSON.parse(storage?.getItem(`lg:portal-cycle:${mapId}`)||"null");if(p)preference={seconds:seconds(p.seconds),enabled:typeof p.enabled==="boolean"?p.enabled:true};}catch(_){}
    slider.value=preference.seconds;toggle.checked=preference.enabled;
    const reduced=host.matchMedia?.("(prefers-reduced-motion: reduce)");
    function render(route) {
      svg.replaceChildren();svg.dataset.routeId=route?.id||"";
      if(!route){status.textContent=!preference.enabled?"Portal highlighting paused":!ready||busy?"Waiting for current arrow image":document.hidden?"Paused while tab is hidden":"Needs two visible Entry/Exit routes (both arrows in view)";return;}
      for(const endpoint of [route.entry,route.exit]) {
        const polygon=document.createElementNS("http://www.w3.org/2000/svg","polygon");polygon.setAttribute("points",endpoint.polygon.map(p=>p.join(",")).join(" "));polygon.classList.add("portal-route-flash");
        if(reduced?.matches)polygon.classList.add("portal-route-steady");svg.appendChild(polygon);
      }
      status.textContent=`Section ${route.entry.section} ${route.entry.compass} → section ${route.exit.section} ${route.exit.compass} (${route.state.replaceAll("_"," ")})`;
    }
    const cycle=new Cycle(host,render);
    function refresh() {
      output.textContent=`${preference.seconds} s per pair`;
      const v=view(),routes=(state?.portal_routes||[]).filter(r=>v&&inViewport(r,v));
      cycle.update(routes,preference.enabled&&ready&&!busy&&!document.hidden&&!!state?.door_arrows_enabled,preference.seconds);
    }
    function save() {try{storage?.setItem(`lg:portal-cycle:${mapId}`,JSON.stringify(preference));}catch(_){}refresh();}
    slider.oninput=()=>{preference.seconds=seconds(slider.value);save();};toggle.onchange=()=>{preference.enabled=toggle.checked;save();};
    document.addEventListener("visibilitychange",refresh);reduced?.addEventListener?.("change",refresh);
    host.addEventListener("pagehide",()=>cycle.stop());host.addEventListener("pageshow",refresh);
    refresh();
    return {setState(next,isReady=false){state=next;ready=isReady;svg.setAttribute("viewBox",`0 0 ${next.work_width} ${next.work_height}`);refresh();},
            setMask(url){svg.style.maskImage=`url("${url}")`;svg.style.webkitMaskImage=`url("${url}")`;},
            setBusy(value){busy=value;refresh();},refresh};
  };
})(typeof window!=="undefined"?window:globalThis);
