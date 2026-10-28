import assert from "node:assert/strict";
import { test } from "node:test";

import { buildTree, siblings, visible } from "../src/shell/tree.ts";

const rows = [
  { path: ".", runs: 26 },
  { path: "scaling", runs: 20 },
  { path: "scaling/lr-sweep", runs: 17, running: 1, failed: 1 },
  { path: "scaling/long-context", runs: 3 },
  { path: "tokenizer", runs: 6 },
  { path: "tokenizer/bpe-vs-unigram", runs: 6 },
];

test("the tree nests folders and shows open ones", () => {
  const root = buildTree(rows);
  assert.deepEqual(root.children.map((c) => c.name), ["scaling", "tokenizer"]);
  assert.deepEqual(visible(root, new Set(), "").map((n) => n.path), [".", "scaling", "tokenizer"]);
  assert.deepEqual(
    visible(root, new Set(["scaling"]), "").map((n) => n.path),
    [".", "scaling", "scaling/long-context", "scaling/lr-sweep", "tokenizer"],
  );
  assert.deepEqual(visible(root, new Set(), "bpe").map((n) => n.path), [".", "tokenizer", "tokenizer/bpe-vs-unigram"]);
  assert.equal(root.children[0].children[1].failed, 1);
});

test("siblings for [ and ]", () => {
  const root = buildTree(rows);
  assert.deepEqual(siblings(root, "scaling/lr-sweep").map((n) => n.path), ["scaling/long-context", "scaling/lr-sweep"]);
  assert.deepEqual(siblings(root, "tokenizer").map((n) => n.path), ["scaling", "tokenizer"]);
});
