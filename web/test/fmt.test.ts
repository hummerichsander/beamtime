import assert from "node:assert/strict";
import { test } from "node:test";

import { ago, duration, full, label, segments, shortLabels, step, value } from "../src/bt/fmt.ts";

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

test("nested values are summarized, never [object Object]", () => {
  assert.equal(value({ a: 1, b: 2, c: 3 }), "{3 keys}");
  assert.equal(value({ a: 1 }), "{1 key}");
  assert.equal(value({}), "{}");
  assert.equal(value([1, 2, 3]), "[1, 2, 3]");
  assert.equal(value(Array.from({ length: 22 }, (_, i) => i)), "[22 items]");
  assert.equal(value([{ a: 1 }, "x", null]), "[{1 key}, x, –]");
  for (const v of [{ a: { b: 1 } }, [[1], [2]], [{}], { x: [1, 2, 3, 4, 5, 6] }]) assert.ok(!value(v).includes("[object"));
});

test("full values keep everything", () => {
  assert.equal(full({ a: [1, 2] }), '{\n  "a": [\n    1,\n    2\n  ]\n}');
  assert.equal(full(3e-4), "0.0003");
  assert.equal(full(null), "–");
  assert.equal(full({ x: NaN }), '{\n  "x": "NaN"\n}');
});

test("config columns show their shortest unique suffix", () => {
  const labels = shortLabels([
    "config.lr",
    "config.model.beads.edge_frame",
    "config.model.egnn.edge_frame",
    "config.hydrantic.seed",
    "config.seed",
    "metric.val/loss.last",
    "run.name",
  ]);
  assert.equal(labels.get("config.lr"), "lr");
  assert.equal(labels.get("config.model.beads.edge_frame"), "beads.edge_frame");
  assert.equal(labels.get("config.model.egnn.edge_frame"), "egnn.edge_frame");
  assert.equal(labels.get("config.hydrantic.seed"), "hydrantic.seed");
  assert.equal(labels.get("config.seed"), "seed");
  assert.equal(labels.get("metric.val/loss.last"), "val/loss");
  assert.equal(labels.get("run.name"), "run");
  assert.deepEqual(segments('a["b.c"].d'), ["a", "b.c", "d"]);
});
