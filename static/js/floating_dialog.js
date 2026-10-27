// Movable native modal dialogs; title bars remain reachable after drag/resize.
window.LGFloatingDialog=function(dialog,handle,centerButton) {
  let position=null,drag=null;
  function bounds(x,y) {
    const r=dialog.getBoundingClientRect();
    return {x:Math.max(4,Math.min(x,Math.max(4,innerWidth-r.width-4))),y:Math.max(4,Math.min(y,Math.max(4,innerHeight-Math.min(r.height,innerHeight-8)-4)))};
  }
  function place(x,y) {
    position=bounds(x,y);dialog.style.left=position.x+"px";dialog.style.top=position.y+"px";
  }
  function reflow() {
    if (!dialog.open) return;
    const r=dialog.getBoundingClientRect();place(r.left,r.top);
  }
  let frame=null;
  const observer=typeof ResizeObserver!=="undefined" ? new ResizeObserver(()=>{
    if(!dialog.open || frame!==null)return;
    frame=requestAnimationFrame(()=>{frame=null;reflow();});
  }) : null;
  observer?.observe(dialog);
  function center() {
    const r=dialog.getBoundingClientRect();place((innerWidth-r.width)/2,(innerHeight-r.height)/2);
  }
  function open() {
    dialog.style.position="fixed";dialog.style.margin="0";
    dialog.showModal();if(position)place(position.x,position.y);else center();
  }
  handle.addEventListener("pointerdown",event=>{
    if(event.button!==0||event.target.closest("button,input,select,a"))return;
    const r=dialog.getBoundingClientRect();drag={id:event.pointerId,x:event.clientX,y:event.clientY,left:r.left,top:r.top};
    handle.setPointerCapture(event.pointerId);event.preventDefault();event.stopPropagation();handle.focus();
  });
  handle.addEventListener("pointermove",event=>{
    if(!drag||drag.id!==event.pointerId)return;
    place(drag.left+event.clientX-drag.x,drag.top+event.clientY-drag.y);event.preventDefault();
  });
  const end=event=>{if(drag&&drag.id===event.pointerId){drag=null;if(handle.hasPointerCapture(event.pointerId))handle.releasePointerCapture(event.pointerId);}};
  handle.addEventListener("pointerup",end);handle.addEventListener("pointercancel",end);handle.addEventListener("lostpointercapture",()=>drag=null);
  handle.addEventListener("keydown",event=>{
    if(event.target!==handle)return;
    const steps={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
    if(!steps[event.key])return;event.preventDefault();event.stopPropagation();
    const r=dialog.getBoundingClientRect(),[x,y]=steps[event.key],step=event.shiftKey?50:10;place(r.left+x*step,r.top+y*step);
  });
  centerButton?.addEventListener("click",center);
  dialog.addEventListener("close",()=>{drag=null;if(frame!==null){cancelAnimationFrame(frame);frame=null;}});
  window.addEventListener("resize",reflow);
  return {open,center,reflow};
};
