import assert from "node:assert/strict";
import { test } from "node:test";

import { diffLines, fold } from "../src/bt/diff.ts";
import { bars, extent, fit, histograms, logSplits, points, tableOf } from "../src/bt/shapes.ts";

const runs = {
  columns: ["run.id", "config.lr", "metric.acc.max", "config.opt"],
  rows: [
    ["a", 0.1, 0.5, "sgd"],
    ["b", 0.01, 0.8, "sgd"],
    ["c", 0.001, 0.7, "adam"],
    ["d", 0.001, null, "adam"],
  ],
};

test("scatter points skip missing values and read seed means", () => {
  const pts = points(runs, "config.lr", "metric.acc.max", "config.opt");
  assert.deepEqual(pts.map((p) => p.key), ["a", "b", "c"]);
  assert.equal(pts[2].color, "adam");
  const seeds = { columns: ["runs", "config.lr", "metric.acc.max"], rows: [[["x", "y"], 0.1, { mean: 0.6, std: 0.1, n: 2 }]] };
  const [p] = points(seeds, "config.lr", "metric.acc.max");
  assert.deepEqual([p.key, p.y, p.err, p.n, p.runs], ["x", 0.6, 0.1, 2, ["x", "y"]]);
});

test("fits recover lines in their space", () => {
  const mk = (xs: number[], f: (x: number) => number) => xs.map((x) => ({ key: "", runs: [], x, y: f(x), err: null, color: null, n: 1 }));
  assert.ok(Math.abs(fit(mk([1, 2, 3], (x) => 2 * x + 1), "linear")!(4) - 9) < 1e-9);
  assert.ok(Math.abs(fit(mk([1, 10, 100], (x) => 3 * x ** -0.5), "power")!(1000) - 3 * 1000 ** -0.5) < 1e-9);
  assert.ok(Math.abs(fit(mk([1, 10, 100], (x) => 1 + Math.log(x)), "log")!(1000) - (1 + Math.log(1000))) < 1e-9);
  assert.equal(fit(mk([1], (x) => x), "linear"), null);
});

test("bars average per category with error bars, grouped and sorted", () => {
  const b = bars(runs, "config.opt", "metric.acc.max", null, "minmax", "x");
  assert.deepEqual(b.map((x) => [x.label, x.value, x.lo, x.hi, x.n]), [["adam", 0.7, 0.7, 0.7, 1], ["sgd", 0.65, 0.5, 0.8, 2]]);
  const sorted = bars(runs, "config.opt", "metric.acc.max", null, "std", "-y");
  assert.deepEqual(sorted.map((x) => x.label), ["adam", "sgd"]);
  const grouped = bars(runs, "config.opt", "metric.acc.max", "config.lr", "none", "x");
  assert.equal(grouped.length, 3);
  assert.deepEqual(grouped.map((x) => x.group), ["0.001", "0.01", "0.1"]);
});

test("histograms keep tables with bins; tables come from columns or answers", () => {
  const entries = [
    { run: "a", step: 3, columns: { bin_start: [0, 1], bin_end: [1, 2], count: [4, 5] } },
    { run: "b", step: 3, columns: { class: ["x"], acc: [1] } },
  ];
  assert.deepEqual(histograms({ entries }).map((h) => h.run), ["a"]);
  assert.deepEqual(tableOf(entries[1]), { columns: ["class", "acc"], rows: [["x", 1]] });
  assert.deepEqual(tableOf({ columns: ["a"], rows: [[1]] }), { columns: ["a"], rows: [[1]] });
  assert.equal(tableOf({ path: "x.parquet" }), null);
});

test("extents pad linear axes and round log axes to decades", () => {
  const [a, b] = extent([0.003, 0.2], true)!;
  assert.ok(a < 0.003 && a > 0.001 && b > 0.2 && b < 1);
  assert.deepEqual(logSplits([0.0009, 0.3]), [0.001, 0.01, 0.1]);
  assert.deepEqual(logSplits([0.9, 30]), [1, 2, 5, 10, 20]);
  const [lo, hi] = extent([0, 10], false)!;
  assert.ok(lo < 0 && hi > 10);
  assert.equal(extent([], false), null);
});

test("line diffs mark changes and fold long unchanged runs", () => {
  const a = "a\nb\nc\nd\ne\nf\ng\nh\ni";
  const b = "a\nb\nc\nd\nX\nf\ng\nh\ni\nj";
  const d = diffLines(a, b);
  assert.deepEqual(d.filter((l) => l.kind !== "same").map((l) => `${l.kind} ${l.text}`), ["removed e", "added X", "added j"]);
  const f = fold(d, 1);
  assert.ok(f.some((l) => l.kind === "skip"));
});

test("time ticks pick a round step", async () => {
  const { timeTicks } = await import("../src/bt/shapes.ts");
  const { at, step } = timeTicks(0, 3 * 3600);
  assert.equal(step, 1800);
  assert.ok(at.every((t) => t % 1800 === 0) && at.length >= 5 && at.length <= 7);
  assert.equal(timeTicks(0, 30 * 86400).step, 7 * 86400);
});
