import assert from "node:assert/strict";
import { test } from "node:test";

import { align, byLabels, reshape } from "../src/bt/curves.ts";

test("raw and bucketed run curves", () => {
  const out = reshape({
    curves: [
      { run: "r1", name: "a", metric: "loss", raw: true, x: [0, 1], y: [2, 1] },
      { run: "r2", name: "a", metric: "loss", raw: false, x: [0, 10], first: [0, 10],
        min: [1, 0.5], max: [3, 1], last: [2, 0.7], count: [10, 10] },
    ],
  });
  assert.equal(out.aggregated, false);
  assert.deepEqual(out.curves.map((c) => c.label), ["a (r1)", "a (r2)"]);
  assert.deepEqual(out.curves[1].y, [2, 0.7]);
  assert.deepEqual(out.curves[1].lo, [1, 0.5]);
  assert.equal(out.curves[0].lo, null);
});

test("aggregated curves are labelled by what differs", () => {
  assert.deepEqual(
    byLabels([{ "config.lr": 0.001, "config.model": "r18" }, { "config.lr": 0.0003, "config.model": "r18" }]),
    ["lr=0.001", "lr=0.0003"],
  );
  const out = reshape({ curves: [{ by: { "config.lr": 1 }, runs: ["a"], metric: "m", x: [0], mean: [1], lo: [0], hi: [2], n: [3] }] });
  assert.equal(out.curves[0].label, "lr=1");
  assert.equal(out.aggregated, true);
  assert.equal(out.curves[0].run, null);
});

test("log scale drops non-positive values", () => {
  const out = reshape({ curves: [{ run: "r", name: "n", metric: "m", raw: true, x: [0, 1], y: [0, 1] }] }, { log: true });
  assert.deepEqual(out.curves[0].y, [null, 1]);
});

test("curves align on the union of their x values", () => {
  const { curves } = reshape({
    curves: [
      { run: "a", name: "a", metric: "m", raw: true, x: [0, 2, 4], y: [1, 2, 3] },
      { run: "b", name: "b", metric: "m", raw: true, x: [1, 2], y: [5, 6] },
    ],
  });
  const al = align(curves);
  assert.deepEqual(al.x, [0, 1, 2, 4]);
  assert.deepEqual(al.y, [[1, null, 2, 3], [null, 5, 6, null]]);
  assert.deepEqual(al.lo[0], [null, null, null, null]);
});
