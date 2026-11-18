import assert from "node:assert/strict";
import { test } from "node:test";

import { groupUrl, parse } from "../src/router.ts";

test("a group's list of hidden runs is part of its URL", () => {
  for (const path of [".", "scaling", "scaling/warmup", "@box/scaling"]) {
    const url = groupUrl(path, { hidden: true });
    const [pathname, search] = url.split("?");
    const route = parse(pathname, search ?? "");
    assert.equal(route.page, "group");
    assert.equal(route.page === "group" && route.path, path);
    assert.equal(route.page === "group" && route.hiddenRuns, true);
    const plain = parse(...(groupUrl(path).split("?").concat("") as [string, string]));
    assert.equal(plain.page === "group" && plain.hiddenRuns, false);
  }
  assert.equal(groupUrl("scaling", { hidden: true }), "/f/local/scaling?hidden");
  assert.equal(groupUrl("scaling", { hidden: true, history: true }), "/f/local/scaling?history&hidden");
});
