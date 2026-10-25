// Saved room-name coverage, independent of reveal state and edit highlighting.
window.LGRoomNameOverlay = class {
  constructor(mapId, toast) {
    this.mapId=mapId;this.toast=toast;this.enabled=false;this.generation=0;this.stamp=null;this.loading=false;
    this.$=id=>document.getElementById(id);
    this.checkbox=this.$("room-select-mode");this.button=this.$("room-name-toggle");
    this.image=this.$("room-name-overlay");this.legend=this.$("room-name-legend");
    this.button.onclick=()=>{
      if(!this.checkbox.checked)return;
      this.enabled=!this.enabled;this.sync();
    };
    this.checkbox.addEventListener("change",()=>this.sync());
    this.sync();
  }
  clear() {
    this.generation++;this.loading=false;
    this.image.hidden=true;this.image.removeAttribute("src");this.legend.hidden=true;
  }
  sync() {
    this.button.hidden=!this.checkbox.checked;
    if(!this.checkbox.checked)this.enabled=false;
    this.button.textContent=this.enabled?"Hide named / unnamed areas":"Show named / unnamed areas";
    this.button.setAttribute("aria-pressed",String(this.enabled));
    if(!this.enabled){this.clear();return;}
    this.refresh();
  }
  mapChanged(state) {
    const stamp=`${state.cache_token}:${state.walls_version}:${state.width}:${state.height}`;
    if(stamp===this.stamp)return;
    this.stamp=stamp;
    if(this.enabled)this.refresh();
  }
  async refresh() {
    if(!this.enabled||!this.checkbox.checked)return;
    this.clear();const generation=this.generation;this.loading=true;
    try {
      const result=await LGApi.get(`/api/maps/${this.mapId}/room-name-overlay`);
      if(generation!==this.generation||!this.enabled||!this.checkbox.checked)return;
      this.image.src=`data:image/png;base64,${result.png}`;this.image.hidden=false;
      this.legend.textContent=`Green: named (${result.named}) · Red: unnamed (${result.unnamed})`;
      this.legend.hidden=false;
    } catch(error){
      if(generation!==this.generation)return;
      this.clear();this.toast("Room name overlay: "+error.message,"warn");
    } finally {if(generation===this.generation)this.loading=false;}
  }
};
