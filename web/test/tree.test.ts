import assert from "node:assert/strict";
import { test } from "node:test";

import { groupUrl, isRoot, parse, rootOf, runUrl, sourcedRun } from "../src/router.ts";
import { buildTree, depth, siblings, visible } from "../src/shell/tree.ts";

const rows = [
  { path: ".", runs: 26 },
  { path: "scaling", runs: 20 },
  { path: "scaling/lr-sweep", runs: 17, running: 1, failed: 1 },
  { path: "scaling/long-context", runs: 3 },
  { path: "tokenizer", runs: 6 },
  { path: "tokenizer/bpe-vs-unigram", runs: 6 },
];

test("the tree nests groups and shows open ones", () => {
  const [root] = buildTree(rows);
  assert.deepEqual(root.children.map((c) => c.name), ["scaling", "tokenizer"]);
  assert.deepEqual(visible([root], new Set(), "").map((n) => n.path), [".", "scaling", "tokenizer"]);
  assert.deepEqual(
    visible([root], new Set(["scaling"]), "").map((n) => n.path),
    [".", "scaling", "scaling/long-context", "scaling/lr-sweep", "tokenizer"],
  );
  assert.deepEqual(visible([root], new Set(), "bpe").map((n) => n.path), [".", "tokenizer", "tokenizer/bpe-vs-unigram"]);
  assert.equal(root.children[0].children[1].failed, 1);
});

test("siblings for [ and ]", () => {
  const roots = buildTree(rows);
  assert.deepEqual(siblings(roots, "scaling/lr-sweep").map((n) => n.path), ["scaling/long-context", "scaling/lr-sweep"]);
  assert.deepEqual(siblings(roots, "tokenizer").map((n) => n.path), ["scaling", "tokenizer"]);
});

test("each source has its own root, also one that can't answer", () => {
  const remote = [{ path: "@box", runs: 4 }, { path: "@box/scaling", runs: 4 }, { path: "@box/scaling/lr-sweep", runs: 4 }];
  const roots = buildTree([...rows, ...remote], [
    { name: "local", state: "connected" },
    { name: "@box", state: "connected" },
    { name: "@gone", state: "unreachable", error: "ssh: timed out" },
  ]);
  assert.deepEqual(roots.map((r) => r.path), [".", "@box", "@gone"]);
  assert.deepEqual(roots[1].children.map((c) => c.path), ["@box/scaling"]);
  assert.equal(roots[2].state, "unreachable");
  assert.deepEqual(visible(roots, new Set(), "").map((n) => n.path), [".", "scaling", "tokenizer", "@box", "@box/scaling", "@gone"]);
  // any host closes, local too; a filter still finds what is inside.
  assert.deepEqual(visible(roots, new Set(), "", new Set([".", "@box"])).map((n) => n.path), [".", "@box", "@gone"]);
  assert.ok(visible(roots, new Set(), "scaling", new Set(["@box"])).some((n) => n.path === "@box/scaling"));
  assert.deepEqual(siblings(roots, "@box").map((n) => n.path), [".", "@box", "@gone"]);
  assert.deepEqual([depth("."), depth("@box"), depth("@box/scaling"), depth("scaling")], [0, 0, 1, 1]);
});

test("remote paths round-trip through URLs", () => {
  for (const path of [".", "scaling/lr-sweep", "@box", "@box/scaling/lr-sweep"]) {
    const url = new URL(groupUrl(path, { drawer: true }), "http://x");
    const r = parse(url.pathname, url.search);
    assert.ok(r.page === "group" && r.path === path && r.drawer, path);
  }
  assert.equal(groupUrl("@box/a b"), "/f/@box/a%20b");
  assert.deepEqual([rootOf("@box/x"), rootOf("x"), isRoot("@box"), isRoot("@box/x"), isRoot(".")], ["@box", ".", true, false, true]);
});

test("runs on a remote's pages link to that remote", () => {
  const id = "20261020-095500-yjb5ba9x";
  assert.equal(runUrl(id, "@box/scaling"), `/r/@box/${id}`);
  assert.equal(runUrl(id, "scaling"), `/r/${id}`);
  assert.equal(runUrl(`@box/${id}`, "scaling"), `/r/@box/${id}`);
  const r = parse(`/r/@box/${id}`, "");
  assert.ok(r.page === "run" && r.id === `@box/${id}`);
  assert.equal(sourcedRun(id, "@box/scaling/lr-sweep"), `@box/${id}`);
});
