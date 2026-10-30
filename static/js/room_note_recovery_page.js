// Dedicated management workspace. Never render archive content as HTML.
window.LGRoomRecoveryPage=class {
  constructor(root){
    this.root=root;this.mapId=Number(root.dataset.mapId);
    this.width=Number(root.dataset.width);this.height=Number(root.dataset.height);
    this.cacheToken=root.dataset.cacheToken;this.wallsVersion=Number(root.dataset.wallsVersion);
    this.pageSize=Number(root.dataset.pageSize)||50;
    this.selected=null;this.target=null;this.point=null;this.next=null;
    this.busy=false;this.loading=false;this.targetLoading=false;this.blocked=true;
    this.listGeneration=0;this.targetGeneration=0;
    this.$=id=>document.getElementById('recovery-'+id);
    this.$('refresh').onclick=()=>this.load(true);
    this.$('more').onclick=()=>this.load(false);
    this.$('apply').onclick=()=>this.recover();
    this.$('target-form').onsubmit=e=>{e.preventDefault();this.inspect(Number(this.$('x').value),Number(this.$('y').value));};
    for(const id of ['x','y'])this.$(id).oninput=()=>{
      if(this.busy)return;
      ++this.targetGeneration;this.targetLoading=false;this.blocked=true;
      this.status('Coordinates changed. Inspect the target before recovering.');this.controls();
    };
    this.$('map').onclick=e=>{
      if(this.busy||e.button!==0)return;
      const rect=this.$('map').getBoundingClientRect();
      if(!rect.width||!rect.height)return;
      const x=(e.clientX-rect.left)*this.width/rect.width;
      const y=(e.clientY-rect.top)*this.height/rect.height;
      this.$('x').value=String(x);this.$('y').value=String(y);this.inspect(x,y);
    };
    this.$('map').onerror=()=>this.status('Artwork could not be loaded. Reload the page; no recovery was performed.');
    window.addEventListener('beforeunload',e=>{if(this.busy){e.preventDefault();e.returnValue='';}});
    this.controls();this.load(true);
  }
  status(text){this.$('status').textContent=text;}
  controls(){
    this.root.querySelectorAll('button,input').forEach(el=>el.disabled=this.busy);
    this.$('refresh').disabled=this.busy||this.loading;
    this.$('more').disabled=this.busy||this.loading;this.$('more').hidden=this.next===null;
    this.$('apply').disabled=this.busy||this.loading||this.targetLoading||this.blocked||!this.selected||!this.target;
    this.root.setAttribute('aria-busy',String(this.busy||this.loading||this.targetLoading));
  }
  choose(entry){
    if(this.busy)return;
    this.selected=entry;
    this.$('source-name').textContent=JSON.stringify(entry.name);
    this.$('source').textContent=entry.markdown;
    const {name,markdown,...provenance}=entry;
    this.$('provenance').textContent=JSON.stringify(provenance,null,2);
    this.$('list').querySelectorAll('[data-archive-id]').forEach(button=>
      button.setAttribute('aria-pressed',String(button.dataset.archiveId===String(entry.id))));
    this.controls();
  }
  async load(reset){
    if(this.busy||this.loading||(!reset&&this.next===null))return;
    this.loading=true;const generation=++this.listGeneration;this.controls();
    this.status('Loading retained notes…');
    const query=new URLSearchParams({limit:String(this.pageSize)});
    if(!reset)query.set('before_id',String(this.next));
    try{
      const page=await LGApi.get(`/api/maps/${this.mapId}/room-note-archives?${query}`);
      if(generation!==this.listGeneration)return;
      if(!page||!Array.isArray(page.archives))throw Error('Invalid archive response.');
      if(reset)this.$('list').replaceChildren();
      for(const entry of page.archives){
        const button=document.createElement('button');button.type='button';
        button.dataset.archiveId=String(entry.id);button.textContent=`${entry.name.trim()||'Unnamed'} (#${entry.id})`;
        button.setAttribute('aria-pressed',String(this.selected?.id===entry.id));
        button.onclick=()=>this.choose(entry);this.$('list').appendChild(button);
      }
      this.next=page.next_before_id??null;
      this.status(page.archives.length?'Choose retained notes and inspect a target room.':'No retained notes on this page.');
    }catch(error){if(generation===this.listGeneration)this.status(error.message);}
    finally{if(generation===this.listGeneration){this.loading=false;this.controls();}}
  }
  checkRoom(room){
    const fields=['area_key','revision','cache_token','walls_version','room_notes_version'];
    if(!room||typeof room.name!=='string'||typeof room.markdown!=='string'||fields.some(key=>room[key]===undefined))
      throw Error('Invalid target response. Inspect again before recovery.');
    if(room.cache_token!==this.cacheToken||room.walls_version!==this.wallsVersion)
      throw Error('Map incarnation or boundaries changed. Reload this page before recovery.');
    return room;
  }
  renderTarget(){
    this.$('target-name').textContent=JSON.stringify(this.target.name);
    this.$('target-markdown').textContent=this.target.markdown;
    this.$('replace-label').hidden=!(this.target.name||this.target.markdown);
    this.$('replace').checked=false;
  }
  async inspect(x,y){
    if(this.busy)return;
    const generation=++this.targetGeneration;this.blocked=true;
    if(!Number.isFinite(x)||!Number.isFinite(y)||x<0||y<0||x>=this.width||y>=this.height){
      this.targetLoading=false;this.status('Choose coordinates inside the map.');this.controls();return;
    }
    this.targetLoading=true;this.controls();this.status('Inspecting current target notes…');
    try{
      const result=await LGApi.post(`/api/maps/${this.mapId}/room-at`,{x,y});
      if(generation!==this.targetGeneration)return;
      const target=this.checkRoom(result);
      this.target=target;this.point={x,y};this.blocked=false;this.renderTarget();
      this.status('Target inspected. Review its saved content before recovery.');
    }catch(error){if(generation===this.targetGeneration)this.status(error.message);}
    finally{if(generation===this.targetGeneration){this.targetLoading=false;this.controls();}}
  }
  async recover(){
    if(this.busy||this.loading||this.targetLoading||this.blocked||!this.selected||!this.target||!this.point)return;
    const archive=this.selected,target={...this.target},point={...this.point};
    const overwrite=Boolean(target.name||target.markdown);
    if(overwrite&&!this.$('replace').checked){
      this.status('Check replacement confirmation after reviewing the target notes.');return;
    }
    const message=`Recover retained note ${JSON.stringify(archive.name)} into ${JSON.stringify(target.name||'Unnamed room')} at (${point.x}, ${point.y})? `+
      (overwrite?'The current saved name and notes will be archived before replacement. ':'')+
      'The source archive is retained. Unsaved editor drafts in other tabs are not applied and may become stale.';
    if(!confirm(message))return;
    const request={...point,area_key:target.area_key,revision:target.revision,
      cache_token:target.cache_token,walls_version:target.walls_version,
      room_notes_version:target.room_notes_version,overwrite};
    this.busy=true;++this.targetGeneration;this.controls();this.status('Recovering notes…');
    try{
      const result=await LGApi.post(`/api/maps/${this.mapId}/room-note-archives/${archive.id}/recover`,request);
      const recovered=this.checkRoom(result);
      this.target=recovered;this.blocked=false;this.renderTarget();
      this.status('Recovered. Source archive retained. Refresh the list to inspect any replacement archive.');
    }catch(error){
      this.blocked=true;
      this.status(error.message+' Recovery was not acknowledged. Selections are retained; inspect the target again before another attempt.');
    }finally{this.busy=false;this.controls();}
  }
};
const roomRecoveryRoot=document.getElementById('room-recovery');
if(roomRecoveryRoot)new window.LGRoomRecoveryPage(roomRecoveryRoot);
