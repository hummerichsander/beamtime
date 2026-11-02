import assert from "node:assert/strict";
import { test } from "node:test";

import { symbolFor } from "../src/ui/symbols.ts";

test("every state has an icon, a tone and a word", () => {
  assert.deepEqual(symbolFor("run", "failed"), { icon: "circle-x", tone: "bad", label: "failed" });
  assert.equal(symbolFor("run", "running").pulse, true);
  assert.equal(symbolFor("result", "pass (provisional)").icon, "check");
  assert.equal(symbolFor("verdict", "refuted").tone, "bad");
  assert.equal(symbolFor("note", "question").icon, "circle-help");
  assert.equal(symbolFor("research", "concluded").tone, "good");
});

test("unknown states still show something", () => {
  assert.deepEqual(symbolFor("run", "weird"), { icon: "circle-dashed", tone: "muted", label: "weird" });
  assert.equal(symbolFor("result", null).label, "unknown");
});
