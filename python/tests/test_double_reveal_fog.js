const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
class Element {
  constructor(){this.checked=false;this.hidden=false;this.open=false;this.children=[];this.listeners={};this.value="";this.style={setProperty:(k,v)=>{this.style[k]=v;}};}
  replaceChildren(...c){this.children=c;}
  append(...c){this.children.push(...c);}
  addEventListener(t,f){(this.listeners[t] ||= []).push(f);}
  dispatchEvent(e){for(const f of this.listeners[e.type]||[])f(e);}
  focus(){this.focused=true;}
}
const nodes=new Map(),get=id=>{if(!nodes.has(id))nodes.set(id,new Element());return nodes.get(id);};
const room={area_key:"a".repeat(64),x:20,y:30,revision:1,true_active:0,destination_map_id:2,valid_geometry:true,revealed:true,name:"Stairs"};
let state={cache_token:"t",walls_version:1,fog_version:2,image_revision:1,active_map_id:1,can_undo:false,maps:[{id:2,name:"Lower floor"}],rooms:[{...room}]};
const copy=()=>JSON.parse(JSON.stringify(state));
let approved=true,confirmations=0,reloads=0,clock=1000,fogMode=true,failPost=false,failGet=false,override=null;
const writes=[];
const ctx={window:{},Date:{now:()=>clock},Event:function(t){this.type=t;},
  document:{getElementById:get,createElement:()=>new Element(),querySelectorAll:()=>[get("reveal"),get("hide")],querySelector:()=>get("reveal")},
  Option:function(t,v){this.text=t;this.value=v;},location:{},confirm:()=>{confirmations++;return approved;},
  LGApi:{get:async path=>{if(failGet)throw Error("network unavailable");const r=copy();if(path.includes("/room?"))r.selected=override||{...r.rooms[0]};return r;},
    post:async(path,body)=>{if(failPost)throw Error("stale write");writes.push({path,body});if(path.endsWith("/travel"))return {editor_url:"/maps/2"};
      assert.ok(path.endsWith("/appearance"));state.rooms[0].true_active=1;state.rooms[0].revision++;return copy();}}
};
vm.runInNewContext(fs.readFileSync("static/js/double_reveal_markers.js","utf8"),ctx);
vm.runInNewContext(fs.readFileSync("static/js/double_reveal.js","utf8"),ctx);
const control=ctx.window.LGDoubleReveal({mapId:1,run:fn=>fn(),reload:async()=>{reloads++;},fogMode:()=>fogMode,scale:()=>2});
async function sync(){await get("double-refresh").onclick();}
(async()=>{
  await sync();assert.equal(get("double-fog-markers").children[0].textContent,"2");
  assert.equal(get("double-fog-markers").style["--double-marker-scale"],"0.5");
  await Promise.all([control.quickAction(20,30),control.quickAction(20,30)]);
  assert.equal(writes.length,1);assert.ok(writes[0].path.endsWith("/appearance"));assert.equal(writes[0].body.true_active,true);
  assert.equal(writes[0].body.revision,1);assert.equal(writes[0].body.fog_version,2);assert.equal(confirmations,0);assert.equal(ctx.location.href,undefined);
  assert.equal(get("double-fog-markers").children[0].textContent,"↗");
  await control.quickAction(20,30);assert.equal(writes.length,1);
  clock+=700;approved=false;await control.quickAction(20,30);assert.equal(writes.length,1);assert.equal(confirmations,1);
  approved=true;await control.quickAction(20,30);assert.equal(writes.length,2);assert.ok(writes[1].path.endsWith("/travel"));
  assert.equal(writes[1].body.expected_active_map_id,1);assert.equal(ctx.location.href,"/maps/2");const count=writes.length;
  state.rooms[0].revealed=false;await sync();await assert.rejects(control.quickAction(20,30),/fog before/);
  state.rooms[0].revealed=true;state.active_map_id=2;await sync();await assert.rejects(control.quickAction(20,30),/source map to players/);
  state.active_map_id=1;state.rooms[0].destination_map_id=null;await sync();assert.equal(get("double-fog-markers").hidden,true);
  await assert.rejects(control.quickAction(20,30),/no destination/);
  state.rooms[0].destination_map_id=2;state.rooms[0].valid_geometry=false;await sync();assert.equal(get("double-fog-markers").hidden,true);
  await assert.rejects(control.quickAction(20,30),/No valid/);state.rooms[0].valid_geometry=true;await sync();
  override={...room,revision:0};await assert.rejects(control.quickAction(80,80),/No valid/);override=null;
  state.rooms[0].true_active=0;await sync();state.rooms[0].true_active=1;state.rooms[0].revision++;
  await assert.rejects(control.quickAction(20,30),/Room state changed/);assert.equal(writes.length,count);
  failPost=true;await assert.rejects(control.quickAction(20,30),/stale write/);failPost=false;
  failGet=true;await assert.rejects(control.quickAction(20,30),/network unavailable/);failGet=false;
  fogMode=false;control.redraw();assert.equal(get("double-fog-markers").hidden,true);await control.quickAction(20,30);assert.equal(writes.length,count);
  fogMode=true;get("double-select").checked=true;get("double-select").onchange();assert.equal(get("double-fog-markers").hidden,true);
  get("double-done").onclick();assert.equal(control.selecting(),false);assert.equal(get("fog-panel").open,true);assert.equal(get("reveal").focused,true);
  state.rooms[0].true_active=0;state.rooms[0].revealed=false;await sync();await control.quickAction(20,30);assert.equal(state.rooms[0].revealed,false);
  const source=fs.readFileSync("static/js/admin_map_editor.js","utf8");
  const code=source.slice(source.indexOf("  function onTap("),source.indexOf("  const simple ="));
  let actions=0,cancels=0,transitions=0,notes=0,editing=false,prevented=0;
  const route={doubleReveal:{selecting:()=>false,quickAction:()=>{actions++;}},roomNotes:{editing:()=>editing,select:()=>{notes++;}},
    areaTaps:{cancel:()=>cancels++},doorTapQueue:{cancel:()=>cancels++},mapTransitions:{tap:()=>{transitions++;return false;}},
    state:{width:100,height:100},busy:false,maskKey:"stale",stateKey:()=>"current",run:fn=>fn()};
  vm.runInNewContext(code,route);const ctrl={button:0,ctrlKey:true,preventDefault:()=>prevented++};
  route.onTap(20,30,ctrl);assert.equal(actions,1);assert.equal(transitions,0);assert.equal(prevented,1);
  route.busy=true;route.onTap(20,30,ctrl);route.busy=false;route.onTap(-1,30,ctrl);assert.equal(actions,1);
  editing=true;route.onTap(20,30,ctrl);assert.equal(notes,1);assert.equal(actions,1);
  editing=false;route.onTap(20,30,{button:0});assert.equal(transitions,1);assert.equal(actions,1);assert.ok(cancels>=8);assert.ok(reloads>=1);
  console.log("Double Reveal fog shortcuts, markers, guards and click routing passed");
})().catch(e=>{console.error(e);process.exitCode=1;});
