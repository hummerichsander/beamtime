import assert from "node:assert/strict";
import { test } from "node:test";

import { assignColors, chartStyle, cssVariables, groupColors, ramp } from "../src/bt/theme.ts";
import { groupUrl, parse } from "../src/router.ts";

const palette = ["#a", "#b", "#c", "#d"];
const theme = {
  name: "T", type: "light" as const,
  colors: { bg: "#ffffff", "sidebar.bg": "#eeeeee", border: "#cccccc", grid: "#dddddd", muted: "#666666" },
  data: { categorical: palette, sequential: ["#000000", "#ffffff"], diverging: [], baseline: { color: "#999999", dash: [4, 3] } },
  fonts: { sans: "system-ui" }, sizes: { xs: 11, sm: 12 }, shape: { radius: 4 },
};

test("run colors are stable and distinct within a view", () => {
  const ids = ["20261020-080300-aaaaaaaa", "20261020-080300-bbbbbbbb", "20261020-080300-cccccccc"];
  const a = assignColors(ids, palette);
  const b = assignColors([...ids].reverse(), palette);
  assert.deepEqual([...a.entries()].sort(), [...b.entries()].sort());
  assert.equal(new Set(a.values()).size, 3);
  const many = assignColors([...ids, "x1", "x2", "x3"], palette);
  assert.equal(many.size, 6);
});

test("groups: categorical in sorted order, numeric ramps when many", () => {
  const g = groupColors([0.1, 0.01, 0.001], theme);
  assert.equal(g.get("0.001"), "#a");
  assert.equal(g.get("0.1"), "#c");
  const many = groupColors([1, 2, 3, 4, 5], theme);
  assert.equal(many.get("1"), "#000000");
  assert.equal(many.get("5"), "#ffffff");
  assert.equal(ramp(["#000000", "#ffffff"], 0.5), "#808080");
});

test("css variables and the chart style come from the tokens", () => {
  const vars = cssVariables(theme);
  assert.equal(vars["--bt-sidebar-bg"], "#eeeeee");
  assert.equal(vars["--bt-radius"], "4px");
  const style = chartStyle(theme);
  assert.equal(style.grid, "#dddddd");
  assert.equal(style.axis, "#666666");
});

test("URLs round-trip", () => {
  assert.deepEqual(parse("/f/local/scaling/lr-sweep", "?run=20261020-080300-aaaaaaaa"), {
    page: "group", source: "local", path: "scaling/lr-sweep", run: "20261020-080300-aaaaaaaa", drawer: true,
  });
  assert.equal(parse("/f/local", "").page, "group");
  assert.equal((parse("/f/local", "") as any).path, ".");
  assert.deepEqual(parse("/r/20261020-080300-aaaaaaaa", ""), { page: "run", id: "20261020-080300-aaaaaaaa" });
  assert.equal(groupUrl("scaling/lr-sweep", { drawer: true }), "/f/local/scaling/lr-sweep?drawer=1");
  assert.equal(groupUrl("."), "/f/local");
});
