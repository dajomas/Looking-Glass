"use strict";
const assert=require("node:assert/strict"),P=require("../../static/js/portal_editor.js");
const wall=(dx,dy)=>[0,0,dx,dy,"portal",true,P.blank()];
const directions=[[1,0,"N","S"],[1,1,"NE","SW"],[0,1,"E","W"],[-1,1,"SE","NW"],[-1,0,"S","N"],[-1,-1,"SW","NE"],[0,-1,"W","E"],[1,-1,"NW","SE"]];
for(const [dx,dy,a,b] of directions) {
  const w=wall(dx,dy);assert.equal(P.sideName(w,0,true),a);assert.equal(P.sideName(w,1,true),b);
  assert.equal(P.sideName([dx,dy,0,0,"portal",true,P.blank()],0,true),b);
}
assert.equal(P.sideName(wall(10,0),0),"North (N)");
assert.equal(P.sideName(wall(0,10),1),"West (W)");
assert.equal(P.sideName(wall(0,0),0),"Unknown");
assert.throws(()=>P.sideName(wall(1,0),2),/index/);
for(let angle=0;angle<360;angle+=.5) {
  const rad=angle*Math.PI/180,w=wall(Math.cos(rad),Math.sin(rad));
  const opposite=P.sideName(w,1,true),codes=["N","NE","E","SE","S","SW","W","NW"];
  assert.equal(codes[(codes.indexOf(P.sideName(w,0,true))+4)%8],opposite);
}
const fresh=()=>[wall(100,0),[200,0,200,100,"portal",true,P.blank()]];
for(const role of ["exit","unconfigured","none"]) {
  const rows=fresh(),links=new Map();P.roleChange(rows[0][6].sides,0,"entry");
  if(role!=="unconfigured")P.roleChange(rows[1][6].sides,0,role);
  assert.equal(P.selectableExit(rows[1][6].sides[0]),true);
  P.selectExit(rows,links,"0:0",{index:1,side:0});
  assert.equal(rows[1][6].sides[0].role,"exit");assert.equal(rows[1][6].sides[1].role,"none");
  const built=P.build(rows,links,()=>"pair");assert.equal(P.validate(built),true);
  assert.equal(built[0][6].sides[0].exit,0);assert.equal(P.sideName(built[1],0,true),"E");
}
for(const role of ["none","unconfigured"]) {
  const rows=fresh();P.roleChange(rows[0][6].sides,0,"entry");
  if(role==="none")P.roleChange(rows[1][6].sides,0,"none");
  const before=structuredClone(rows),built=P.build(rows,new Map([["0:0",{index:1,side:0}]]),()=>"p");
  assert.equal(built[1][6].sides[0].role,"exit");assert.deepEqual(rows,before);
}
let rows=fresh(),links=new Map();P.roleChange(rows[0][6].sides,0,"entry");
P.roleChange(rows[1][6].sides,0,"both");rows[1][6].sides[0].kind="secret";rows[1][6].sides[0].after="locked_door";
const original=structuredClone(rows[1][6].sides[0]);
P.selectExit(rows,links,"0:0",{index:1,side:0});assert.deepEqual(rows[1][6].sides[0],original);
rows=fresh();links=new Map();P.roleChange(rows[0][6].sides,0,"entry");P.roleChange(rows[1][6].sides,0,"entry");
const snapshot=structuredClone(rows);
assert.equal(P.selectableExit(rows[1][6].sides[0]),false);
assert.throws(()=>P.selectExit(rows,links,"0:0",{index:1,side:0}),/Entry-only/);
assert.deepEqual(rows,snapshot);assert.equal(links.size,0);
assert.throws(()=>P.selectExit(rows,links,"0:0",{index:0,side:0}),/another portal/);
rows=fresh();P.roleChange(rows[0][6].sides,0,"entry");P.roleChange(rows[1][6].sides,0,"exit");
P.roleChange(rows[1][6].sides,1,"entry");links=new Map();
P.selectExit(rows,links,"0:0",{index:1,side:0});assert.equal(rows[1][6].sides[1].role,"entry");
rows.push([300,0,300,100,"portal",true,P.blank()]);P.roleChange(rows[0][6].sides,1,"entry");
const snapshot2=structuredClone(rows);
assert.throws(()=>P.selectExit(rows,links,"0:1",{index:2,side:0}),/two sections/);assert.deepEqual(rows,snapshot2);
console.log("Compass: all eight headings, opposite/reversed geometry and 720 angular samples passed");
console.log("Exit selection: Exit/Unconfigured/None conversion, Both preservation, Entry-only and third-partner rejection passed");
