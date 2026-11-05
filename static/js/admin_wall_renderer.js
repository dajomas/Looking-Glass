// Calibration fields and wall SVG rendering for the DM fog editor.
window.LGAdminWallRenderer = function (options) {
  "use strict";
  const {$, svg, pz, hiddenTypes, getState, getRawWalls, updateWallWidth} = options;
  function cal() {
    return {
      offset_x: parseFloat($("cal-ox").value) || 0,
      offset_y: parseFloat($("cal-oy").value) || 0,
      scale_x: parseFloat($("cal-sx").value) || 1,
      scale_y: parseFloat($("cal-sy").value) || 1,
      doors_block: $("cal-doors").checked,
    };
  }

  function fillCalibration(c) {
    $("cal-ox").value = +c.offset_x.toFixed(4);
    $("cal-oy").value = +c.offset_y.toFixed(4);
    $("cal-sx").value = +c.scale_x.toFixed(6);
    $("cal-sy").value = +c.scale_y.toFixed(6);
    $("cal-doors").checked = c.doors_block;
  }

  function renderWalls() {
    const state = getState(), rawWalls = getRawWalls();
    const c = cal();
    const paths = {};
    for (const [x1, y1, x2, y2, kind, blocks] of rawWalls) {
      if (hiddenTypes.has(kind)) continue;
      let k = kind;
      if (!blocks || (state?.disabled_wall_types || []).includes(kind) || (["door", "secret", "locked_door", "unlocked_door", "portal"].includes(kind) && !c.doors_block)) k = ["locked_door", "unlocked_door"].includes(kind) ? kind + " passive" : "passive";
      const a = (x1 - c.offset_x) * c.scale_x, b = (y1 - c.offset_y) * c.scale_y;
      const d = (x2 - c.offset_x) * c.scale_x, e = (y2 - c.offset_y) * c.scale_y;
      (paths[k] ||= []).push(`M${a.toFixed(1)} ${b.toFixed(1)}L${d.toFixed(1)} ${e.toFixed(1)}`);
    }
    svg.innerHTML = Object.entries(paths)
      .map(([k, segs]) => `<path class="w-${k}" d="${segs.join("")}"/>`).join("");
    for (const p of state?.portal_styles || []) {
      if (hiddenTypes.has("portal")) continue;
      const dx=p.x2-p.x1,dy=p.y2-p.y1,len=Math.hypot(dx,dy)||1;
      p.sides.forEach((side,i)=>{
        if(side.role==="none")return;
        const sign=i===0?-1:1,offset=2/pz.scale;
        const path=document.createElementNS(svg.namespaceURI,"path");
        const kind=["entry","both"].includes(side.role)?side.kind:"door";
        path.setAttribute("class",`portal-side p-${kind}`);
        path.setAttribute("d",`M${p.x1-sign*dy/len*offset} ${p.y1+sign*dx/len*offset}L${p.x2-sign*dy/len*offset} ${p.y2+sign*dx/len*offset}`);
        svg.appendChild(path);
      });
    }
    updateWallWidth();
  }

  return {cal, fillCalibration, renderWalls};
};
