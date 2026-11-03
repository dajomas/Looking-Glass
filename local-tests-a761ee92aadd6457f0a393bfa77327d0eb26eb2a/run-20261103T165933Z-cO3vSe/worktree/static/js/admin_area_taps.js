// Separate area gestures from fog single clicks; do not reinterpret door/arrow gestures.
window.LGAdminAreaTaps = class {
  constructor(clock=window,delay=400,tolerance=12) {
    this.clock=clock;this.delay=delay;this.tolerance=tolerance;this.pending=null;
  }
  cancel() {if(this.pending)this.clock.clearTimeout(this.pending.timer);this.pending=null;}
  tap(x,y,stamp,single,double) {
    const old=this.pending;
    if(old && old.stamp===stamp && Math.hypot(x-old.x,y-old.y)<=this.tolerance) {
      this.cancel();double();return;
    }
    // A different target cancels rather than allowing a delayed fog action on stale context.
    this.cancel();
    const next={x,y,stamp};
    next.timer=this.clock.setTimeout(()=>{if(this.pending!==next)return;this.pending=null;single();},this.delay);
    this.pending=next;
  }
};
