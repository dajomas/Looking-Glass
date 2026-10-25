// DM-only notes. All rendered HTML comes from the server's sanitized Markdown renderer.
window.LGRoomNotes = class {
  constructor(mapId, toast) {
    this.mapId=mapId;this.toast=toast;this.point=null;this.room=null;this.dirty=false;this.generation=0;this.revealed=null;this.stateStamp=null;this.refreshGeneration=0;
    this.$=id=>document.getElementById(id);
    this.$("room-toggle").onclick=()=>this.collapse(!this.$("room-panel").classList.contains("collapsed"));
    try {this.collapse(localStorage.getItem("lg:room-panel-collapsed")==="true");} catch(_) {}
    for(const id of ["room-name","room-markdown"]) this.$(id).oninput=()=>{this.dirty=true;};
    this.$("room-cancel").onclick=()=>{this.dirty=false;if(this.room)this.show(this.room);};
    this.$("room-form").onsubmit=async e=>{
      e.preventDefault();if(!this.room||!this.point)return;
      const button=e.submitter;button.disabled=true;
      try {
        const room=await LGApi.post(`/api/maps/${this.mapId}/room-notes`,{
          ...this.point,area_key:this.room.area_key,revision:this.room.revision,
          name:this.$("room-name").value,markdown:this.$("room-markdown").value});
        this.dirty=false;this.show(room);this.toast("Room saved");
      } catch(error) {this.toast(error.message,"error");}
      finally {button.disabled=false;}
    };
    window.addEventListener("beforeunload",e=>{if(this.dirty){e.preventDefault();e.returnValue="";}});
  }
  async refresh(state) {
    const stamp=`${state.cache_token}:${state.walls_version}:${state.fog_version}`;
    if(stamp===this.stateStamp)return;
    this.stateStamp=stamp;
    const generation=++this.refreshGeneration;
    try {
      const result=await LGApi.get(`/api/maps/${this.mapId}/room-notes`);
      if(generation!==this.refreshGeneration)return;
      const revealed=new Set(result.rooms.filter(r=>r.revealed).map(r=>r.area_key));
      const next=this.revealed && result.rooms.find(r=>r.revealed&&!this.revealed.has(r.area_key));
      this.revealed=revealed;
      if(next&&!this.dirty&&!this.editing()) await this.select(next.x,next.y);
      else if(this.room&&!this.dirty&&!this.editing()&&!revealed.has(this.room.area_key)) {
        this.$("room-preview").textContent="";this.$("room-title").textContent="";
        this.$("room-form").hidden=true;this.$("room-status").textContent="Room hidden or geometry changed.";
        this.room=null;this.point=null;
      }
    } catch(error) {this.stateStamp=null;this.toast(error.message,"error");}
  }
  editing() {return this.$("room-select-mode").checked;}
  collapse(value) {
    this.$("room-panel").classList.toggle("collapsed",value);
    document.querySelector("main.editor").classList.toggle("room-panel-collapsed",value);
    this.$("room-panel-body").hidden=value;
    this.$("room-toggle").setAttribute("aria-expanded",String(!value));
    try {localStorage.setItem("lg:room-panel-collapsed",String(value));} catch(_) {}
  }
  show(room) {
    this.room=room;
    this.$("room-title").textContent=room.name||"Unnamed room";
    this.$("room-name").value=room.name;
    this.$("room-markdown").value=room.markdown;
    this.$("room-preview").innerHTML=room.html;
    this.$("room-status").textContent=room.revealed ? "Revealed room · DM notes only" : "Hidden room · DM notes only";
    this.$("room-form").hidden=false;
  }
  async select(x,y,explicit=false) {
    if(this.dirty && !confirm("Discard unsaved room notes?"))return;
    const generation=++this.generation;
    const room=await LGApi.post(`/api/maps/${this.mapId}/room-at`,{x,y});
    if(generation!==this.generation)return;
    if(!explicit && !room.revealed) {
      this.point=null;this.room=null;this.dirty=false;
      this.$("room-form").hidden=true;this.$("room-preview").textContent="";
      this.$("room-title").textContent="";this.$("room-status").textContent="Room hidden.";return;
    }
    this.point={x,y};this.dirty=false;this.show(room);
    // A deliberate collapse stays collapsed; notes still update in the background.
  }
};
