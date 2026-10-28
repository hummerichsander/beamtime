import assert from "node:assert/strict";
import { test } from "node:test";

import { groupLabels, reshape } from "../src/bt/curves.ts";

test("raw and bucketed run curves become points", () => {
  const out = reshape({
    curves: [
      { run: "r1", name: "a", metric: "loss", raw: true, x: [0, 1], y: [2, 1] },
      { run: "r2", name: "a", metric: "loss", raw: false, x: [0, 10], first: [0, 10],
        min: [1, 0.5], max: [3, 1], last: [2, 0.7], count: [10, 10] },
    ],
  });
  assert.equal(out.points.length, 4);
  assert.equal(out.grouped, false);
  assert.deepEqual(out.points[3], { key: "r2:loss", label: "a (r2)", run: "r2", x: 10, y: 0.7, lo: 0.5, hi: 1, n: 10 });
  assert.equal(out.points[0].label, "a (r1)");
});

test("grouped curves are labelled by what differs", () => {
  assert.deepEqual(
    groupLabels([{ "config.lr": 0.001, "config.model": "r18" }, { "config.lr": 0.0003, "config.model": "r18" }]),
    ["lr=0.001", "lr=0.0003"],
  );
  const out = reshape({ curves: [{ by: { "config.lr": 1 }, runs: ["a"], metric: "m", x: [0], mean: [1], lo: [0], hi: [2], n: [3] }] });
  assert.equal(out.points[0].label, "lr=1");
  assert.equal(out.grouped, true);
});

test("log scale drops non-positive values", () => {
  const out = reshape({ curves: [{ run: "r", name: "n", metric: "m", raw: true, x: [0, 1], y: [0, 1] }] }, { log: true });
  assert.equal(out.points[0].y, null);
  assert.equal(out.points[1].y, 1);
});
