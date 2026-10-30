# The bt kit (custom blocks)

A custom block is an ES module on the `bt` kit, for what no built-in block shows (a heatmap over two
configs, a linked table and chart). Prefer built-in blocks; they need no code. The block runs in a
sandboxed frame with no network: all data comes from the queries it declares.

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

## The API

| Name | What |
|---|---|
| `bt.useData(name, values?)` | hook: a declared query's result; re-renders on new data |
| `bt.data(name, values?)`, `bt.subscribe(name, cb, values?)` | the same as a promise, or a callback per update |
| result | `status` (`loading`, `ready`, `error`), `error`, `columns`, `rows` (objects keyed by field), `curves` (`{run, key, group, x, y \| min, max, last, mean, count}`), `data` (the raw answer) |
| `bt.chart.Line`, `Scatter`, `Bar`, `Histogram` | built-in charts: the props of their YAML form, plus `data` (a result) |
| `bt.ui.Table`, `Stat`, `DataTable`, `Grid`, `Row`, `Section`, `Tabs`/`Tab`, `Note` | built-in blocks and layouts |
| `bt.theme.tokens`, `.mode`, `.onChange(cb)` | the theme; also as CSS variables (`var(--bt-fg)`, `var(--bt-muted)`, ...) |
| `bt.theme.runColor(id)`, `.groupColor(values, value)`, `.scale(kind)` | colors: a run's, a group value's, `sequential`/`diverging` (t in 0..1) or `categorical` (index) |
| `bt.fmt.value(v)`, `bt.fmt.step(n)`, `bt.fmt.duration(s)`, `bt.label(field)`, `bt.name(run)` | formatting |
| `bt.link.run(id)`, `bt.link.group(path)` | URLs; links open in the page |
| `bt.useSize()` | `[ref, width]` of an element |
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
  error panel with the message.
