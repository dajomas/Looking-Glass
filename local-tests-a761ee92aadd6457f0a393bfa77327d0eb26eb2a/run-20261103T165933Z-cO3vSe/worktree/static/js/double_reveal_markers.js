/* DM-only decorations. Never mounted in the viewer or used for hit testing. */
(function () {
  "use strict";
  window.LGDoubleRevealMarkers = class {
    constructor(layer, legend) { this.layer=layer; this.legend=legend; this.key=""; }
    draw(data, enabled, scale=1) {
      if (!this.layer || !this.legend) return;
      const rooms=enabled && data?.image_revision ? data.rooms.filter(r=>r.revision && r.valid_geometry && (!r.true_active || r.destination_map_id)) : [];
      this.layer.hidden=this.legend.hidden=!rooms.length;
      this.layer.style.setProperty("--double-marker-scale", String(1/Math.max(.001,scale)));
      const key=JSON.stringify(rooms.map(r=>[r.area_key,r.x,r.y,r.true_active,r.destination_map_id,r.revealed,r.name,r.destination_name,data.active_map_id]));
      if (key===this.key) return;
      this.key=key;
      this.layer.replaceChildren();
      for (const room of rooms) {
        const marker=document.createElement("span"), travel=!!room.true_active;
        marker.className="double-fog-marker " + (travel ? "double-fog-travel" : "double-fog-reveal");
        marker.textContent=travel ? "↗" : "2";
        marker.style.left=`${room.x}px`;marker.style.top=`${room.y}px`;
        this.layer.append(marker);
      }
      this.legend.textContent="Ctrl + left-click room: 2 = reveal true artwork; ↗ = destination (confirmation).";
    }
  };
})();
