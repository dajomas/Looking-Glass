const assert=require("node:assert/strict");
const fs=require("node:fs"),vm=require("node:vm");
class Element {
  constructor(){this.checked=false;this.hidden=false;this.disabled=false;this.value="";this.children=[];this.listeners={};}
  replaceChildren(...children){this.children=children;}
  append(...children){this.children.push(...children);}
  addEventListener(name,fn){this.listeners[name]=fn;}
  dispatchEvent(event){this.listeners[event.type]?.(event);}
  focus(){this.focused=true;}
}
const ids=new Map(),get=id=>{if(!ids.has(id))ids.set(id,new Element());return ids.get(id);};
let state={ok:true,cache_token:"t",walls_version:1,fog_version:2,image_revision:1,active_map_id:1,
  can_undo:false,maps:[{id:2,name:"Upper floor"}],rooms:[]};
const fresh=()=>JSON.parse(JSON.stringify(state));
const row={area_key:"a".repeat(64),x:20,y:30,revision:0,true_active:0,destination_map_id:null,name:"Stair room",valid_geometry:true,revealed:true};
const reads=[],writes=[],errors=[];let pending,approved=true;
const ctx={window:{},document:{getElementById:get,createElement:()=>new Element(),
    querySelectorAll:()=>[get("fog-reveal"),get("fog-hide")],querySelector:()=>get("fog-reveal")},
  Event:function(type){this.type=type;},
  Option:function(text,value){this.text=text;this.value=value;},location:{},confirm:()=>approved,
  LGApi:{get:async path=>{reads.push(path);const result=fresh();if(path.includes("/room?"))result.selected=state.rooms[0]||{...row};return result;},
    post:async(path,body)=>{writes.push({path,body});
      if(path.endsWith("/room")){state.rooms=[{...row,revision:1,destination_map_id:body.destination_map_id}];}
      else if(path.endsWith("/appearance")){state.rooms[0].true_active=Number(body.true_active);state.rooms[0].revision++;state.can_undo=true;}
      else if(path.endsWith("/undo")){state.rooms[0].true_active=0;state.rooms[0].revision++;state.can_undo=false;}
      else if(path.endsWith("/travel"))return {editor_url:"/maps/2"};
      state.fog_version++;return fresh();},del:async()=>{throw Error("unexpected delete");}}};
vm.runInNewContext(fs.readFileSync("static/js/double_reveal.js","utf8"),ctx);
const run=fn=>{pending=Promise.resolve().then(fn).catch(e=>errors.push(e));return pending;};
let reloads=0;const control=ctx.window.LGDoubleReveal({mapId:1,run,reload:async()=>{reloads++;}});
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  control.refresh({cache_token:"t",walls_version:1,fog_version:2,is_active:true});await flush();
  assert.equal(writes.length,0);assert.equal(get("double-room-form").hidden,true);
  get("double-select").checked=true;get("room-select-mode").checked=true;get("double-select").onchange();
  assert.equal(get("room-select-mode").checked,false);await control.select(20,30);
  assert.equal(writes.length,0);assert.equal(get("double-true").disabled,true);assert.equal(get("double-room-mask").hidden,false);
  get("double-enabled").checked=true;get("double-destination").value="2";get("double-save").onclick();await pending;
  assert.equal(writes[0].path,"/api/maps/1/double-reveal/room");assert.equal(writes[0].body.enabled,true);assert.equal(writes[0].body.destination_map_id,2);
  assert.equal(get("double-true").disabled,false);assert.equal(get("double-travel").disabled,true);
  get("double-true").onclick();await pending;assert.equal(writes[1].body.true_active,true);assert.equal(ctx.location.href,undefined);
  assert.equal(get("double-travel").disabled,false);assert.equal(reloads,2);
  approved=false;get("double-travel").onclick();await flush();assert.equal(writes.length,2);
  approved=true;get("double-travel").onclick();await pending;
  assert.equal(writes[2].path,"/api/maps/1/double-reveal/travel");assert.equal(ctx.location.href,"/maps/2");
  get("double-undo").onclick();await pending;assert.equal(writes[3].path,"/api/maps/1/double-reveal/undo");
  get("room-select-mode").checked=true;get("room-select-mode").listeners.change();assert.equal(control.selecting(),false);
  assert.equal(get("double-room-mask").hidden,true);assert.deepEqual(errors,[]);
  const source=fs.readFileSync("static/js/admin_map_editor.js","utf8");
  const tap=source.slice(source.indexOf("  function onTap("),source.indexOf("  const simple ="));
  let selections=0,cancels=0;
  const test={doubleReveal:{selecting:()=>true,select:()=>{selections++;}},areaTaps:{cancel:()=>cancels++},doorTapQueue:{cancel:()=>cancels++},state:{width:100,height:100},busy:false,run:fn=>fn()};
  vm.runInNewContext(tap,test);test.onTap(20,30,{button:0});assert.equal(selections,1);
  test.onTap(20,30,{button:2});test.onTap(-1,30,{button:0});assert.equal(selections,1);assert.equal(cancels,6);
  console.log("Double reveal controls and production selection interception passed");
})().catch(error=>{console.error(error);process.exitCode=1;});
