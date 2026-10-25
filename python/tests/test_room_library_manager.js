const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Node {
 constructor(){this.children=[];this.dataset={};this.textContent='';this.disabled=false;this.events={};}
 appendChild(n){this.children.push(n);}
 replaceChildren(){this.children=[];}
 addEventListener(k,fn){this.events[k]=fn;}
 querySelectorAll(tag){return this.children.flatMap(c=>[...(tag==='button'&&c.tag==='button'?[c]:[]),...c.querySelectorAll(tag)]);}
 showModal(){this.open=true;}
 close(){this.open=false;this.events.close?.();}
}
const nodes=new Map(),node=id=>{if(!nodes.has(id))nodes.set(id,new Node());return nodes.get(id);};
let entries=[{id:1,name:'Taken',markdown:'Old',assigned:true,notes_match:false},{id:2,name:'<unsafe>',markdown:'<script>bad</script>',assigned:false}],calls=0,answer=true,reject=false;
const c={window:{},document:{getElementById:node,createElement:tag=>Object.assign(new Node(),{tag})},confirm:()=>answer,
 LGApi:{get:async()=>({entries}),del:async()=>{calls++;if(reject)throw Error('Now assigned');entries=entries.filter(e=>e.id!==2);return {entries};}}};
vm.runInNewContext(fs.readFileSync('static/js/room_library_manager.js','utf8'),c);
(async()=>{
 const owner={mapId:1,libraryGeneration:0,renderLibrary(){this.renders=(this.renders||0)+1;}};
 const manager=new c.window.LGRoomLibraryManager(owner);await manager.refresh();
 const list=node('room-library-list');assert.equal(list.children.length,2);assert.equal(list.querySelectorAll('button').length,1);
 assert.equal(list.children[1].children[0].textContent,'<unsafe> (#2)');
 assert.equal(list.children[1].children[2].children[1].textContent,'<script>bad</script>','notes must be assigned via textContent');
 await manager.remove(1);assert.equal(calls,0,'assigned entry has no delete action');
 answer=false;await manager.remove(2);assert.equal(calls,0);
 answer=true;reject=true;await manager.remove(2);assert.equal(node('room-library-status').textContent,'Now assigned');assert.equal(owner.libraryEntries.length,2);
 reject=false;await manager.remove(2);assert.equal(owner.libraryEntries.length,1);assert.equal(list.children.length,1);
 assert.equal(list.querySelectorAll('button').length,0);
 console.log('Library list, safe text, assigned protection and delete-refresh tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
