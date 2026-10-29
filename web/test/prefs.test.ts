import assert from "node:assert/strict";
import { test } from "node:test";

import { changed, effective, prefsOf, setChart, toggleRun } from "../src/bt/prefs.ts";

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

test("runs hide, show, and solo", () => {
  const all = ["a", "b", "c"];
  toggleRun("h", "a", all);
  assert.deepEqual(prefsOf("h").value.hidden, ["a"]);
  toggleRun("h", "b", all, true);
  assert.deepEqual(prefsOf("h").value.hidden.sort(), ["a", "c"]);
  toggleRun("h", "b", all, true);
  assert.deepEqual(prefsOf("h").value.hidden, []);
});
