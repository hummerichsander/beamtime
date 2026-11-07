import assert from "node:assert/strict";
import { test } from "node:test";

import { readFile } from "node:fs/promises";

import { labelOf } from "../src/bt/labels.ts";
import { assignColors, chartStyle, colormaps, cssVariables, dashOf, groupColors, ramp, slotOf, stopsOf, swatch } from "../src/bt/theme.ts";
import { groupUrl, parse } from "../src/router.ts";

const palette = ["#aaaaaa", "#bbbbbb", "#cccccc", "#dddddd"];
const theme = {
  name: "T", type: "light" as const,
  colors: { paper: "#ffffff", line: "#dddddd", muted: "#666666", "data-1": palette[0], "data-2": palette[1], "data-3": palette[2], "data-4": palette[3] },
  dashes: [[], [6, 3], [1.5, 3], [8, 3]],
  stroke: 1.6,
  font: "12.5px Plex",
  ramps: { sequential: ["#000000", "#ffffff"], diverging: ["#000000", "#ffffff"] },
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

test("groups: palette in sorted order, numeric ramps from the colormap when many", () => {
  const g = groupColors([0.1, 0.01, 0.001], theme);
  assert.equal(g.get("0.001"), palette[0]);
  assert.equal(g.get("0.1"), palette[2]);
  const many = groupColors([1, 2, 3, 4, 5], theme);
  assert.equal(many.get("1"), "#000000");
  assert.equal(many.get("5"), "#ffffff");
  assert.equal(ramp(["#000000", "#ffffff"], 0.5), "#808080");
});

test("a chosen colormap always applies: to numbers by order, to categories evenly spaced", () => {
  const stops = ["#000000", "#ffffff"];
  const few = groupColors([0.1, 0.01, 0.001], theme, stops);
  assert.deepEqual([...few.values()], ["#000000", "#808080", "#ffffff"]);
  const arms = groupColors(["a", "b", "c"], theme, stops);
  assert.equal(arms.get('"a"'), "#000000");
  assert.equal(arms.get('"c"'), "#ffffff");
  assert.equal(groupColors(["only"], theme, stops).get('"only"'), "#ffffff");
  assert.equal(groupColors(["a", "b"], theme).get('"a"'), palette[0]);
});

test("colormaps are found by name in either family, and an export keeps their colors", async () => {
  // export.ts reads the page's color scheme when it loads.
  (globalThis as any).matchMedia ??= () => ({ matches: false, addEventListener() {} });
  const { recolor } = await import("../src/bt/export.ts");
  colormaps.set({ sequential: { viridis: ["#440154", "#fde725"] }, diverging: { coolwarm: ["#3b4cc0", "#b40426"] } });
  assert.deepEqual(stopsOf("coolwarm"), ["#3b4cc0", "#b40426"]);
  assert.equal(stopsOf("nope"), null);
  assert.equal(stopsOf(null), null);
  const dark = { ...theme, colors: { ...theme.colors, "data-1": "#111111" } };
  assert.equal(recolor("#440154", theme, dark), "#440154");
  assert.equal(recolor(palette[0], theme, dark), "#111111");
});

test("a run's color carries its line style; a colormap's color is solid", () => {
  assert.deepEqual(dashOf(palette[1], theme), [6, 3]);
  assert.deepEqual(dashOf("#123456", theme), []);
  assert.equal(slotOf(palette[2], theme), 3);
  assert.deepEqual(swatch(palette[3], theme), { class: "swatch run-4" });
  assert.deepEqual(swatch("#123456", theme), { class: "swatch", style: "color:#123456" });
});

test("css variables and the chart style come from the tokens", () => {
  assert.equal(cssVariables(theme)["--paper"], "#ffffff");
  const style = chartStyle(theme);
  assert.equal(style.grid, "#dddddd");
  assert.equal(style.axis, "#666666");
  assert.equal(style.line, 1.6);
});

test("sections are labelled by what they hold", () => {
  const node = (block: string, props = {}, children?: any[]) => ({ block, props, children });
  assert.equal(labelOf(node("table", { title: "Recent runs" })), "runs");
  assert.equal(labelOf(node("row", {}, [node("stat"), node("stat")])), "readings");
  assert.equal(labelOf(node("grid", {}, [node("line"), node("scatter")])), "charts");
  assert.equal(labelOf(node("grid", {}, [node("line"), node("table")])), "");
  assert.equal(labelOf(node("custom", { title: "Phase map" })), "phase map");
  assert.equal(labelOf(node("custom", { title: "A long title of a block" })), "");
});

test("no stylesheet sets a font size or uses an old variable", async () => {
  for (const file of ["base", "shell", "blocks"]) {
    const css = await readFile(`src/styles/${file}.css`, "utf8");
    assert.doesNotMatch(css, /font-size:(?!\s*inherit)/, file);
    assert.doesNotMatch(css, /--bt-/, file);
  }
});

test("URLs round-trip", () => {
  assert.deepEqual(parse("/f/local/scaling/lr-sweep", "?run=20261020-080300-aaaaaaaa"), {
    page: "group", source: "local", path: "scaling/lr-sweep", run: "20261020-080300-aaaaaaaa", drawer: true,
    version: null, draft: null, history: false,
  });
  const old = parse("/f/local/g", "?v=20261028-215111-36js&history");
  assert.equal((old as any).version, "20261028-215111-36js");
  assert.equal((old as any).history, true);
  assert.equal(groupUrl("g", { history: true }), "/f/local/g?history");
  assert.equal(groupUrl("g", { version: "20261028-215111-36js" }), "/f/local/g?v=20261028-215111-36js");
  assert.equal(parse("/f/local", "").page, "group");
  assert.equal((parse("/f/local", "") as any).path, ".");
  assert.deepEqual(parse("/r/20261020-080300-aaaaaaaa", ""), { page: "run", id: "20261020-080300-aaaaaaaa" });
  assert.equal(groupUrl("scaling/lr-sweep", { drawer: true }), "/f/local/scaling/lr-sweep?drawer=1");
  assert.equal(groupUrl("."), "/f/local");
});
