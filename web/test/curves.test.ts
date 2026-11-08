import assert from "node:assert/strict";
import { test } from "node:test";

import { align, byLabels, logDomain, markers, nearest, reshape } from "../src/bt/curves.ts";

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

test("debiased EMA keeps the first value and gaps", async () => {
  const { ema } = await import("../src/bt/curves.ts");
  assert.deepEqual(ema([1, 2, 3], 0), [1, 2, 3]);
  const out = ema([1, null, 1, 1], 0.9);
  assert.equal(out[0], 1);
  assert.equal(out[1], null);
  assert.ok(Math.abs((out[3] as number) - 1) < 1e-9);
  const step = ema([0, 0, 0, 10, 10, 10], 0.5) as number[];
  assert.ok(step[3] > 0 && step[3] < 10 && step[5] > step[4]);
});

test("robust range ignores a diverging run", async () => {
  const { robustRange } = await import("../src/bt/curves.ts");
  const calm = Array.from({ length: 200 }, (_, i) => 1 + (i % 10) / 10);
  const spike = [...calm.slice(0, 198), 266, 300];
  const [lo, hi] = robustRange([spike])!;
  assert.ok(lo < 1 && hi < 3, `${lo} ${hi}`);
  assert.equal(robustRange([[1, 2]]), null);
});

test("smoothing smooths the band with the curve", async () => {
  const { smooth } = await import("../src/bt/curves.ts");
  const c = reshape({ curves: [{ by: { "config.lr": 1 }, runs: ["a", "b"], metric: "m", x: [0, 1, 2], mean: [0, 10, 0], lo: [0, 8, 0], hi: [0, 12, 0], n: [2, 2, 2] }] });
  const out = smooth(c, 0.5).curves[0];
  assert.ok(out.lo![2]! > 0 && out.hi![2]! > out.y[2]!, "the band follows the smoothed mean");
  assert.deepEqual(out.runs, ["a", "b"]);
  assert.equal(out.group, "lr=1");
});

test("log ranges pad around the data instead of rounding to decades", async () => {
  const { logRange } = await import("../src/bt/curves.ts");
  const [lo, hi] = logRange(0.3, 0.93);
  assert.ok(lo < 0.3 && lo > 0.2 && hi > 0.93 && hi < 1, `${lo} ${hi}`);
});

test("log ticks fit the range", async () => {
  const { logTicks } = await import("../src/bt/curves.ts");
  assert.deepEqual(logTicks(0.32, 0.75), [0.4, 0.5, 0.6, 0.7]);
  assert.deepEqual(logTicks(0.1, 1.5), [0.1, 0.2, 0.3, 0.5, 1]);
  assert.deepEqual(logTicks(0.001, 10), [0.001, 0.01, 0.1, 1, 10]);
});

test("sparse curves mark every finite point, dense ones none", () => {
  const series = (n: number) => Array.from({ length: n }, (_, i) => i);
  assert.deepEqual(markers([]), []);
  assert.deepEqual(markers([null, 3, null]), [1]);
  assert.deepEqual(markers([1, 2]), [0, 1]);
  assert.deepEqual(markers([NaN, 1, Infinity, 2, null]), [1, 3]);
  assert.equal(markers(series(30)).length, 30);
  assert.deepEqual(markers(series(31)), []);
  // gaps in the aligned data don't count: 31 slots, 3 values.
  assert.deepEqual(markers(series(31).map((i) => (i % 15 === 0 ? i : null))), [0, 15, 30]);
});

const aggregated = (mean: (number | null)[], lo: number[], hi: number[]) => ({
  curves: [{ metric: "m", by: { "config.arm": "a" }, runs: ["r1", "r2"], x: mean.map((_, i) => i), mean, lo, hi, n: mean.map(() => 3) }],
});

