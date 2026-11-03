const {test}=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm"),path=require("node:path");
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const source=name=>fs.readFileSync(path.join(__dirname,"../../static/js/",name),"utf8");
function viewer(states){
 const elements=new Map(),images=[],intervals=[],timers=[],sockets=[];
 const element=id=>{if(!elements.has(id))elements.set(id,{hidden:false,textContent:"",src:"",addEventListener(){},classList:{add(){},remove(){}}});return elements.get(id);};
 class Image{constructor(){this.naturalWidth=400;this.naturalHeight=200;images.push(this);}decode(){return new Promise((resolve,reject)=>{this.ready=resolve;this.fail=reject;});}}
 class WebSocket{constructor(){this.readyState=1;this.sent=[];sockets.push(this);}send(body){this.sent.push(body);}close(){this.readyState=3;this.onclose({code:1006});}}
 const context={window:{LG_CAMPAIGN:1,addEventListener(){}},document:{getElementById:element},location:{protocol:"http:",host:"test",pathname:"/c/1"},Image,WebSocket,
 PanZoom:class{constructor(){this.scale=1;this.x=0;this.y=0;this.minScale=.02;this.maxScale=8;}setContentSize(w,h){this.w=w;this.h=h;}fit(){}apply(){}},
 console:{error(){}},setTimeout(fn,ms){timers.push({fn,ms});return timers.length;},clearTimeout(){},clearInterval(){},setInterval(fn,ms){intervals.push({fn,ms});},
 fetch:async()=>{const state=states.shift();if(state instanceof Error)throw state;return {ok:true,status:200,json:async()=>state};}};
 vm.runInNewContext(source("viewer_area_zoom.js"),context);
 for(const key of ["LGViewerAreaZoom","LGViewerDoubleTap","LGViewerHasNewAreas"])context[key]=context.window[key];
 vm.runInNewContext(source("viewer_display.js"),context);
 return {element,images,sockets,timers,poll:()=>intervals.find(i=>i.ms===40000).fn(),reports:()=>sockets[0].sent.filter(s=>s!=="ping").map(JSON.parse)};
}
const state=(version)=>({map:{name:version,version,image_url:`/${version}.png`}});

test("loading is not ready until decode and swap",async()=>{
 const app=viewer([state("1:t-1-1")]);await tick();
 assert.equal(app.reports().at(-1).state,"loading");
 app.images[0].ready();await tick();
 assert.equal(app.reports().at(-1).state,"ready");assert.equal(app.element("map").src,"/1:t-1-1.png");
});

test("older decode never acknowledges the newer image",async()=>{
 const app=viewer([state("1:t-1-1"),state("1:t-1-2")]);await tick();app.poll();await tick();
 app.images[1].ready();await tick();app.images[0].ready();await tick();
 const ready=app.reports().filter(r=>r.state==="ready");assert.equal(ready.length,1);assert.equal(ready[0].version,"1:t-1-2");
});

test("blank invalidates in-flight image and is acknowledged",async()=>{
 const app=viewer([state("1:t-1-1"),{map:null}]);await tick();app.poll();await tick();app.images[0].ready();await tick();
 assert.equal(app.element("stage").hidden,true);assert.equal(app.reports().at(-1).version,"blank");assert.equal(app.reports().at(-1).state,"ready");
});

test("failed decode reports failure and periodic refresh recovers",async()=>{
 const app=viewer([state("1:t-1-1"),state("1:t-1-1")]);await tick();app.images[0].fail(new Error("decode"));await tick();
 assert.equal(app.reports().at(-1).state,"failed");app.poll();await tick();app.images[1].ready();await tick();assert.equal(app.reports().at(-1).state,"ready");
});

test("fetch failure is visible, image timeout fails, close shows reconnecting",async()=>{
 const app=viewer([new Error("offline"),state("1:t-1-1")]);await tick();assert.equal(app.reports().at(-1).state,"failed");
 app.poll();await tick();app.timers.find(t=>t.ms===30000).fn();await tick();assert.equal(app.reports().at(-1).state,"failed");
 app.sockets[0].close();assert.equal(app.element("sync-status").textContent,"Reconnecting");
});

test("a stale failed decode cannot overwrite latest success status",async()=>{
 const app=viewer([state("1:t-1-1"),state("1:t-1-2")]);await tick();app.poll();await tick();app.images[1].ready();await tick();
 app.images[0].fail(new Error("old failure"));await tick();assert.equal(app.reports().at(-1).state,"ready");assert.equal(app.reports().at(-1).version,"1:t-1-2");
});

test("admin diagnostics render untrusted names only as text and clear on error",async()=>{
 const summary={textContent:""},list={rows:[],replaceChildren(){this.rows=[];},appendChild(row){this.rows.push(row);}},timers=[];
 const panel={dataset:{viewerSync:"1"},querySelector:sel=>sel.includes("summary")?summary:list};let fail=false;
 const context={document:{querySelectorAll:()=>[panel],createElement:()=>({textContent:""})},window:{addEventListener(){}},clearTimeout(){},setTimeout(fn){timers.push(fn);},
 fetch:async()=>({ok:!fail,status:fail?403:200,json:async()=>({blank:false,viewers:[{username:"<script>bad</script>",id:"abc",status:"up-to-date",last_report_seconds:0}]})})};
 vm.runInNewContext(source("admin_viewer_sync.js"),context);await tick();assert.ok(list.rows[0].textContent.includes("<script>bad</script>"));assert.equal(list.rows[0].innerHTML,undefined);
 fail=true;timers.shift()();await tick();assert.equal(list.rows.length,0);assert.ok(summary.textContent.includes("unavailable"));assert.equal(timers.length,0);
});
