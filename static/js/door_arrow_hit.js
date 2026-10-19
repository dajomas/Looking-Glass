// Exact alpha hit testing in displayed-map coordinates. No viewer write capability.
window.LGDoorArrowHit = class {
  constructor() { this.key = ""; this.pixels = null; }
  set(image, key) {
    const canvas = document.createElement("canvas");
    canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
    const ctx = canvas.getContext("2d", {willReadFrequently: true});
    ctx.drawImage(image, 0, 0);
    this.pixels = ctx.getImageData(0, 0, canvas.width, canvas.height);
    this.key = key;
  }
  at(x, y, state, key) {
    if (!state.door_arrows_enabled || key !== this.key || !this.pixels ||
        !Number.isFinite(x) || !Number.isFinite(y) ||
        x < 0 || y < 0 || x >= state.width || y >= state.height) return null;
    const px = Math.floor(x * this.pixels.width / state.width);
    const py = Math.floor(y * this.pixels.height / state.height);
    if (!this.pixels.data[(py * this.pixels.width + px) * 4 + 3]) return null;
    return {x: (px + 0.5) / state.work_scale, y: (py + 0.5) / state.work_scale};
  }
};