test("a band clips at the floor on a log axis instead of leaving holes", () => {
  // mean − std is not positive at the second point; the floor is the smallest positive mean ÷ √10.
  const { curves } = reshape(aggregated([1, 0.5, 2], [0.5, -0.1, 1.5], [1.5, 1.1, 2.5]), { log: true });
  const floor = 0.5 / Math.sqrt(10);
  assert.deepEqual(curves[0].y, [1, 0.5, 2]);
  assert.deepEqual(curves[0].lo, [0.5, floor, 1.5]);
  assert.deepEqual(curves[0].hi, [1.5, 1.1, 2.5]);
});

test("a min of zero clips too, and a band exists exactly where the curve does", () => {
  const raw = { curves: [{ run: "r", metric: "m", x: [0, 1, 2], last: [1, 0, 4], min: [0, 0, 2], max: [2, 0, 5], count: [3, 3, 3] }] };
  const { curves } = reshape(raw, { log: true });
  assert.deepEqual(curves[0].y, [1, null, 4]);
  assert.deepEqual(curves[0].lo, [1 / Math.sqrt(10), null, 2]);
  assert.deepEqual(curves[0].hi, [2, null, 5]);
});

test("all-zero curves have no curve and no band", () => {
  const raw = { curves: [{ run: "r", metric: "m", x: [0, 1], last: [0, 0], min: [0, 0], max: [0, 0], count: [1, 1] }] };
  const { curves } = reshape(raw, { log: true });
  assert.deepEqual([curves[0].y, curves[0].lo, curves[0].hi], [[null, null], [null, null], [null, null]]);
  assert.equal(logDomain(curves), null);
});

test("symlog and linear axes keep the band as it is", () => {
  const { curves } = reshape(aggregated([1, 0.5, 2], [0.5, -0.1, 1.5], [1.5, 1.1, 2.5]));
  assert.deepEqual(curves[0].lo, [0.5, -0.1, 1.5]);
});

test("the log range follows the curves and the band edges above the floor, nothing clipped", () => {
  const { curves } = reshape(aggregated([1, 0.5, 2], [0.5, -0.1, 1.5], [1.5, 1.1, 2.5]), { log: true });
  // lo of 0.5 and 1.5 count, the clipped one does not; hi reaches 2.5.
  assert.deepEqual(logDomain(curves), [0.5, 2.5]);
  // a window leaves out the points outside it.
  assert.deepEqual(logDomain(curves, [1, 1]), [0.5, 1.1]);
});

test("the nearest point of a sorted x, with steps and duplicates", () => {
  assert.equal(nearest([], 3), -1);
  assert.equal(nearest([5], 100), 0);
  assert.equal(nearest([0, 10, 20], -4), 0);
  assert.equal(nearest([0, 10, 20], 4), 0);
  assert.equal(nearest([0, 10, 20], 6), 1);
  assert.equal(nearest([0, 10, 20], 99), 2);
  assert.ok([1, 2, 3].includes(nearest([0, 1, 1, 1, 2], 1)));
});

test("a curve is a path when x goes back, and keeps the steps its points were logged at", () => {
  const out = reshape({ curves: [
    { run: "r1", metric: "m", raw: true, x: [0, 2, 1], y: [1, 2, 3], monotone: false, step: [0, 10, 20] },
    { run: "r2", metric: "m", raw: true, x: [0, 1], y: [1, 2] },
  ] });
  assert.deepEqual(out.curves.map((c) => c.monotone), [false, true]);
  assert.deepEqual(out.curves.map((c) => c.step), [[0, 10, 20], null]);
});

test("where a resumed run's attempts meet comes with its curve", () => {
  const out = reshape({
    curves: [
      { run: "r1", name: "a", metric: "loss", raw: true, x: [0, 1], y: [2, 1], resumes: [1] },
      { run: "r2", name: "b", metric: "loss", raw: true, x: [0, 1], y: [2, 1] },
    ],
  });
  assert.deepEqual(out.curves.map((c) => c.resumes), [[1], []]);
});
