import assert from "node:assert/strict";
import { test } from "node:test";

import { runSymbol, symbolFor } from "../src/ui/symbols.ts";

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

test("an unknown kind, as a custom block may pass it, falls back to the neutral symbol", () => {
  assert.deepEqual(symbolFor("nope" as never, "failed"), { icon: "circle-dashed", tone: "muted", label: "failed" });
});

test("a run killed by its time limit says so, and no other state changes", () => {
  assert.equal(runSymbol("killed", { reason: "time_limit" }).label, "killed · time limit");
  assert.equal(runSymbol("killed", { reason: "time_limit" }).tone, "warn");
  assert.equal(runSymbol("killed", { reason: "interrupted" }).label, "killed");
  assert.equal(runSymbol("killed", null).label, "killed");
  assert.equal(runSymbol("finished", { reason: "time_limit" }).label, "finished");
});
