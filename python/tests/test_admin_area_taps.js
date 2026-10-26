const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict");
const src=fs.readFileSync('static/js/admin_map_editor.js','utf8');
const tap=src.slice(src.indexOf('  function onTap('),src.indexOf('  const simple ='));
function app({mode='hide',door=null,arrow=null}={}){
 let id=0;const tasks=new Map(),calls=[];
 const clock={setTimeout(fn){tasks.set(++id,fn);return id;},clearTimeout(i){tasks.delete(i);}};
 const c={window:clock,console};vm.runInNewContext(fs.readFileSync('static/js/admin_area_taps.js','utf8'),c);
 Object.assign(c,{roomNotes:{editing:()=>false,select:async()=>{}},doubleReveal:null,mapTransitions:null,areaTaps:new c.window.LGAdminAreaTaps(clock),state:{width:400,height:200,cache_token:'t',walls_version:1,fog_version:2},
  MAP_ID:1,busy:false,maskKey:'t-1-2',stateKey:s=>`${s.cache_token}-${s.walls_version}-${s.fog_version}`,
  mode:()=>mode,pz:{scale:2,x:33,y:44},arrowHit:{at:()=>arrow},LGManagedDoorHit:()=>door,hiddenTypes:new Set(),$:()=>({checked:true}),
  doorTapQueue:{cancel(){},tap(key,stamp,single,double){c.doorGesture={single,double};}},
  LGApi:{post:async(path,body)=>{calls.push({path,body});return path.endsWith('/viewer-zoom')?{ok:true,viewers:2,sent:true}:{area_fraction:.1,is_active:true,walls:[]};},get:async()=>c.state},
  applyState(){},toast(){}});
 c.run=fn=>{c.pending=fn().catch(e=>c.error=e);};
 vm.runInNewContext(tap,c);
 return {c,calls,tap(x=100,y=100,button=0){c.onTap(x,y,{button,clientX:x*2+33,clientY:y*2+44});},
  async flush(){const fns=[...tasks.values()];tasks.clear();for(const fn of fns)fn();if(c.pending)await c.pending;}};
}
(async()=>{
 let a=app();const pose=[a.c.pz.x,a.c.pz.y,a.c.pz.scale];a.tap();assert.equal(a.calls.length,0);a.tap();await a.flush();
 assert.equal(a.calls.length,1);assert.equal(a.calls[0].path,'/api/maps/1/viewer-zoom');assert.equal(a.calls[0].body.fog_version,2);
 assert.deepEqual([a.c.pz.x,a.c.pz.y,a.c.pz.scale],pose);
 a=app();a.tap();await a.flush();assert.equal(a.calls[0].path,'/api/maps/1/hide');
 a=app({mode:'reveal'});a.tap();await a.flush();assert.equal(a.calls[0].path,'/api/maps/1/reveal');
 a=app();a.tap(100,100,2);await a.flush();assert.equal(a.calls[0].path,'/api/maps/1/reveal');
 a=app();a.tap();a.c.state.fog_version++;await a.flush();assert.equal(a.calls.length,0);
 a=app();a.tap();a.c.areaTaps.cancel();await a.flush();assert.equal(a.calls.length,0);
 a=app();a.tap();a.tap(200,100);await a.flush();assert.equal(a.calls.length,1);assert.equal(a.calls[0].path,'/api/maps/1/hide');
 a=app({arrow:{x:175,y:100}});a.tap(175,100);await a.flush();assert.equal(a.calls[0].path,'/api/maps/1/door-arrows/reveal');
 a=app({door:{wall_id:4,kind:'locked_door',hit:'arrow',x:175,y:100},arrow:{x:175,y:100}});a.tap(175,100);assert.ok(a.c.doorGesture);assert.equal(a.calls.length,0);
 a.c.doorGesture.double();await a.flush();assert.equal(a.calls[0].path,'/api/maps/1/door-action');assert.equal(a.calls[0].body.gesture,'double');
 console.log('Admin area single/double, mode, stale, cancellation, camera and door-priority tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
