import assert from "node:assert/strict";
import { test } from "node:test";

import { importanceBars as bars, signed } from "../src/bt/shapes.ts";

const rows = [
  { field: "config.opt", spearman: null, eta_squared: 0.62, n: 12 },
  { field: "config.lr", spearman: -0.8, eta_squared: 0.4, n: 12 },
  { field: "config.wd", spearman: 0.1, eta_squared: 0.02, n: 7 },
];

test("a negative correlation draws as magnitude and keeps its sign in the text", () => {
  const [, lr] = bars(rows);
  assert.equal(lr.rhoFraction, 0.8);
  assert.equal(signed(lr.rho), "−0.80");
  assert.equal(signed(0.1), "0.10");
});

test("bars keep the answer's order and each row's own run count", () => {
  const out = bars(rows);
  assert.deepEqual(out.map((b) => b.field), ["config.opt", "config.lr", "config.wd"]);
  assert.deepEqual(out.map((b) => b.n), [12, 12, 7]);
});

test("a categorical field has no correlation bar, only variance explained", () => {
  const [opt] = bars(rows);
  assert.equal(opt.rho, null);
  assert.equal(opt.rhoFraction, 0);
  assert.equal(opt.etaFraction, 0.62);
  assert.equal(signed(opt.rho), "–");
});

test("one field gives one bar and no rows give none", () => {
  assert.equal(bars(rows.slice(0, 1)).length, 1);
  assert.deepEqual(bars([]), []);
});

test("fractions stay within the bar", () => {
  const [b] = bars([{ field: "config.x", spearman: 1.0000001, eta_squared: 1.2, n: 10 }]);
  assert.deepEqual([b.rhoFraction, b.etaFraction], [1, 1]);
});
