import assert from "node:assert/strict";
import { test } from "node:test";

import { clockAt, hasClock, indexAt, latestOf, nearest, scrubLabel, shownAt, stopsOf, type Entry } from "../src/bt/scrub.ts";
import { FIT, MAX, panBy, zoomAt } from "../src/bt/zoom.ts";

const meta = { steps: [100, 200, 300, 400], clocks: [0, 0, 1, 1] };

test("stops are the steps, or the last step of each distinct clock value", () => {
  assert.deepEqual(stopsOf(meta, "step"), { values: [100, 200, 300, 400], steps: [100, 200, 300, 400] });
  assert.deepEqual(stopsOf(meta, "clock"), { values: [0, 1], steps: [200, 400] });
  assert.deepEqual(stopsOf({ steps: [1, 2], clocks: [null, null] }, "clock"), { values: [], steps: [] });
  assert.deepEqual(stopsOf(undefined, "step"), { values: [], steps: [] });
  assert.ok(hasClock(meta));
  assert.ok(!hasClock({ steps: [1, 2], clocks: [3, 3] }));
  assert.ok(!hasClock({ steps: [1, 2] }));
});

test("a position snaps to its closest stop and a step to the stop at or before it", () => {
  const stops = stopsOf(meta, "step");
  assert.equal(nearest(stops.values, 260), 2);
  assert.equal(nearest(stops.values, 240), 1);
  assert.equal(indexAt(stops, 250), 1);
  assert.equal(indexAt(stops, 50), 0);
  assert.equal(indexAt(stopsOf(meta, "clock"), 300), 0);
});

test("every run shows its entries at its latest step at or before the stop", () => {
  const e = (run: string, step: number): Entry => ({ run, step, path: `${step}.png` });
  const entries = [e("a", 100), e("a", 200), e("b", 100), e("c", 300)];
  const at200 = shownAt(entries, 200);
  assert.deepEqual(at200.map((t) => [t.entry.run, t.entry.step, t.earlier]), [["a", 200, false], ["b", 100, true]]);
  assert.deepEqual(shownAt(entries, 50), []);
  assert.equal(latestOf(at200)?.entry.run, "a");
  assert.equal(latestOf([]), undefined);
  assert.deepEqual(shownAt(entries, Infinity).map((t) => [t.entry.run, t.earlier]), [["a", false], ["b", false], ["c", false]]);
});

test("the label names the clock when the page has one", () => {
  assert.equal(scrubLabel("train/epoch", 12, 4000), "epoch 12 · step 4000");
  assert.equal(scrubLabel(null, null, 4000), "step 4000");
  assert.equal(scrubLabel("step", 5, 5), "step 5");
  assert.equal(clockAt(meta, 300), 1);
  assert.equal(clockAt(meta, 301), null);
});

test("zoom keeps the point under the pointer and never leaves the box", () => {
  const z = zoomAt(FIT, 2, 100, 50, 400, 200);
  assert.deepEqual(z, { k: 2, x: -100, y: -50 });
  assert.equal((100 - z.x) / z.k, 100);
  assert.deepEqual(zoomAt(z, 0.25, 0, 0, 400, 200), FIT);
  assert.equal(zoomAt(FIT, 1000, 0, 0, 400, 200).k, MAX);
  assert.deepEqual(panBy(z, 500, 500, 400, 200), { k: 2, x: 0, y: 0 });
  assert.deepEqual(panBy(z, -500, -500, 400, 200), { k: 2, x: -400, y: -200 });
});
