// Pure camera geometry and double-tap recognition; no map/fog mutation.
window.LGViewerAreaZoom = {
  target(bounds, imageWidth, imageHeight, pz, viewport) {
    if (!bounds || !imageWidth || !imageHeight || !viewport.width || !viewport.height) return null;
    const sx = pz.w/imageWidth, sy = pz.h/imageHeight;
    const scale = Math.max(pz.minScale, Math.min(pz.maxScale,
      .90*Math.min(viewport.width/Math.max(1,bounds.width*sx), viewport.height/Math.max(1,bounds.height*sy))));
    return {scale, x:viewport.width/2-(bounds.x+bounds.width/2)*sx*scale,
      y:viewport.height/2-(bounds.y+bounds.height/2)*sy*scale};
  },
  matches(pz, target) {
    return target && Math.abs(pz.scale-target.scale) <= Math.max(1e-6,target.scale*1e-4) &&
      Math.abs(pz.x-target.x) <= 1 && Math.abs(pz.y-target.y) <= 1;
  },
  apply(pz, target) {if (target) {Object.assign(pz,target); pz.apply();}}
};
window.LGViewerDoubleTap = class {
  constructor() {this.last=null;}
  cancel() {this.last=null;}
  tap(x,y,time) {
    const old=this.last;
    this.last={x,y,time};
    if (old && time>=old.time && time-old.time<=400 && Math.hypot(x-old.x,y-old.y)<=12) {
      this.last=null; return true;
    }
    return false;
  }
};
