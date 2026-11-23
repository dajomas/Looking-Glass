// Run from repository root: node --test python/tests/test_pan_zoom_drag.js
// I2: PanZoom's optional onDragStart hook lets the wall editor drag endpoints.
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function setup(opts = {}) {
  const listeners = new Map(), classes = new Set(), calls = [];
  const on = (map) => (type, fn) => { if (!map.has(type)) map.set(type, []); map.get(type).push(fn); };
  const vp = {
    addEventListener: on(listeners), setPointerCapture() {},
    getBoundingClientRect() { return {left: 0, top: 0, width: 800, height: 600}; },
    classList: {add: (c) => classes.add(c), remove: (c) => classes.delete(c), contains: (c) => classes.has(c)},
  };
  const stage = {style: {}};
  const context = {window: {addEventListener() {}}, document: {activeElement: {tagName: "BODY"}}, setTimeout, clearTimeout};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../../static/js/pan_zoom.js"), "utf8"), context);
  const handler = {
    move: (x, y) => calls.push(["move", x, y]), end: (x, y) => calls.push(["end", x, y]),
    cancel: () => calls.push(["cancel"]),
  };
  const pz = new context.window.PanZoom(vp, stage, {
    secondaryTap: true, onTap: (x, y) => calls.push(["tap", x, y]),
    ...(opts.drag === undefined ? {} : {onDragStart: (x, y, e) => { calls.push(["start", x, y]); return opts.drag(e) ? handler : null; }}),
  });
  const fire = (type, e) => (listeners.get(type) || []).forEach((fn) => fn({pointerId: 1, button: 0, pointerType: "mouse", ...e, type}));
  return {pz, fire, calls, classes};
}

test("without a hook a left drag pans as before", () => {
  const {pz, fire, calls} = setup();
  fire("pointerdown", {clientX: 100, clientY: 100});
  fire("pointermove", {clientX: 140, clientY: 120});
  fire("pointerup", {clientX: 140, clientY: 120});
  assert.equal(pz.x, 40); assert.equal(pz.y, 20);
  assert.deepEqual(calls, []);
});

test("a claimed press drags instead of panning and does not tap", () => {
  const {pz, fire, calls, classes} = setup({drag: () => true});
  fire("pointerdown", {clientX: 100, clientY: 100});
  fire("pointermove", {clientX: 102, clientY: 101});   // inside the tap tolerance
  assert.deepEqual(calls, [["start", 100, 100]]);
  fire("pointermove", {clientX: 130, clientY: 110});
  assert.ok(classes.has("dragging"));
  fire("pointerup", {clientX: 140, clientY: 120});
  assert.equal(pz.x, 0); assert.equal(pz.y, 0);
  assert.deepEqual(calls, [["start", 100, 100], ["move", 130, 110], ["end", 140, 120]]);
  assert.ok(!classes.has("dragging")); assert.equal(pz.drag, null);
});

test("a stationary claimed press is cancelled and stays a tap", () => {
  const {fire, calls} = setup({drag: () => true});
  fire("pointerdown", {clientX: 50, clientY: 60});
  fire("pointerup", {clientX: 51, clientY: 60});
  assert.deepEqual(calls, [["start", 50, 60], ["cancel"], ["tap", 51, 60]]);
});

test("an unclaimed press still pans", () => {
  const {pz, fire, calls} = setup({drag: () => false});
  fire("pointerdown", {clientX: 100, clientY: 100});
  fire("pointermove", {clientX: 160, clientY: 100});
  fire("pointerup", {clientX: 160, clientY: 100});
  assert.equal(pz.x, 60);
  assert.deepEqual(calls, [["start", 100, 100]]);
});

test("pointercancel and cancelDrag end a drag without end or tap", () => {
  for (const how of ["pointercancel", "cancelDrag"]) {
    const {pz, fire, calls} = setup({drag: () => true});
    fire("pointerdown", {clientX: 100, clientY: 100});
    fire("pointermove", {clientX: 130, clientY: 100});
    if (how === "cancelDrag") { assert.equal(pz.cancelDrag(), true); fire("pointerup", {clientX: 130, clientY: 100}); }
    else fire("pointercancel", {clientX: 130, clientY: 100});
    assert.deepEqual(calls.map((c) => c[0]), ["start", "move", "cancel"], how);
    assert.equal(pz.cancelDrag(), false);
  }
});

test("a second pointer cancels the drag and pinches", () => {
  const {pz, fire, calls} = setup({drag: () => true});
  fire("pointerdown", {clientX: 100, clientY: 100});
  fire("pointermove", {clientX: 130, clientY: 100});
  fire("pointerdown", {pointerId: 2, clientX: 300, clientY: 100});
  assert.deepEqual(calls.map((c) => c[0]), ["start", "move", "cancel"]);
  assert.equal(pz.drag, null);
});

test("middle-button presses pan and are never offered as a drag", () => {
  const {fire, calls} = setup({drag: () => true});
  fire("pointerdown", {clientX: 1, clientY: 1, button: 1}); fire("pointerup", {clientX: 1, clientY: 1, button: 1});
  assert.deepEqual(calls, []);
});
