/* Explicit, read-only lookup using the selected room's saved name. */
window.LGScryingGlassRoom = class {
  constructor(mapId) {
    this.mapId=mapId;this.generation=0;this.key="";this.room=null;this.point=null;
    this.button=document.getElementById("scrying-room-check");
    this.status=document.getElementById("scrying-room-status");
    this.button.onclick=()=>this.check();
  }
  set(room,point,editing,dirty) {
    const valid=!!room && !!point && !editing && !dirty && !!room.name?.trim();
    const key=JSON.stringify([room?.area_key,room?.revision,room?.name,point?.x,point?.y,valid]);
    if(key===this.key)return;
    this.key=key;this.generation++;this.room=room;this.point=point;this.valid=valid;
    this.button.disabled=!valid;
    this.status.textContent=valid ? "Check for a saved battle setup with this room name." : "Select a named room and save or cancel edits before checking.";
  }
  async check() {
    if(!this.valid || this.button.disabled)return;
    const gen=++this.generation,room=this.room,point=this.point;
    this.button.disabled=true;this.status.textContent="Checking Scrying Glass…";
    try {
      const result=await LGApi.post(`/api/maps/${this.mapId}/scrying-glass/check`,{
        x:point.x,y:point.y,area_key:room.area_key,revision:room.revision});
      if(gen!==this.generation)return;
      this.status.textContent=result.message;
    } catch(error) {
      if(gen===this.generation)this.status.textContent="Scrying Glass: "+error.message;
    } finally {if(gen===this.generation)this.button.disabled=!this.valid;}
  }
};
