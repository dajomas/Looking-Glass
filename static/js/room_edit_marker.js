// Separate admin-only decoration; no fog state is modified or restored.
window.LGRoomEditMarker = class {
  constructor(mapId, toast) {
    this.mapId=mapId;this.toast=toast;this.generation=0;this.target=null;this.key=null;this.geometry=null;
    this.image=document.getElementById("room-edit-overlay");
    this.label=document.getElementById("room-edit-indicator");
  }
  clear() {
    this.generation++;this.key=null;
    this.image.hidden=true;this.image.removeAttribute("src");this.label.hidden=true;
  }
  mapChanged(state) {
    const stamp=`${state.cache_token}:${state.walls_version}:${state.width}:${state.height}`;
    if(this.geometry&&stamp!==this.geometry){
      const target=this.target;this.clear();
      if(target)this.set(true,target.room,target.point);
    }
    this.geometry=stamp;
  }
  set(editMode, room, point) {
    if(!editMode||!room||!point){this.target=null;this.clear();return;}
    this.target={room,point:{...point}};
    const key=`${room.area_key}:${point.x}:${point.y}`;
    if(this.key===key)return;
    this.clear();this.key=key;
    const generation=this.generation;
    this.label.textContent=`Editing room notes: ${room.name||"Unnamed room"}`;this.label.hidden=false;
    LGApi.post(`/api/maps/${this.mapId}/room-edit-overlay`,{...point,area_key:room.area_key}).then(result=>{
      if(generation!==this.generation||!this.target)return;
      if(result.area_key!==room.area_key)throw new Error("Room highlight does not match the selected room.");
      this.image.src=`data:image/png;base64,${result.png}`;this.image.hidden=false;
    }).catch(error=>{
      if(generation!==this.generation)return;
      this.clear();this.toast(error.message,"warn");
    });
  }
};
