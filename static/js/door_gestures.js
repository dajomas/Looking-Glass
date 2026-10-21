// Managed-door single clicks wait so a double click cannot reveal before locking.
window.LGDoorTapQueue = class {
  constructor(delay=400,clock=window) {this.delay=delay;this.clock=clock;this.pending=null;}
  cancel() {if(this.pending)this.clock.clearTimeout(this.pending.timer);this.pending=null;}
  tap(key,stamp,single,double) {
    if(this.pending && this.pending.key===key && this.pending.stamp===stamp) {
      this.cancel();double();return;
    }
    this.cancel();
    const pending={key,stamp};
    pending.timer=this.clock.setTimeout(()=>{if(this.pending!==pending)return;this.pending=null;single();},this.delay);
    this.pending=pending;
  }
};
window.LGManagedDoorHit = function(state,arrowPoint,x,y,scale,showWalls,hiddenTypes) {
  if(arrowPoint) {
    const px=arrowPoint.x*state.work_scale,py=arrowPoint.y*state.work_scale;
    function inside(poly) {
      let found=false;
      for(let i=0,j=poly.length-1;i<poly.length;j=i++) {
        const [ax,ay]=poly[i],[bx,by]=poly[j];
        if(((ay>py)!==(by>py)) && px<(bx-ax)*(py-ay)/(by-ay)+ax)found=!found;
      }
      return found;
    }
    let hit=[...(state.door_arrows||[])].reverse().find(a=>inside(a.polygon));
    if(!hit) {
      // Pillow and browser edge rounding may differ. Server independently validates the ID.
      hit=[...(state.door_arrows||[])].reverse().find(a=>{
        const xs=a.polygon.map(p=>p[0]),ys=a.polygon.map(p=>p[1]);
        return px>=Math.min(...xs)-1 && px<=Math.max(...xs)+1 && py>=Math.min(...ys)-1 && py<=Math.max(...ys)+1;
      });
    }
    if(hit?.exit_only)return {blocked:true};
    if(hit && (hit.portal || hit.secret_origin || ["locked_door","unlocked_door","secret"].includes(hit.kind)))
      return {wall_id:hit.wall_id,kind:hit.kind,side:hit.side ?? -1,hit:"arrow",...arrowPoint};
    if(!hit)return {blocked:true};
    return null;
  }
  let best=null,limit=10/scale;
  for(const w of state.managed_doors||[]) {
    if(w.kind!=="locked_door" && (!showWalls || hiddenTypes.has(w.kind)))continue;
    const dx=w.x2-w.x1,dy=w.y2-w.y1;
    const t=Math.max(0,Math.min(1,((x-w.x1)*dx+(y-w.y1)*dy)/(dx*dx+dy*dy||1)));
    const d=Math.hypot(x-w.x1-t*dx,y-w.y1-t*dy);
    if(d<=limit){limit=d;best={wall_id:w.wall_id,kind:w.kind,hit:"wall",x,y};}
  }
  return best;
};
