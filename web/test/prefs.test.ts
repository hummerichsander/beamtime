import assert from "node:assert/strict";
import { test } from "node:test";

import { effective } from "../src/bt/chart-settings.ts";
import type { Node } from "../src/bt/index.ts";
import { changed, prefsOf, setChart, setView, toggleRun } from "../src/bt/prefs.ts";

const line = (id: string, props: Record<string, unknown> = {}, params: Record<string, unknown> = {}): Node => ({
  block: "line",
  id,
  props: { y: "loss", ...props },
  data: { main: { method: "series", params } },
});

test("a chart's own settings win over its node's defaults", () => {
  setChart("g", "c1", { smooth: 0.9, scale: "symlog", ymin: 0 });
  const p = prefsOf("g").value;
  const e = effective(line("c1", { scale: "log", smooth: 0.2 }), p);
  assert.deepEqual([e.smooth, e.scale, e.ymin, e.x, e.raw, e.legend], [0.9, "symlog", 0, "_step", true, true]);
  assert.equal(effective(line("c2", { smooth: 0.2 }), p).smooth, 0.2);
  assert.ok(changed(p));
  setChart("g", "c1", null);
  assert.equal(effective(line("c1"), prefsOf("g").value).smooth, 0);
  assert.ok(!changed(prefsOf("g").value));
});

test("a page-wide setting sits between the node's defaults and a chart's own", () => {
  setChart("v", "c1", { x: "epoch", smooth: 0.5 });
  setChart("v", "c2", { smooth: 0.1 });
  setView("v", { x: "sys/gpu_mem" });
  const p = prefsOf("v").value;
  assert.equal(effective(line("c3", { x: "_t" }), p).x, "sys/gpu_mem");
  assert.equal(effective(line("c1"), p).x, "sys/gpu_mem");
  assert.equal(effective(line("c1"), p).smooth, 0.5);
  assert.equal(effective(line("c2"), p).smooth, 0.1);
  setChart("v", "c2", { x: "_elapsed" });
  assert.equal(effective(line("c2"), prefsOf("v").value).x, "_elapsed");
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

test("a node's settings come from its props and its series call, and absent ones are the defaults", () => {
  const empty = prefsOf("n").value;
  const plain = effective(line("a"), empty);
  assert.deepEqual([plain.x, plain.band, plain.scale, plain.by, plain.steps, plain.smooth], ["_step", "minmax", "linear", null, null, 0]);
  const e = effective(line("b", { scale: "log", x: "epoch" }, { seeds: "config.seed", band: "std", steps: [0, 5] }), empty);
  assert.deepEqual([e.scale, e.x, e.by, e.band, e.steps], ["log", "epoch", "seeds", "std", [0, 5]]);
  assert.equal(effective(line("c", {}, { by: ["config.lr"] }), empty).by, "config.lr");
});
