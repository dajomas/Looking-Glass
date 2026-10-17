// Pan & zoom for a fixed-size "stage" element inside a viewport.
// Pointer events: drag to pan (mouse, pen, touch), two-finger pinch, wheel zoom.
// A press/release without movement fires onTap(imageX, imageY, event).
window.PanZoom = class PanZoom {
  constructor(viewport, stage, opts = {}) {
    this.vp = viewport;
    this.stage = stage;
    this.w = 1; this.h = 1;
    this.scale = 1; this.x = 0; this.y = 0;
    this.minScale = 0.02; this.maxScale = 8;
    this.onTap = opts.onTap || null;
    this.onChange = opts.onChange || null;
    this.tapTolerance = 5;
    this.pointers = new Map();
    this.spaceDown = false;
    this._bind();
  }

  setContentSize(w, h) {
    this.w = w; this.h = h;
    this.stage.style.width = w + "px";
    this.stage.style.height = h + "px";
  }

  apply() {
    this.stage.style.transform = `translate(${this.x}px, ${this.y}px) scale(${this.scale})`;
    if (this.onChange) this.onChange(this);
  }

  fit(margin = 0.98) {
    const r = this.vp.getBoundingClientRect();
    if (!r.width || !r.height) return;
    this.scale = Math.min(r.width / this.w, r.height / this.h) * margin;
    this.x = (r.width - this.w * this.scale) / 2;
    this.y = (r.height - this.h * this.scale) / 2;
    this.apply();
  }

  zoomAt(factor, cx, cy) {
    const r = this.vp.getBoundingClientRect();
    const px = cx - r.left, py = cy - r.top;
    const ns = Math.min(this.maxScale, Math.max(this.minScale, this.scale * factor));
    const k = ns / this.scale;
    this.x = px - (px - this.x) * k;
    this.y = py - (py - this.y) * k;
    this.scale = ns;
    this.apply();
  }

  zoomCenter(factor) {
    const r = this.vp.getBoundingClientRect();
    this.zoomAt(factor, r.left + r.width / 2, r.top + r.height / 2);
  }

  toImage(clientX, clientY) {
    const r = this.vp.getBoundingClientRect();
    return { x: (clientX - r.left - this.x) / this.scale, y: (clientY - r.top - this.y) / this.scale };
  }

  _bind() {
    const vp = this.vp;
    vp.addEventListener("wheel", (e) => {
      e.preventDefault();
      const f = Math.exp(-e.deltaY * (e.ctrlKey ? 0.01 : 0.0015));
      this.zoomAt(f, e.clientX, e.clientY);
    }, { passive: false });
    vp.addEventListener("contextmenu", (e) => e.preventDefault());

    vp.addEventListener("pointerdown", (e) => {
      vp.setPointerCapture(e.pointerId);
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY, sx: e.clientX, sy: e.clientY, button: e.button });
      this.moved = this.pointers.size > 1 || e.button === 2 || e.button === 1 || this.spaceDown;
      if (this.pointers.size === 2) this._pinchStart = this._pinchInfo();
    });
    vp.addEventListener("pointermove", (e) => {
      const p = this.pointers.get(e.pointerId);
      if (!p) return;
      if (this.pointers.size === 2) {
        p.x = e.clientX; p.y = e.clientY;
        const now = this._pinchInfo();
        if (this._pinchStart) {
          this.zoomAt(now.dist / this._pinchStart.dist, now.cx, now.cy);
          this.x += now.cx - this._pinchStart.cx;
          this.y += now.cy - this._pinchStart.cy;
          this.apply();
        }
        this._pinchStart = now;
        this.moved = true;
        return;
      }
      const dx = e.clientX - p.x, dy = e.clientY - p.y;
      if (Math.hypot(e.clientX - p.sx, e.clientY - p.sy) > this.tapTolerance) this.moved = true;
      if (this.moved) {
        this.x += dx; this.y += dy;
        this.apply();
        vp.classList.add("panning");
      }
      p.x = e.clientX; p.y = e.clientY;
    });
    const end = (e) => {
      const p = this.pointers.get(e.pointerId);
      if (!p) return;
      this.pointers.delete(e.pointerId);
      vp.classList.remove("panning");
      if (this.pointers.size < 2) this._pinchStart = null;
      if (e.type === "pointerup" && !this.moved && p.button === 0 && this.pointers.size === 0 && this.onTap) {
        const pt = this.toImage(e.clientX, e.clientY);
        this.onTap(pt.x, pt.y, e);
      }
    };
    vp.addEventListener("pointerup", end);
    vp.addEventListener("pointercancel", end);

    window.addEventListener("keydown", (e) => {
      if (e.code === "Space" && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) {
        this.spaceDown = true; vp.classList.add("grab"); e.preventDefault();
      }
    });
    window.addEventListener("keyup", (e) => {
      if (e.code === "Space") { this.spaceDown = false; vp.classList.remove("grab"); }
    });
    window.addEventListener("resize", () => this._onResize());
  }

  _onResize() {
    if (this._resizeT) clearTimeout(this._resizeT);
    this._resizeT = setTimeout(() => this.fit(), 120);
  }

  _pinchInfo() {
    const [a, b] = [...this.pointers.values()];
    return { dist: Math.max(1, Math.hypot(a.x - b.x, a.y - b.y)), cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2 };
  }
};
