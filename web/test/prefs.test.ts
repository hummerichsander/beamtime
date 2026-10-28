import assert from "node:assert/strict";
import { test } from "node:test";

import { effective, prefsOf, setChart, setView, toggleRun } from "../src/bt/prefs.ts";

test("a chart's own settings win over the view's, which win over the defaults", () => {
  setView("g", { smooth: 0.6, x: "_t" });
  setChart("g", "c1", { smooth: 0.9 });
  const p = prefsOf("g").value;
  const e = effective({ scale: "log" }, p, "c1");
  assert.equal(e.smooth, 0.9);
  assert.equal(e.x, "_t");
  assert.equal(e.scale, "log");
  assert.equal(effective({}, p, "c2").smooth, 0.6);
  setChart("g", "c1", null);
  assert.equal(effective({}, prefsOf("g").value, "c1").smooth, 0.6);
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
