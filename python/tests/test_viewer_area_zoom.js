const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function response(data,status=200){return {ok:status>=200&&status<300,status,json:async()=>data};}
function app(){
 const elements=new Map(),handlers=new Map(),intervals=[],timers=[],images=[],queries=[];let pz,now=0;
 const view={left:0,top:0,width:1000,height:600};
 const element=id=>{if(!elements.has(id))elements.set(id,{hidden:false,src:"",textContent:"",classList:{add(){},remove(){}},
   getBoundingClientRect:()=>view,addEventListener(type,fn){const key=id+":"+type;if(!handlers.has(key))handlers.set(key,[]);handlers.get(key).push(fn);},
   click(){if(this.onclick)this.onclick();}});return elements.get(id);};
 const a={x:10,y:10,width:180,height:180},b={x:210,y:50,width:180,height:100};
 let state={map:{name:"M",version:"1:token-1-1",width:400,height:200,image_url:"/image",revealed_bounds:{x:10,y:10,width:380,height:180}}};
 let deferred=null,delayArea=false;
 const context={console,URLSearchParams,Date:{now:()=>now},document:{getElementById:element},location:{protocol:"http:",host:"test",pathname:"/c/1"},
   Image:class{constructor(){this.naturalWidth=200;this.naturalHeight=100;images.push(this);}decode(){return Promise.resolve();}},
   PanZoom:class{constructor(v,s,opts){this.w=this.h=1;this.x=this.y=0;this.scale=1;this.minScale=.02;this.maxScale=8;this.opts=opts;this.pointers=new Map();pz=this;}
      setContentSize(w,h){this.w=w;this.h=h;}apply(){}fit(){this.scale=4.9;this.x=10;this.y=55;}},
   WebSocket:class{},setInterval(fn,ms){intervals.push({fn,ms});},clearInterval(){},setTimeout(fn){timers.push(fn);return timers.length;},clearTimeout(){},
   fetch:async url=>{
    if(url.includes('/area-bounds?')){
      queries.push(url);const u=new URL(url,'http://test'),x=Number(u.searchParams.get('x'));
      const data={ok:true,version:u.searchParams.get('v'),bounds:x>=390 || (state.hideA && x<200)?null:(x<200?a:b)};
      if(delayArea){delayArea=false;return new Promise(resolve=>{deferred=()=>resolve(response(data));});}
      return response(data);
    }
    return response(state);
   }};
 context.window=context;context.LG_CAMPAIGN=1;context.addEventListener=(type,fn)=>{handlers.set('window:'+type,[...(handlers.get('window:'+type)||[]),fn]);};
 vm.runInNewContext(fs.readFileSync('static/js/viewer_area_zoom.js','utf8'),context);
 vm.runInNewContext(fs.readFileSync('static/js/viewer_display.js','utf8'),context);
 function fire(type,event={}){for(const fn of handlers.get('viewport:'+type)||[])fn(event);}
 function tap(x,y){now+=70;fire('pointerdown',{button:0});pz.opts.onTap(x/2,y/2,{button:0,clientX:x/2*pz.scale+pz.x,clientY:y/2*pz.scale+pz.y});}
 return {context,element,queries,view,a,b,get pz(){return pz;},
   pose:()=>({x:pz.x,y:pz.y,scale:pz.scale}),double:async(x,y)=>{tap(x,y);tap(x,y);await tick();},
   expected:bounds=>context.LGViewerAreaZoom.target(bounds,400,200,pz,view),
   poll:async()=>{await intervals.find(i=>i.ms===40000).fn();await tick();},
   setState:s=>{state=s;},tap,delay:()=>{delayArea=true;},resolve:async()=>{deferred();await tick();},fire,
   resize(){for(const fn of handlers.get('window:resize')||[])fn();timers.pop()();},
   bump(){state={map:{...state.map,version:'1:token-1-2'}};}};
}
function near(actual,expected){for(const k of ['x','y','scale'])assert.ok(Math.abs(actual[k]-expected[k])<1e-8,`${k}: ${actual[k]} != ${expected[k]}`);}
(async()=>{
 let v=app();await tick();const overview=v.pose();
 await v.double(100,100);near(v.pose(),v.expected(v.a));assert.equal(v.queries.length,1);
 await v.double(100,100);near(v.pose(),overview);
 await v.double(100,100);await v.double(300,100);near(v.pose(),v.expected(v.b));
 await v.double(300,100);near(v.pose(),overview);
 await v.double(100,100);v.pz.x+=40;await v.double(100,100);near(v.pose(),v.expected(v.a)); // actual camera, not a stale flag
 const focused=v.pose();await v.double(395,100);near(v.pose(),focused); // hidden target is a no-op
 v.element('btn-fit').click();near(v.pose(),overview);
 await v.double(100,100);v.view.width=800;v.resize();near(v.pose(),v.expected(v.a));
 v.bump();await v.poll();near(v.pose(),v.expected(v.a)); // retained/revalidated focus
 assert.ok(v.queries.some(q=>q.includes('x=100'))); // image-to-source scaling
 v=app();await tick();await v.double(100,100);v.setState({hideA:true,map:{name:"M",version:"1:token-1-2",width:400,height:200,image_url:"/image",revealed_bounds:v.b}});await v.poll();near(v.pose(),v.expected(v.b));
 v=app();await tick();v.delay();await v.double(100,100);v.pz.x=123;v.pz.scale=2;v.fire('wheel');
 const manual=v.pose();await v.resolve();near(v.pose(),manual); // late response cannot overwrite navigation
 v=app();await tick();v.delay();await v.double(100,100);v.setState({map:null});await v.poll();await v.resolve();
 assert.equal(v.element('stage').hidden,true);
 // Recognizer: far-apart taps, drags/zoom cancellation, and timeout cannot pair.
 v=app();await tick();v.tap(100,100);v.fire('wheel');v.tap(100,100);await tick();assert.equal(v.queries.length,0);
 v=app();await tick();v.tap(100,100);v.pz.moved=true;v.pz.pointers.set(1,{});v.fire('pointermove');v.pz.pointers.clear();v.pz.moved=false;v.tap(100,100);await tick();assert.equal(v.queries.length,0);
 v=app();await tick();v.tap(100,100);v.pz.pointers.set(1,{});v.pz.pointers.set(2,{});v.fire('pointerdown',{button:0});v.pz.pointers.clear();v.tap(100,100);await tick();assert.equal(v.queries.length,0);
 const T=v.context.LGViewerDoubleTap,pair=new T();
 assert.equal(pair.tap(10,10,0),false);assert.equal(pair.tap(100,10,50),false);
 pair.cancel();assert.equal(pair.tap(10,10,100),false);assert.equal(pair.tap(10,10,600),false);
 pair.cancel();pair.tap(10,10,1000);assert.equal(pair.tap(11,11,1100),true);
 const geometry=v.context.LGViewerAreaZoom;
 const pz={w:200,h:100,minScale:.02,maxScale:8,scale:1,x:0,y:0};
 assert.equal(geometry.target(v.a,400,200,pz,{width:0,height:600}),null);
 console.log('Viewer room focus/toggle, other room, manual camera, hidden clicks, resize, refresh and stale-response tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
