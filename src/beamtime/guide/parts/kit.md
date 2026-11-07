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

## The API

| Name | What |
|---|---|
| `bt.useData(name, values?)` | hook: a declared query's result; re-renders on new data |
| `bt.data(name, values?)`, `bt.subscribe(name, cb, values?)` | the same as a promise, or a callback per update |
| result | `status` (`loading`, `ready`, `error`), `error`, `columns`, `rows` (objects keyed by field), `curves` (`{run, key, group, x, y \| min, max, last, mean, count}`), `data` (the raw answer); a `runs` answer's `columns` always start with `run.id`, selected or not |
| `bt.chart.Line`, `Scatter`, `Bar`, `Histogram` | built-in charts: the props of their YAML form, plus `data` (a result) |
| `bt.chart.Figure` | your own drawing in the chart frame: `id`, `title`, `xlabel`, `ylabel`, `series`, `settings`, `csv`, `draw(el, {width, height, prefs, hovered, hidden})` |
| `bt.ui.Table`, `Stat`, `DataTable`, `Grid`, `Row`, `Section`, `Tabs`/`Tab`, `Note` | built-in blocks and layouts |
| `bt.ui.Sym` (`kind`, `value`, `word?`) | the app's symbol for a value; `kind`: `run`, `result`, `verdict`, `note`, `research`, `thing`; unknown values get a neutral symbol |
| `bt.ui.Icon` (`name`), `bt.ui.Tag` (`tone`) | a lucide icon by name; a pill with a tone |
| `bt.ui.Predictions` (`of?`) | the `proposal` block's prediction rows with the live check of a group (default: the view's) |
| `bt.ui.Config` (`config`, optional `varying`: dotted keys) | a nested config as a collapsible, filterable tree |
| `bt.theme.tone(name)` | the colour of `good`, `bad`, `warn`, `muted` or `accent` in the current theme: colour a pass or fail like the app does |
| `bt.theme.tokens`, `.mode`, `.onChange(cb)` | the theme (`colors.ink`, `colors["data-1"]`, ...); also as CSS variables (`var(--ink)`, `var(--muted)`, `var(--line)`, ...) |
| `bt.theme.runColor(id)`, `.runDash(id)`, `.groupColor(values, value)`, `.scale(kind, name?)` | a run's color and line style (stroke-dasharray values), a group value's color, the built-in colormaps as `sequential` (viridis)/`diverging` (coolwarm) (t in 0..1) or the matplotlib colormap `name` (e.g. `.scale("sequential", "magma")`), or `categorical` (index) |
| `bt.fmt.value(v)`, `bt.fmt.step(n)`, `bt.fmt.duration(s)`, `bt.label(field)`, `bt.name(run)` | formatting |
| `bt.link.run(id)`, `bt.link.group(path)` | URLs; links open in the page |
| `bt.useSize()` | `[ref, width]` of an element |
| `bt.hover(run)`, `bt.useHovered()` | highlight a run in every chart of the page; the run hovered anywhere on it |
| `bt.warn(message)` | a warning on the block and in `view_validate` |
| `bt.params` | a library block's params as the view gives them, defaults filled in |
| `bt.lib.d3` ... | the declared libraries |
| `bt.preact` | `h`, `render`, `html` (htm) and the hooks |

## Rules (checked by `view_validate`)

- `export default function render(root)`; no `import`: everything comes through `bt`.
- No network (`fetch`, `XMLHttpRequest`, `WebSocket`, ...), at most 64 KB, no long inline number
  lists (data belongs in queries or data files).
- No color literals (`#hex`, `rgb(`, `hsl(`): take colors from `bt.theme` or CSS variables, so the
  block works in light and dark.
- Read field names from the query's `columns` instead of writing them into the code; such a block
  can become a library block later.
- The render must show no errors, draw something and fit its width; a block that throws shows an
  error panel with the message. The checks can't tell a chart drawn from the wrong column: look at
  the screenshot.

## Library blocks

`block_promote` and `block_fork` write a draft `.beamtime/drafts/blocks/<name>/block.yaml`:

```yaml
schema: 1
name: phase-map
description: >                       # what it shows; "Use for ..."; "Not for ..."
  Heatmap of a value over two config fields. Use for two-way sweeps. Not for single runs.
params:                              # kind: field, fields, metric, metrics, number, string, bool
  x: {kind: field, description: the config across}
  y: {kind: field, default: config.seed}
  value: {kind: field}
  curves: {kind: metrics, default: [val/acc]}
examples:                            # at least two; each is the params of one use
  - {x: config.lr, value: metric.val/acc.max}
  - {x: config.lr, y: config.wd, value: metric.val/loss.min, curves: [val/loss]}
queries:                             # $param fills in when a view uses it; other $names at runtime
  runs: {runs: {select: [run.id, $x, $y, $value]}}
  detail: {series: {from: $run, y: $curves}}
code: code/phase-map.js
libs: [d3]
```

A list param fills a list in place (`select: [run.id, $fields]`). Number, string and bool params
reach the code as `bt.params`. `block_validate` runs and renders every example as a use in a view
of the draft's group; `view_render block-<name>` takes screenshots of them.
