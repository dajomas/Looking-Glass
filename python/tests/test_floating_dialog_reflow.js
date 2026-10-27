const assert = require("node:assert/strict");
const events = new Map(), frames = new Map(); let id=0, resized;
global.window=global;global.innerWidth=1400;global.innerHeight=1000;
global.addEventListener=(name,fn)=>events.set(name,fn);
global.requestAnimationFrame=fn=>{frames.set(++id,fn);return id;};
global.cancelAnimationFrame=id=>frames.delete(id);
global.ResizeObserver=class {constructor(fn){resized=fn;} observe(){} };
function element(){return {addEventListener(){},focus(){}};}
const dialog={open:false,style:{},height:400,addEventListener:(n,fn)=>events.set('dialog:'+n,fn),
 showModal(){this.open=true;},
 getBoundingClientRect(){return {left:parseFloat(this.style.left)||0,top:parseFloat(this.style.top)||0,width:720,height:this.height};}};
require('../../static/js/floating_dialog.js');
const api=LGFloatingDialog(dialog,element(),element());api.open();
assert.equal(parseFloat(dialog.style.top),300);
dialog.height=850;resized();resized();assert.equal(frames.size,1);
for(const [key,fn] of frames){frames.delete(key);fn();}
assert.ok(parseFloat(dialog.style.top)+850<=996);
const top=dialog.style.top;dialog.height=500;api.reflow();assert.equal(dialog.style.top,top);
resized();dialog.open=false;events.get('dialog:close')();assert.equal(frames.size,0);
console.log('Floating dialog dynamic growth, coalescing, position retention and close cleanup passed');
