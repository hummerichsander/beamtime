import assert from "node:assert/strict";
import { test } from "node:test";

import { fill, placeholders, READS, ResizeGuard } from "../src/kit/protocol.ts";
import { shape } from "../src/kit/shape.ts";

test("placeholders are whole strings, found anywhere in the params", () => {
  const params = { from: "$run", y: ["$metric", "val/acc"], where: { x: "$5 off" } };
  assert.deepEqual([...placeholders(params)].sort(), ["metric", "run"]);
  const call = { method: "series", params, scope: "g" };
  const filled = fill(call, { run: "r1" });
  assert.deepEqual(filled.params, { from: "r1", y: ["$metric", "val/acc"], where: { x: "$5 off" } });
  assert.deepEqual(call.params.from, "$run");
});

test("frames may only read", () => {
  assert.ok(READS.has("runs") && READS.has("series"));
  for (const write of ["note_add", "view_save", "set", "note_rm", "memory_update"]) assert.ok(!READS.has(write));
});

test("a block that keeps resizing is frozen", () => {
  const guard = new ResizeGuard(3, 1000);
  assert.ok(guard.accept(0) && guard.accept(100) && guard.accept(200));
  assert.equal(guard.accept(300), false);
  assert.ok(guard.frozen);
  assert.equal(guard.accept(5000), false);
  const calm = new ResizeGuard(3, 1000);
  for (const t of [0, 600, 1200, 1800, 2400]) assert.ok(calm.accept(t));
});

test("results as blocks see them", () => {
  const call = { method: "runs", params: {}, scope: "g" };
  const runs = shape({ status: "ready", data: { columns: ["run.id", "config.lr"], rows: [["a", 0.1]] }, error: null, refreshing: false }, call);
  assert.deepEqual(runs.rows, [{ "run.id": "a", "config.lr": 0.1 }]);
  assert.equal(runs.call, call);
  const curves = shape({ status: "ready", data: { curves: [
    { run: "a", metric: "loss", raw: true, x: [0, 1], y: [2, 1] },
    { metric: "loss", by: { "config.lr": 0.1 }, x: [0], mean: [1], lo: [0.5], hi: [1.5], n: [3] },
  ] }, error: null, refreshing: false }, null);  // prettier-ignore
  assert.deepEqual(curves.curves[0], { run: "a", key: "loss", group: null, x: [0, 1], y: [2, 1] });
  assert.deepEqual(curves.curves[1], { run: null, key: "loss", group: { "config.lr": 0.1 }, x: [0], min: [0.5], max: [1.5], mean: [1], count: [3] });
  const loading = shape({ status: "loading", data: null, error: null, refreshing: false }, null);
  assert.deepEqual([loading.rows, loading.curves, loading.columns], [[], [], []]);
});
