// DM-only overlay preference shared by the fog and wall editors for this map.
window.LGWallAppearance = function (mapId, onChange) {
  "use strict";
  const input = document.getElementById("wall-width");
  const output = document.getElementById("wall-width-value");
  const key = `lg:wall-width:${mapId}`;
  const valid = (value) => Number.isFinite(value) && value >= 0.5 && value <= 10;
  let width = 2;
  try {
    const stored = Number(localStorage.getItem(key));
    if (valid(stored)) width = stored;
  } catch (_) { /* Storage may be unavailable; keep the usable default. */ }
  function update() {
    input.value = String(width);
    output.textContent = `${width} px`;
    onChange(width);
  }
  input.addEventListener("input", () => {
    const next = Number(input.value);
    if (!valid(next)) return;
    width = next;
    try { localStorage.setItem(key, String(width)); } catch (_) {}
    update();
  });
  update();
  return { get width() { return width; } };
};
