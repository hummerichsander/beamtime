import assert from "node:assert/strict";
import { test } from "node:test";

import { fieldTitle, xTitle, yTitle } from "../src/bt/axes.ts";

const metrics = { "val/loss": { label: "Validation loss", unit: "nats" }, "val/acc": {} };

test("x is a clock by name or a metric by label", () => {
  assert.deepEqual(["_step", "epoch", "_t", "_elapsed"].map((x) => xTitle(x, metrics)), ["step", "epoch", "wall time", "elapsed"]);
  assert.equal(xTitle("val/loss", metrics), "Validation loss (nats)");
  assert.equal(xTitle("grad_norm", metrics), "grad_norm");
});

test("y is one metric, the path several share, or nothing", () => {
  assert.equal(yTitle(["val/loss"], metrics), "Validation loss (nats)");
  assert.equal(yTitle(["val/loss", "val/acc"], metrics), "val");
  assert.equal(yTitle(["a/b/x", "a/b/y"], metrics), "a/b");
  assert.equal(yTitle(["a/b/x", "a/c/y"], metrics), "a");
  assert.equal(yTitle(["val/loss", "train/loss"], metrics), "");
  assert.equal(yTitle(["loss", "acc"], metrics), "");
});

test("run fields read as their label, metrics with the view's name and unit", () => {
  assert.equal(fieldTitle("config.lr", metrics), "lr");
  assert.equal(fieldTitle("metric.val/acc.min", metrics), "val/acc min");
  assert.equal(fieldTitle("metric.val/loss.last", metrics), "Validation loss (nats)");
  assert.equal(fieldTitle("metric.val/loss.min", metrics), "Validation loss min (nats)");
});
