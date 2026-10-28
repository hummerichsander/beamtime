import assert from "node:assert/strict";
import { test } from "node:test";

import { ago, duration, label, step, value } from "../src/bt/fmt.ts";

test("values are compact", () => {
  assert.equal(value(3e-4), "3e-4");
  assert.equal(value(0.000312), "3.1e-4");
  assert.equal(value(0.93125), "0.9313");
  assert.equal(value(12), "12");
  assert.equal(value(12400), "12.4k");
  assert.equal(value(2_500_000), "2.5M");
  assert.equal(value(1.5), "1.5");
  assert.equal(value(null), "–");
  assert.equal(value(NaN), "NaN");
  assert.equal(value("adam"), "adam");
});

test("steps, durations and times", () => {
  assert.equal(step(12400), "12.4k");
  assert.equal(step(999), "999");
  assert.equal(duration(42), "42s");
  assert.equal(duration(185), "3m 5s");
  assert.equal(duration(4 * 3600 + 12 * 60), "4h 12m");
  const now = Date.parse("2026-10-28T12:00:00Z");
  assert.equal(ago("2026-10-28T10:00:00Z", now), "2 h ago");
  assert.equal(ago("2026-09-01T10:00:00Z", now), "2026-09-01");
});

test("labels drop prefixes", () => {
  assert.equal(label("metric.val/acc.max"), "val/acc max");
  assert.equal(label("metric.val/acc.last"), "val/acc");
  assert.equal(label("config.lr"), "lr");
  assert.equal(label("run.status"), "status");
  assert.equal(label("run.created_at"), "started");
});

test("metric direction from the name", async () => {
  const { lowerIsBetter } = await import("../src/bt/fmt.ts");
  assert.equal(lowerIsBetter("metric.train/loss.last"), true);
  assert.equal(lowerIsBetter("metric.val/acc.max"), false);
  assert.equal(lowerIsBetter("val/ppl"), true);
});
