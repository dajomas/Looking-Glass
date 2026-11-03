// Run from the repository root: node python/tests/test_wall_appearance.js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("static/js/wall_appearance.js", "utf8");
function setup(storage = new Map(), blocked = false) {
  const input = { value: "2", addEventListener(name, fn) { this[name] = fn; } };
  const output = {};
  const context = { window: {}, document: { getElementById: id => id === "wall-width" ? input : output },
    localStorage: { getItem(key) { if (blocked) throw Error("blocked"); return storage.get(key) ?? null; },
      setItem(key, value) { if (blocked) throw Error("blocked"); storage.set(key, value); } } };
  vm.runInNewContext(source, context);
  let current;
  const pref = context.window.LGWallAppearance(42, width => current = width);
  return { input, output, pref, current: () => current };
}
const storage = new Map();
let ui = setup(storage);
assert.equal(ui.current(), 2);
assert.equal(ui.output.textContent, "2 px");
for (const value of [0.5, 4, 10]) {
  ui.input.value = String(value); ui.input.input();
  assert.equal(ui.current(), value);
  assert.equal(ui.pref.width, value);
  assert.equal(setup(storage).current(), value);
}
for (const value of ["0", "-1", "99", "NaN", "Infinity"]) {
  storage.set("lg:wall-width:42", value);
  assert.equal(setup(storage).current(), 2);
}
ui = setup(new Map(), true);
ui.input.value = "3.5"; ui.input.input();
assert.equal(ui.current(), 3.5);
assert.equal(ui.output.textContent, "3.5 px");
ui.input.value = "nope"; ui.input.input();
assert.equal(ui.current(), 3.5);
console.log("Wall appearance tests passed");
