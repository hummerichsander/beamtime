import assert from "node:assert/strict";
import { test } from "node:test";

import katex from "katex";

import { hasMath, linkFor, markdown } from "../src/bt/md.ts";

test("links to runs, groups, predictions and view versions", () => {
  assert.equal(linkFor("20261020-095500-kg8f9975"), "/r/20261020-095500-kg8f9975");
  assert.equal(linkFor("scaling/lr-sweep/20261020-095500-kg8f9975"), "/r/20261020-095500-kg8f9975");
  assert.equal(linkFor("scaling/lr-sweep#converges"), "/f/local/scaling/lr-sweep");
  assert.equal(linkFor("scaling@20261025-101532-k3m9"), "/f/local/scaling?v=20261025-101532-k3m9");
  assert.equal(linkFor("."), "/f/local");
  const out = markdown("See [[scaling/lr-sweep#converges]] and [[20261020-095500-kg8f9975]].");
  assert.match(out, /<a class="wikilink" href="\/f\/local\/scaling\/lr-sweep">scaling\/lr-sweep#converges<\/a>/);
  assert.match(out, /href="\/r\/20261020-095500-kg8f9975"/);
});

test("raw HTML and unsafe links stay text", () => {
  const out = markdown('<script>alert(1)</script> <img src=x onerror=alert(1)> [x](javascript:alert(1))');
  assert.doesNotMatch(out, /<script|<img|href="javascript/);
  assert.doesNotMatch(markdown("[x](javascript:void(0))"), /href=/);
  assert.match(out, /&#60;script&#62;/);
  assert.match(markdown("[docs](https://example.org)"), /target="_blank" rel="noopener noreferrer"/);
});

test("GFM: tables, task lists, code", () => {
  const out = markdown("| a | b |\n|---|---|\n| 1 | 2 |\n\n- [x] done\n\n```py\nx < 1\n```\n");
  assert.match(out, /<table>/);
  assert.match(out, /type="checkbox"/);
  assert.match(out, /x &lt; 1/);
});

test("math renders with KaTeX; prices stay text", () => {
  assert.equal(hasMath("costs $5 and $10"), false);
  assert.equal(hasMath("the effect $\\Delta = 0.035$"), true);
  const out = markdown("Effect $\\Delta = 0.03$ and\n\n$$\\sum_i x_i$$\n", katex);
  assert.match(out, /class="katex"/);
  assert.match(out, /class="math"/);
  assert.match(markdown("costs $5 and $10", katex), /costs \$5 and \$10/);
});
