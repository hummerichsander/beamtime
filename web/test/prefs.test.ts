import assert from "node:assert/strict";
import { test } from "node:test";

import { changed, effective, prefsOf, setChart, setView, toggleRun } from "../src/bt/prefs.ts";

test("a chart's own settings win over its node's defaults", () => {
  setChart("g", "c1", { smooth: 0.9, scale: "symlog", ymin: 0 });
  const p = prefsOf("g").value;
  const e = effective({ scale: "log", smooth: 0.2 }, p, "c1");
  assert.deepEqual([e.smooth, e.scale, e.ymin, e.x, e.raw, e.legend], [0.9, "symlog", 0, "_step", true, true]);
  assert.equal(effective({ smooth: 0.2 }, p, "c2").smooth, 0.2);
  assert.ok(changed(p));
  setChart("g", "c1", null);
  assert.equal(effective({}, prefsOf("g").value, "c1").smooth, 0);
  assert.ok(!changed(prefsOf("g").value));
});

test("a page-wide setting sits between the node's defaults and a chart's own", () => {
  setChart("v", "c1", { x: "epoch", smooth: 0.5 });
  setChart("v", "c2", { smooth: 0.1 });
  setView("v", { x: "sys/gpu_mem" });
  const p = prefsOf("v").value;
  assert.equal(effective({ x: "_t" }, p, "c3").x, "sys/gpu_mem");
  assert.equal(effective({}, p, "c1").x, "sys/gpu_mem");
  assert.equal(effective({}, p, "c1").smooth, 0.5);
  assert.equal(effective({}, p, "c2").smooth, 0.1);
  setChart("v", "c2", { x: "_elapsed" });
  assert.equal(effective({}, prefsOf("v").value, "c2").x, "_elapsed");
  setChart("v", "c1", null);
  setChart("v", "c2", null);
  assert.ok(changed(prefsOf("v").value));
});

test("runs hide, show, and solo", () => {
  const all = ["a", "b", "c"];
  toggleRun("h", "a", all);
  assert.deepEqual(prefsOf("h").value.hidden, ["a"]);
  toggleRun("h", "b", all, true);
  assert.deepEqual(prefsOf("h").value.hidden.sort(), ["a", "c"]);
  toggleRun("h", "b", all, true);
  assert.deepEqual(prefsOf("h").value.hidden, []);
});
