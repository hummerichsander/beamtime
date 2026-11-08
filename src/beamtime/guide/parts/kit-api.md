# The bt kit: API and rules

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
