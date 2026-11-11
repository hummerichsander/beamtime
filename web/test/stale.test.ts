import assert from "node:assert/strict";
import { test } from "node:test";

import { kindsOf, setStaleKinds } from "../src/api.ts";

test("a call is stale on every kind until meta names its kinds", () => {
  assert.deepEqual(kindsOf("series"), ["metrics", "status", "authored"]);
  setStaleKinds({ series: ["metrics", "status"], notes: ["authored"] });
  assert.deepEqual(kindsOf("series"), ["metrics", "status"]);
  assert.deepEqual(kindsOf("notes"), ["authored"]);
  assert.deepEqual(kindsOf("a_new_method"), ["metrics", "status", "authored"]);
  setStaleKinds(undefined);
  assert.deepEqual(kindsOf("series"), ["metrics", "status", "authored"]);
});
