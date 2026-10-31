import assert from "node:assert/strict";
import { test } from "node:test";

import { frozenKey } from "../src/api.ts";

test("an exported page finds curves at any chart width, with defaults and in any key order", () => {
  const stored = frozenKey("series", { from: "g", y: ["val/acc"] });
  assert.equal(frozenKey("series", { y: ["val/acc"], from: "g", x: "_step", points: 640, band: "minmax" }), stored);
  assert.notEqual(frozenKey("series", { from: "g", y: ["val/acc"], points: 48 }), stored);
  assert.equal(frozenKey("series", { from: "g", y: ["val/acc"], steps: [100, 900] }), stored);
  assert.notEqual(frozenKey("series", { from: "g", y: ["val/acc"], band: "std" }), stored);
  assert.equal(frozenKey("runs", { b: 1, a: [2, { d: 3, c: 4 }] }), frozenKey("runs", { a: [2, { c: 4, d: 3 }], b: 1 }));
});
