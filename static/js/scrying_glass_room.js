/* Automatic saved-name lookup, gated by server-side configuration/access verification. */
window.LGScryingGlassRoom = class {
  constructor(mapId) {
    this.mapId=mapId;this.generation=0;this.key="";this.inFlight=false;
    this.room=null;this.point=null;this.valid=false;this.checkedUntil=0;
    this.gate=null;this.gateUntil=0;this.gatePromise=null;this.cache=new Map();
    this.status=document.getElementById("scrying-room-status");
    this.status.hidden=true;
  }
  ttl(result) {return Math.min(60,Math.max(1,Number(result?.retry_after_seconds)||30))*1000;}
  set(room,point,editing,dirty) {
    const valid=!!room && !!point && !editing && !dirty && !!room.name?.trim();
    // Selection coordinates do not affect an area identity; avoid repeated checks in one room.
    const key=JSON.stringify([room?.area_key,room?.revision,room?.name,valid]);
    if(key!==this.key) {
      this.key=key;this.generation++;this.inFlight=false;this.checkedUntil=0;
      this.status.hidden=true;this.status.textContent="";
    }
    this.room=room;this.point=point;this.valid=valid;
    if(!valid || this.inFlight || Date.now()<this.checkedUntil)return;
    const cached=this.cache.get(key);
    if(cached && cached.until>Date.now() && this.gate?.verified) {
      this.status.textContent=cached.message;this.status.hidden=!cached.message;
      this.checkedUntil=cached.until;return;
    }
    this.check();
  }
  async verifyAccess() {
    if(this.gate && Date.now()<this.gateUntil)return this.gate;
    if(!this.gatePromise) {
      this.gatePromise=LGApi.post(`/api/maps/${this.mapId}/scrying-glass/access`,{}).then(result=>{
        this.gate=result;this.gateUntil=Date.now()+this.ttl(result);return result;
      }).finally(()=>{this.gatePromise=null;});
    }
    return this.gatePromise;
  }
  async check() {
    if(!this.valid || this.inFlight)return;
    const gen=this.generation,key=this.key,room=this.room,point=this.point;
    this.inFlight=true;
    try {
      const gate=await this.verifyAccess();
      if(gen!==this.generation)return;
      if(!gate.enabled || !gate.verified) {
        this.checkedUntil=this.gateUntil;
        this.status.textContent=gate.enabled ? (gate.message||"") : "";
        this.status.hidden=!this.status.textContent;return;
      }
      this.status.hidden=false;this.status.textContent="Checking Scrying Glass…";
      const result=await LGApi.post(`/api/maps/${this.mapId}/scrying-glass/check`,{
        x:point.x,y:point.y,area_key:room.area_key,revision:room.revision});
      if(gen!==this.generation)return;
      const until=Math.min(this.gateUntil,Date.now()+this.ttl(result));
      this.checkedUntil=until;
      this.status.textContent=result.message||"";this.status.hidden=!this.status.textContent;
      if(result.enabled===false || result.verified===false) {
        this.gate=result;this.gateUntil=until;
      }
      if(this.cache.size>=64)this.cache.delete(this.cache.keys().next().value);
      this.cache.set(key,{until,message:this.status.textContent});
    } catch(error) {
      if(gen!==this.generation)return;
      this.cache.clear();
      // Stop rapid room changes from repeatedly attempting a failed connection/login.
      this.gate={enabled:true,verified:false,message:"Scrying Glass: "+error.message};
      this.gateUntil=Date.now()+30000;
      if(gen===this.generation) {
        this.checkedUntil=this.gateUntil;this.status.textContent=this.gate.message;this.status.hidden=false;
      }
    } finally {if(gen===this.generation)this.inFlight=false;}
  }
};
