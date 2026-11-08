# The bt kit (custom blocks)

**Built-in blocks come first.** Before writing a custom block, make sure that no built-in block
(`guide blocks`) or library block (`block_list`) can show what you need, or that it would look visibly
worse. Try it: draft the view with the built-in block, `view_render` it and look at the screenshot.
Write code only for what remains, such as a heatmap over two configs or a linked table and chart, and
say why in the `--message` of `view_save`. Built-in blocks need no code and follow the design system
and every later change to it.

A custom block is an ES module on the `bt` kit. It runs in a sandboxed frame with no network: all data
comes from the queries it declares. Declare `kit: 2` for `bt.chart.Figure` and the app's vocabulary
(`bt.ui.Sym`, `Icon`, `Tag`, `Predictions`, `bt.theme.tone`); version 1 blocks run unchanged.

```yaml
- custom:
    id: phase-map
    title: val/acc over lr and weight decay
    caption: Mean val/acc per cell over seeds; click a cell for its best run.
    code: code/phase-map.js          # in the draft's code/ folder
    libs: [d3]                       # optional: d3, uplot, katex
    queries:                         # one kind each: keys, runs, series, data, timeline, groups, file
      runs:   {runs: {select: [run.id, config.lr, config.weight_decay, metric.val/acc.max]}}
      detail: {series: {from: $run, y: [train/acc, val/acc]}}   # $run is filled at runtime
```

Queries take the parameters of the MCP tool of the same name; `from` is relative to the page, and
the view's `filters` and the block's `where` apply. `$name` strings are placeholders the code fills.
`guide examples custom` shows a complete view; `view_new <group> --from custom` copies its code.

## The module

```js
const { html, useState } = bt.preact;

function Block() {
  const runs = bt.useData("runs");              // {status, error, columns, rows, curves, data}
  const [run, setRun] = useState(null);
  return html`
    <${bt.ui.Table} data=${runs} columns=${runs.columns} />
    ${run ? html`<${Detail} run=${run} />` : null}`;
}

function Detail({ run }) {
  const detail = bt.useData("detail", { run }); // fills $run
  return html`<${bt.chart.Line} data=${detail} caption="Curves of the selected run." />`;
}

export default function render(root) {
  bt.preact.render(html`<${Block} />`, root);
}
```

## Three tiers of charts

Use the first tier that can show what you need; each later one gives up something the earlier ones do.
The rule: a chart a built-in block can draw is tier 1 or 2; tier 3 only for a drawing none can make.

1. **A YAML block** (`line`, `scatter`, `scorecard`, ...): everything is included. No code.
2. **`bt.chart.Line`, `Scatter`, `Bar`, `Histogram`** in a custom layout: the props of the YAML form, a
   declared query as `data`, and the same features (settings, legend, hover, downloads, axis titles).
   Use these when the layout is custom (a table beside a chart, a chart for the selected run) and the chart is
   a built-in one.
3. **`bt.chart.Figure`**, for a drawing no block can make (a phase portrait, a heatmap, an annotated curve):

```js
const { html } = bt.preact;
const d3 = bt.lib.d3;

function Phase() {
  const orbit = bt.useData("orbit");
  const series = orbit.curves.map((c) => ({ key: c.run, label: bt.name(c.run), color: bt.theme.runColor(c.run) }));
  const draw = (el, { width, height, prefs, hovered, hidden }) => {
    const ramp = bt.theme.scale("sequential", prefs.colormap);
    const curves = orbit.curves.filter((c) => !hidden.has(c.run));
    // d3 into el: replace what is there, el is the same element on every call
    d3.select(el).selectAll("svg").data([0]).join("svg").attr("width", width).attr("height", height)
      .selectAll("path").data(curves, (c) => c.run).join("path")
      .attr("fill", "none")
      .attr("stroke", (c, i) => ramp(i / Math.max(1, curves.length - 1)))
      .attr("stroke-width", (c) => (c.run === hovered ? 3 : 1.5))
      .on("pointerenter", (e, c) => bt.hover(c.run))
      .on("pointerleave", () => bt.hover(null));
    /* scales, axes and the path data omitted */
  };
  return html`<${bt.chart.Figure} id="phase" title="Phase portrait" xlabel="x" ylabel="p"
    series=${series} settings=${["scale", "colormap"]} draw=${draw}
    csv=${orbit.curves.flatMap((c) => c.x.map((x, i) => ({ run: c.run, x, y: c.y?.[i] ?? c.last?.[i] })))} />`;
}
```

`Figure` supplies the head, the settings panel (the fields in `settings`: `x`, `scale`, `range`, `smooth`, `color`,
`colormap`, `outliers`, `legend`), the legend with hide and solo (from `series`), hover both ways, downloads (SVG or
PNG of what `el` holds, CSV from `csv`) and the viewer's saved preferences. Your code draws the plot into `el` and
**titles both axes** from `xlabel` and `ylabel` (also in `draw`'s context). `draw` runs again when the data, the
preferences, the hovered key, the hidden keys, the size or the theme change, and never fetches: keep it a pure
function of its inputs. Colors come from `bt.theme` (`runColor`, `scale`, `tone`), never from literals. A block with a
`Figure` has no head of its own; the figure's Expand opens the block in the page's dialog, where `height` is larger.

## Reuse Beamtime's vocabulary

A symbol, colour or pill the app already has for a thing is used as is, so the same mark means the same
thing on every page. Never hex colours, emoji or glyphs for status, and never a typed-in result.

| Thing | Kit name |
|---|---|
| run status, prediction result, verdict, note type | `bt.ui.Sym` with that `kind` |
| predictions with their check | the `predictions` block, or `bt.ui.Predictions` |
| pass, fail, warning | `bt.theme.tone` (`good`, `bad`, `warn`) |
| a run's or group's colour, a colour ramp | `bt.theme.runColor`, `groupColor`, `scale` |

## Titles go in the left column

Every top-level block of a view is a page section. A top-level `section` (or custom block) titled
with one or two words shows that title in the margin; a longer title, a nested section, a Markdown
`##` in a `text` block and `bt.ui.Section` inside code all stay in the content column. So structure a
view as top-level `section`s with short titles (`validation`, `energy`, `phase space`) and put the
blocks, custom ones included, inside; split one big custom block into one per section. Use
`bt.ui.Section` only for subheadings within one block; longer explanations go in the caption.

`guide kit-api` lists every name and the rules `view_validate` checks. For live data use `bt.useData`,
never a value copied into the code.
