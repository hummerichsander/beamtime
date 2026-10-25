# Layer 5: Views

Status: **draft, under discussion.** This part covers prior art, principles, the view format,
custom blocks and the agent loop. The widget catalog, the `bt` kit's API and the theme follow in
later parts.

A view is what a folder shows: a page that agents build freely, from declarative widgets and from
their own code.
[Layer 1](01-storage.md#views) fixes where views live, how they are inherited and versioned, and that
they get data only through queries ([layer 3](03-index.md#query-language)).

## Prior art: dashboards as code

| Tool | Format and layout | Data binding | Interactivity | Lesson |
|---|---|---|---|---|
| W&B workspaces and reports | Server-held JSON, editable via Pydantic classes; sections of panels, reports as blocks plus panel grids with `x, y, w, h` | the container owns a run set (filters, grouping); panels only name metric keys | run selection, grouping and smoothing cascade to all panels | closest to Beamtime's folder-relative views; not diffable; panels with unknown keys render blank |
| TensorBoard custom scalars | `Layout → Category → Chart` with regex-matched tags; written into the event log | regex over tags | none | tiny schema; a value-plus-band chart as a first-class type |
| Grafana | JSON with a 24-column grid; v2 separates an `elements` map from a `layout` (grid, auto-grid, rows, tabs) | panels hold queries; per-field config (unit, decimals, thresholds) | typed variables interpolated into queries, `repeat` panels per value, conditional rendering when empty | variables and repeat are the most copied pattern; absolute grids cause noisy diffs; library panels outside files are painful |
| Evidence.dev | Markdown with named SQL blocks; components reference queries by name | query-then-component | inputs feed `${inputs.x}` into queries; optional clauses vanish when unset | an unset filter should drop its clause |
| Quarto dashboards | headings form pages, rows, columns; each cell a card; tabsets, sidebars, value boxes | code cells | via Shiny/OJS only | a handful of layout primitives covers most dashboards |
| Observable Framework | Markdown with reactive JS; CSS grid classes and cards | build-time data loaders | reactive inputs | responsiveness comes from the card, not the chart |
| Streamlit, Gradio | imperative layout by execution order | code | Streamlit reruns everything on interaction | static dependency graphs scale, full reruns don't |
| Superset, Metabase | charts bound to datasets, dashboards reference charts | per chart | filters wired per chart | per-widget filter wiring is the recurring pain |
| Vega-Lite, Altair | concat, repeat, facet; `config` themes | inline or named datasets | params and selections, but only within one spec | good per chart; cross-chart layout and filters belong to the host |
| Rill canvas | YAML rows of items on 12 columns, tabs, `if` per item, inline theme | all charts share one metrics view | page filters apply to every chart | the closest analogue to a Beamtime view file |
| Lightdash | chart YAML separate from dashboard YAML; items addressed by slug | per chart | filters with explicit targets | slugs make items addressable; whole-file uploads clobber edits |

## Prior art: agents generating UIs and charts

- **Freedom levels.** The field has settled on the same three levels as Beamtime: a catalog of
  components the host renders, a declarative spec (Google's A2UI, Vercel's json-render), and free
  code in a sandbox (Claude Artifacts, MCP Apps). Catalogs win on safety, consistency, validation
  and incremental updates; free code wins on expressiveness. Every system allowing free code
  sandboxes it and narrows the libraries.
- **Component descriptions for the model.** json-render gives every component a schema and a
  natural-language "when to use" description that the model reads. Catalogs are kept small.
- **A2UI uses a flat list of components linked by id** rather than a nested tree, because it is
  easier to generate, stream and update incrementally.
- **Most chart errors are semantic, not syntactic**: wrong field, wrong aggregation, wrong scale,
  layout and readability problems (VisEval, DV-World). Plotly and D3 fail more often than
  matplotlib and Vega-Lite; a repair loop on execution errors brings Vega-Lite success to ~96%.
- **Templates remove whole classes of error.** Data Formulator 2 lets the model choose the chart
  and the fields while Vega-Lite templates produce the encoding.
- **Rules alone are not enough.** Frontier models catch common design-rule violations but miss
  subtle perceptual ones; deterministic checkers are stronger. Few-shot examples beat zero-shot.
- **Screenshot critique helps strong models.** In MatPlotAgent, visual feedback gave GPT-4 about 8
  of a 12-point gain; a weak model got worse. WebGen-Agent nearly doubled Claude 3.5 Sonnet's
  accuracy with screenshot critique and backtracking. Gains level off after 1–3 rounds.
- **Model judges are reliable on checklists, not on beauty.** VisJudge-Bench: the best general
  model correlates only 0.43 with experts on aesthetics. ArtifactsBench (render, screenshot, judge
  against a per-task checklist) reaches 94% ranking agreement with human preference.
- **Design consistency is enforced structurally.** v0, the Apps SDK, A2UI and Thesys let the host's
  design system render; Anthropic's frontend-design skill shows that unguided models converge on
  generic styles. For dashboards, consistency matters more than distinctiveness, so Beamtime owns
  the tokens.

## Principles

1. **Agents build views freely; robustness comes from contracts, building blocks and tests.** Custom
   code is a first-class part of a view, not an escape hatch. What keeps views correct and
   consistent is the data contract (declared queries), Beamtime's kit and theme, the sandbox, and a
   validation pipeline that renders every view before it is saved.
2. **The view owns the data context.** A view's scope is the viewed folder plus view-level filters.
   All data, for widgets and custom code alike, comes through declared queries relative to that
   scope, so inheritance and live updates work everywhere.
3. **Two ways to build, freely mixed.** Declarative widgets are the fast path for standard views:
   the agent states intent (`line: {y: val/loss, color: config.lr}`) and Beamtime produces the chart
   with correct defaults. Custom blocks are code for everything else. A view may be all widgets, all
   custom, or both.
4. **Beamtime owns the look.** One theme drives widgets, the kit, Vega-Lite's `config` and CSS
   variables. Runs keep their color across every widget, custom block and page. Views contain no
   colors, fonts or pixel sizes; custom code takes them from the theme.
5. **Few layout primitives, no coordinates** in the YAML tree: section, row, auto-fitting grid, tabs
   (not nested) and repeat. Inside a custom block, layout is the agent's.
6. **Strict, deterministic validation before any screenshot.** Errors carry the block id, the
   location and a suggested fix.
7. **Everything addressable.** Every node can carry an `id`, used by validation errors, screenshots
   and edits.
8. **Degrade, never break.** A block without data in the viewed folder shows a one-line notice; a
   custom block that throws shows an error panel; the frame and every other block stay intact.

## The view format

```yaml
version: 1
title: Grokking under weight decay
finding: Generalization jumps once weight decay exceeds 0.1, independent of model size.

filters:
  run.status: {ne: failed}

metrics:
  val/acc: {label: Validation accuracy, unit: "%", higher_is_better: true}
  train/loss: {label: Training loss, scale: log}

baseline:
  where: {config.weight_decay: 0}
  match: [config.n_params, config.seed]

body:
  - row:
      - stat: {id: best-acc, field: metric.val/acc.max, best: true}
      - stat: {id: runs, field: count}
  - custom:
      id: grokking-map
      code: grokking-map.js
      kit: 1
      queries:
        runs:   {runs: {select: [run.id, config.weight_decay, config.n_params, metric.val/acc.max]}}
        detail: {series: {from: $run, y: [train/acc, val/acc]}}
  - line: {id: by-wd, y: val/acc, group: [config.weight_decay], band: std,
           caption: Validation accuracy per weight decay, mean and spread over runs.}
  - repeat:
      over: config.n_params
      body:
        - stat: {field: metric.val/acc.max, best: true, caption: Best run with $value parameters.}
        - line: {y: val/acc, color: config.weight_decay}
```

- **The view is a nested tree.** Layout nodes contain blocks; any node may carry an `id`. A flat list
  of elements plus a separate layout (A2UI, Grafana v2) helps streaming generators, but Beamtime's
  agents write and edit a file with ordinary tools, where a nested tree reads better.
- **`finding`**: the one-sentence key result, shown under the frame.
- **`filters`** and **`metrics`** are inherited together with the view; `metrics` gives labels,
  units, scales and `higher_is_better`, so widgets, the kit and axes agree.
- **`baseline`** marks reference runs (see [Baselines](#baselines)).
- **`repeat`** repeats a block of widgets once per value of a field, or per subfolder. Each copy's
  scope is narrowed to the runs with that value; `$value` names the value in captions. For a single
  chart split by a field, `facet` is better (shared axes).
- **`custom`** is a block of agent code (see [Custom blocks](#custom-blocks)). Reusable blocks from
  the project's library are used by name, like widgets (see [Block library](#block-library)).
- **`uses`** is written by `view_save`: the library block versions the view is pinned to.

The widget catalog (charts, tables, stat tiles, images, notes, proposal, timeline) is specified in a
later part. Each widget is a msgspec struct with a "when to use / when not to use" description in
its JSON schema.

## Custom blocks

A custom block is an ES module written by the agent, stored with the view as
`view/code/<sha8>-<name>.js` (immutable, named by content hash, like data files).

```js
// grokking-map.js
const {html, useState} = bt.preact;

function GrokkingMap() {
  const runs = bt.useData("runs");
  const [selected, setSelected] = useState(runs.rows[0]?.["run.id"]);
  const detail = bt.useData("detail", {run: selected});
  return html`
    <${bt.ui.Grid} columns=${2}>
      <${bt.ui.Heatmap} data=${runs} x="config.weight_decay" y="config.n_params"
                        value="metric.val/acc.max" onSelect=${r => setSelected(r["run.id"])} />
      <${bt.chart.Line} data=${detail} y=${["train/acc", "val/acc"]}
                        caption="Train and validation accuracy of the selected run." />
    <//>`;
}

export default function render(root) {
  bt.preact.render(html`<${GrokkingMap} />`, root);
}
```

### Data: declared queries

- Every query a block uses is **declared in the YAML**, in the object form of
  [layer 3](03-index.md#query-language), relative to the viewed folder.
- Queries without placeholders are **prefetched** before the code runs and kept live: when runs
  change, Beamtime re-runs exactly the affected queries and the block re-renders.
- Queries may contain **placeholders** (`$run`, `$start`, `$end`). Their shape is fixed and validated
  statically; only values are supplied at runtime (`bt.useData("detail", {run: id})`), checked
  against the placeholder's type. This covers interaction such as clicking into a run, step-window
  sliders and selections, while every field a block can touch is known before it runs.
- There is no free query API. Code cannot read files, call the network or query anything it hasn't
  declared.

### The `bt` kit

Every custom block gets a global `bt`. This is an overview; the full API is in
[The `bt` kit API](#the-bt-kit-api).

| Part | Contents |
|---|---|
| `bt.useData`, `bt.data`, `bt.subscribe` | declared query results, as a Preact hook, a plain getter and a change callback |
| `bt.ui` | layout and content components matching the YAML widgets: `Grid`, `Row`, `Tabs`, `Section`, `Stat`, `Table`, `Heatmap`, `Note`, `Image`, … |
| `bt.chart` | chart components producing themed Vega-Lite: `Line`, `Scatter`, `Bar`, … with the same options as the widgets (`color`, `facet`, `group`, `band`, `baseline`) |
| `bt.plot(spec)` | renders a raw Vega-Lite spec with the theme applied |
| `bt.theme` | tokens, `runColor(id)`, `groupColor(value)`, light/dark |
| `bt.fmt` | number and metric formatting using the view's `metrics` (units, precision) |
| `bt.preact` | Preact with hooks and `htm` (`html` tagged templates, JSX-like without a build step) |
| `bt.lib` | bundled libraries: Vega and Vega-Lite, D3, uPlot, KaTeX |

- **Preact with `htm`** is the recommended way to write blocks: agents write React-style components
  fluently, and state (selections, toggles, detail panels) stays a few lines instead of manual DOM
  updates. Plain DOM code is allowed for simple static blocks; every kit component also exists as a
  plain function (`bt.ui.stat(root, {...})`).
- **Kit first, raw libraries second.** The design guide recommends kit components and `bt.chart`, and
  raw Vega-Lite, D3 or uPlot for what they don't cover. Colors always come from `bt.theme`.
- All libraries are served locally by Beamtime, so views work offline and on a cluster login node.

### Sandbox

- Each custom block runs in its own iframe with `sandbox="allow-scripts"` (no same-origin access) and
  a content security policy that allows scripts only from Beamtime's bundled libraries and no
  network requests.
- Data, images from runs and size changes travel over a `postMessage` bridge, which `bt` wraps.
- This also protects readers from views that someone else committed to a shared repository.

## Built-in blocks

The built-in blocks are Beamtime's own block library, written on the `bt` kit. Each is usable in
two forms with the same name and the same props: as a YAML block in a view, and as a kit component
in custom code (`line` in YAML, `bt.chart.Line` in code).

### Common props

Every block accepts:

| Prop | Meaning |
|---|---|
| `id` | address for validation errors, screenshots and edits |
| `title` | short heading; optional, since many blocks are self-explanatory |
| `caption` | one or two sentences on what the block shows; required on charts |
| `span` | width in a grid: `1` (default), `2` or `full` |
| `from`, `where` | narrow or shift the block's scope relative to the view's; rarely needed |

Fields follow the query language of [layer 3](03-index.md#fields). Two kinds of reference appear in
props:

- **Metric keys** (`val/loss`) where a block plots a series over steps.
- **Fields** (`config.lr`, `metric.val/acc.max`, `run.status`) where a block works with one value per
  run.

### Catalog

**Layout.** These exist in YAML and as kit components; `repeat` only in YAML.

| Block | Purpose |
|---|---|
| `section` | titled group of blocks, collapsible |
| `row` | blocks side by side, wrapping on narrow screens |
| `grid` | auto-fitting grid (`min_width`, or fixed `columns`) |
| `tabs` | alternative contents under one heading; not nested |
| `repeat` | a block of widgets once per value of a field or per subfolder |

**Curves over steps.**

| Block | Purpose | Key props |
|---|---|---|
| `line` | metric curves over steps, time or another metric | `y` (keys), `x`, `color`, `facet`, `group`, `band`, `seeds`, `smooth`, `scale`, `steps`, `highlight` |
| `histogram` | logged distributions over steps (tables with `bin_start`, `bin_end`, `count`) | `key`, `step` (`last`, a step, or `all` as a step-by-bin heatmap) |

**One value per run.**

| Block | Purpose | Key props |
|---|---|---|
| `scatter` | two fields against each other, e.g. learning rate against final accuracy | `x`, `y`, `color`, `size`, `x_scale`, `y_scale`, `fit` (`linear`, `log`, `power`), `seeds` |
| `bar` | a field per category, e.g. accuracy per optimizer | `x` (category), `y`, `group`, `error` (`std`, `stderr`, `minmax`), `sort` |
| `heatmap` | a value over two config axes | `x`, `y`, `value`, `aggregate` (`mean`, `max`, `min`) |
| `parallel` | many config fields and one or two metrics at once | `fields`, `color` |
| `stat` | one number, with delta against the baseline | `field`, `aggregate` (`best`, `mean`, `last`, `count`), `delta` |
| `table` | runs as rows, fields as columns | `columns`, `sort`, `limit`, `highlight_best`, `sparkline` (a metric drawn per row from previews) |
| `compare` | two runs or two groups side by side: config diff and metric deltas | `a`, `b` (run ids or filters), `fields` |
| `importance` | how strongly each config field relates to a target metric, as a sorted bar chart | `target`, `fields` (default: every config key that varies in scope) |

**Logged data.**

| Block | Purpose | Key props |
|---|---|---|
| `data_table` | a table logged by runs | `key`, `step` |
| `images` | logged images, per run or over steps | `key`, `step` (`last`, a step, `slider`) |
| `text` | logged text samples | `key`, `step` |

**Research context.**

| Block | Purpose | Key props |
|---|---|---|
| `proposal` | the folder's proposal: statement, each prediction with its check, current verdict | `of` (default `.`) |
| `folders` | the child groups with proposal, check, verdict, run counts and a chosen field | `field`, `depth` |
| `timeline` | notes and run events in time order | `types`, `limit` |
| `note` | a short text, optionally as a callout (`info`, `warning`, `success`) | `text`, `kind` |
| `output` | the tail of a run's captured output, for failed runs | `run`, `lines`, `stream` (`main`, a rank) |

**Code.**

| Block | Purpose |
|---|---|
| `vega` | a Vega-Lite spec whose named datasets are declared queries; the theme is applied |
| `custom` | a custom block (see [Custom blocks](#custom-blocks)) |

### Hyperparameter importance

`importance` answers "which hyperparameters matter for this metric?" over the runs in scope. It
compiles to the `importance` query of [layer 3](03-index.md#query-kinds), so agents get the same
numbers over MCP. For each field it shows:

- **Correlation**: Spearman rank correlation with the target, signed, for numeric fields.
- **Importance**: the share of the target's variance explained by grouping runs on the field
  (the correlation ratio η²), which works for numeric fields (in quantile bins) and categorical
  ones alike.

Both measures look at one field at a time and miss interactions between fields; the block says so in
its caption and shows how many runs it rests on. Below about ten runs it shows a notice instead of
bars. A model-based importance that captures interactions (e.g. a random forest, as W&B uses) can
follow later.

### Linking blocks

A selection in one block highlights the same runs in every other block of the view: click a run in
the table and its curve stands out in every chart, its point in the scatter plot, its row in other
tables.

- **One shared selection per view**: a set of run ids, held by the page, not by any block.
- **Interactive built-in blocks** (`table`, `scatter`, `heatmap`, `parallel`, `line`, `bar`) write to
  it on click and read it to highlight.
- **Each block decides how to react** with `on_selection`: `highlight` (default; others are dimmed),
  `filter` (show only the selected runs), or `ignore`.
- **Custom blocks** take part through `bt.useSelection()`; the page relays the selection between the
  sandboxed iframes.
- **Clearing**: Escape or a click on empty space. The selection is kept in the URL, so a link
  reproduces it.

### Behavior with one run, many runs and no data

Views are inherited down to single runs and into folders their author never saw, so every block
defines what it does in those cases:

| Situation | Behavior |
|---|---|
| no run in scope logs the field or key | one-line notice naming what is missing |
| a single run | curve blocks, `stat`, `table`, logged-data and context blocks render normally; `scatter`, `bar`, `heatmap` and `parallel` show a notice that they compare runs |
| more than about eight curves | rendered, plus a `validate` lint suggesting `color`, `facet`, `group` or `seeds` |
| more rows than `limit` | the first rows, plus a count of the rest |
| a running run | rendered from current data; values that can still change are marked |

### Schema and descriptions

Every block is a msgspec struct; together they form one tagged union, and the JSON schema served to
agents is generated from it. Each block's schema carries a description written for agents:

```yaml
line:
  description: >
    Curves of one or more metrics over steps (or time, or another metric such as epoch), one per
    run. Use for training dynamics: convergence, instabilities, comparing settings over time.
    Not for one value per run (use scatter or bar) or for more than about eight runs without
    color, facet, group or seeds.
```

### What a block compiles to

YAML blocks are not rendered directly. Each compiles to declared queries ([layer 3](03-index.md))
plus a kit component; for example, `line: {y: val/loss, color: config.lr}` becomes a `series` query
for `val/loss` over the block's scope and a `bt.chart.Line` with `color: "config.lr"`. That is why the
YAML form and the kit form behave identically, and why `validate` can check a YAML block exactly like
custom code.

## The `bt` kit API

The kit is a small, versioned JavaScript API. A custom block declares the major version it was
written for (`kit: 1` next to `code:`); Beamtime keeps serving older majors as long as blocks use
them.

### Entry point

```js
export default function render(root) { ... }
```

`render` is called once with the block's root element. Re-rendering on data changes is handled by
the kit's hooks and component handles, not by calling `render` again.

### Data

| Function | Returns |
|---|---|
| `bt.useData(name, values?)` | Preact hook: the result of a declared query; with `values` for placeholder queries. Re-renders on live updates. |
| `bt.data(name)` | the current result of a prefetched query, synchronously |
| `bt.fetch(name, values)` | a promise for a placeholder query, for plain DOM code |
| `bt.subscribe(name, callback)` | calls `callback(result)` on every update; returns an unsubscribe function |

Every result has the shape of its query kind in [layer 3](03-index.md#answers) plus `status`
(`ready`, `loading` for placeholder queries in flight, `error`) and `meta` (freshness, downsampled or
not, truncated or not). Runs results come as `{columns, rows}` with rows as objects keyed by field;
series results as a list of curves `{run, key, group, x, y}` or, when aggregated or downsampled,
`{x, min, max, last, mean, count}`.

### Components

`bt.ui` (layout and tables) and `bt.chart` (charts) contain every built-in block as a Preact
component with the same props as its YAML form; component names are PascalCase (`bt.ui.Table`,
`bt.chart.Line`). Instead of a declared query generated from YAML, components take their data as a
prop:

```js
html`<${bt.chart.Line} data=${bt.useData("curves")} y="val/loss" color="config.lr" />`
```

Interactive components report events: `onSelect(row)` for tables, scatter, heatmap and parallel
coordinates; `onHover(item)` for charts. They also take part in the view's shared selection (see
[Linking blocks](#linking-blocks)), which custom code reads and sets with
`const [selected, setSelected] = bt.useSelection()` (a set of run ids).

For code without Preact, every component also exists as a function returning a handle:

```js
const table = bt.ui.table(el, {data: bt.data("runs"), columns: ["run.name", "config.lr"]});
table.update({sort: ["-config.lr"]});
table.destroy();
```

### Theme and formatting

| Function | Purpose |
|---|---|
| `bt.theme.tokens` | semantic colors (`fg`, `muted`, `bg`, `surface`, `grid`, `accent`, `good`, `bad`, `warn`), font sizes and spacing |
| `bt.theme.runColor(id)` | the run's color, identical in every block and view |
| `bt.theme.groupColor(field, value)` | a stable color for a group value |
| `bt.theme.scale(kind)` | color scales: `sequential`, `diverging`, `categorical` |
| `bt.theme.mode`, `bt.theme.onChange(cb)` | light or dark, and a callback when it switches |
| `bt.fmt.value(field, v)` | a value formatted with the view's `metrics` config (unit, precision) |
| `bt.fmt.delta(field, v)` | a signed difference, colored by `higher_is_better` |
| `bt.fmt.step(n)`, `bt.fmt.duration(s)` | steps and durations in readable form |
| `bt.label(field)` | the display label of a field or metric key |

The same tokens are available as CSS variables (`--bt-fg`, `--bt-accent`, …) for plain HTML and SVG.

### Vega-Lite, navigation and size

| Function | Purpose |
|---|---|
| `bt.plot(el, spec, {data})` | renders a Vega-Lite spec with the theme's `config` merged in; `data` maps dataset names to query results |
| `bt.link.run(id)`, `bt.link.folder(path)` | URLs for links to runs and folders, opened in the main window |
| `bt.useSize()`, `bt.size` | the block's current width; the iframe's height follows its content |
| `bt.warn(message)` | a warning shown in `validate` results and, in the UI, on the block |
| `bt.useSelection()`, `bt.selection` | the view's shared run selection, as a hook and as `{get, set, subscribe}` |

### Libraries

| Name | Contents |
|---|---|
| `bt.preact` | `h`, `render`, `html` (htm), hooks (`useState`, `useMemo`, `useEffect`, …) |
| `bt.lib.vega`, `bt.lib.vegaLite` | Vega and Vega-Lite |
| `bt.lib.d3` | D3 |
| `bt.lib.uplot` | uPlot, for dense interactive time series |
| `bt.lib.katex` | KaTeX, for formulas |

## Theme

Beamtime owns the look of every view. A theme defines it; views never contain colors, fonts or
sizes, so the same view renders correctly in any theme. Like VS Code, Beamtime ships a clean default
and lets users install or write other themes.

### Tokens

Everything visual is expressed through **semantic tokens**. The web UI, the frame, the built-in
blocks, the generated Vega-Lite `config` and the CSS variables for custom blocks all read the same
tokens.

| Group | Tokens |
|---|---|
| Surfaces | `bg`, `surface`, `surface-raised`, `border`, `grid` |
| Text | `fg`, `muted`, `subtle`, `link` |
| Accent and state | `accent`, `selection`, `dim` (opacity for de-emphasized runs) |
| Status | `good`, `bad`, `warn`, `info`, and per run status: `running`, `finished`, `failed`, `killed`, `lost` |
| Data | `categorical` (10–12 colors for runs and groups), `sequential` and `diverging` scales, `baseline` (color and dash for baseline runs) |
| Type | `font-sans`, `font-mono`, a size scale (`xs` … `xl`), tabular figures for numbers |
| Shape | spacing scale, `radius`, line width, point size |

Custom blocks see them as `bt.theme.tokens` and as CSS variables (`--bt-fg`, `--bt-categorical-3`,
…). Vega-Lite charts get a `config` generated from them; `bt.theme.uplot()` returns matching uPlot
options.

### Theme files

A theme is a JSON file:

```json
{
  "name": "Beamtime Light",
  "type": "light",
  "extends": null,
  "colors": {
    "bg": "#ffffff", "surface": "#f6f8fa", "border": "#d0d7de", "grid": "#eaeef2",
    "fg": "#1f2328", "muted": "#59636e", "accent": "#0969da",
    "good": "#1a7f37", "bad": "#cf222e", "warn": "#9a6700"
  },
  "data": {
    "categorical": ["#0969da", "#d1242f", "#1a7f37", "#bf8700", "#8250df", "#bc4c00", "#1b7c83", "#bf3989", "#59636e", "#2da44e"],
    "sequential": ["#ddf4ff", "#0969da", "#0a3069"],
    "diverging": ["#cf222e", "#f6f8fa", "#0969da"],
    "baseline": {"color": "#59636e", "dash": [4, 3]}
  },
  "fonts": {"sans": "system-ui, -apple-system, 'Segoe UI', sans-serif", "mono": "ui-monospace, 'SF Mono', Menlo, monospace"}
}
```

- **`type`** is `light` or `dark`. Themes come in **pairs** (`Beamtime Light` and `Beamtime Dark`);
  by default the viewer's system preference picks the variant.
- **`extends`** names another theme; only the tokens that differ need to be listed. Missing tokens
  fall back to the default theme, so a minimal theme can be a dozen colors.
- Fonts default to the system font stack, so nothing has to be downloaded and views work offline.

### The default theme

**Beamtime Light** and **Beamtime Dark** are clean and quiet, in the spirit of GitHub's and VS Code's
default themes: neutral grays, one blue accent, the system font, thin grid lines, no shadows or
gradients. Color is reserved for data and status, so it carries meaning wherever it appears.

- The categorical palette is colorblind-safe and tuned separately for light and dark backgrounds.
- A **high-contrast** pair is built in for accessibility.
- A **print** theme is used for static export (PDF, paper figures): white background, black text,
  and the same data colors, matching the scienceplots style used for matplotlib figures.

### Custom themes

- **Choosing a theme**: `theme: atom-one` in the user settings sets a personal default, in a
  project's `beamtime.yaml` the project's default ([settings](01-storage.md#settings)). Each viewer
  can switch theme and light or dark in the UI, stored in their browser; that choice wins for the
  viewer.
- **Where themes come from**: the built-in themes, installed packages
  (`beamtime install git:github.com/someone/beamtime-theme-atom-one`, see [Packages](#packages)), files in
  `~/.config/beamtime/themes/`, and paths in `beamtime.yaml` for project themes.
- **Importing VS Code themes**: `beamtime theme import <vscode-theme.json>` converts a VS Code color
  theme. Workbench colors map to surfaces, text and accent (`editor.background` to `bg`,
  `editor.foreground` to `fg`, `focusBorder` to `accent`, …), and the terminal's ANSI colors become
  the categorical palette. That opens the large ecosystem of VS Code themes (Atom One, Dracula,
  Solarized, Nord, …). The importer fills gaps from the default theme and validates the result.
- **`beamtime theme validate`** checks a theme: all required tokens present after inheritance, text
  contrast of at least 4.5:1, data colors at least 3:1 against the background, categorical colors
  distinguishable from each other, including under simulated color blindness. A theme failing these
  checks is reported with the offending tokens; imported themes often need a tweak to their palette.

### Colors for runs and groups

- **Runs** get a stable color: a hash of the run id picks a preferred slot in the categorical
  palette. Within a view, collisions are resolved by moving later runs (in id order) to the next free
  slot. A run therefore keeps its color across blocks and views as long as it doesn't collide, and
  runs shown together never share a color. More runs than palette colors is the case for `color`,
  `group` or `facet` anyway (see [Many runs in one chart](#many-runs-in-one-chart)).
- **Groups colored by a field** take their colors from the field's type: a categorical field (an
  optimizer name) uses the categorical palette in sorted value order; a numeric field (a learning
  rate) uses the sequential scale, ordered by value, so the colors themselves say "small to large".
- **Baseline runs** always use the theme's `baseline` style.
- **Selection** dims other runs with `dim`, rather than recoloring the selected ones.

### Themes and validation

`view_validate` runs its layout and design checks in the light and the dark variant of the default
theme, so a custom block that hard-codes a color, or only works on white, is caught. Colors in custom
code that don't come from the theme are reported as warnings.

## Block library

Custom blocks that prove useful become **library blocks**: named, described and parameterized, and
usable in any view exactly like a built-in widget. The library grows with the project, so agents
reuse and adapt working blocks instead of starting from scratch.

### Definition

```yaml
# beamtime/blocks/phase-map/20261025-101532-k3m9.yaml
name: phase-map
description: >
  Heatmap of a final metric over two config axes; click a cell to see that run's curves.
  Use for sweeps over two hyperparameters. Not for more than two axes or for single runs.
params:
  x:      {kind: field}
  y:      {kind: field}
  value:  {kind: field}
  curves: {kind: metrics, default: [train/acc, val/acc]}
examples:                                  # parameter sets used for testing the block
  - {x: config.weight_decay, y: config.n_params, value: metric.val/acc.max}
  - {x: config.lr, y: config.batch_size, value: metric.val/loss.min}
queries:
  runs:   {runs: {select: [run.id, $x, $y, $value]}}
  detail: {series: {from: $run, y: $curves}}      # $run remains a runtime placeholder
code: code/3f9a21c0-phase-map.js
kit: 1
derived_from: null                         # set when forked from another block
```

A view uses it like any widget:

```yaml
- phase-map: {x: config.weight_decay, y: config.n_params, value: metric.val/acc.max}
```

- **Params** are fixed when the view is written; **placeholders** (`$run`) stay runtime values.
- The block's JSON schema is generated from `params`, so a use of the block is validated like a
  built-in widget, and `guide` lists library blocks with their descriptions.
- **The built-in widgets are the built-in block library**, written on the same `bt` kit. Built-in
  and project blocks behave identically.

### Location

- Library blocks live in a `blocks/` folder: at the log dir root for the whole project, or in any
  group for that group and below. A block further down overrides one of the same name further up,
  like views. Built-in block names cannot be overridden.
- `blocks/` is a reserved folder name, like `notes/` and `view/`.
- Blocks live in the same source as the views using them, so a view on a remote finds its blocks on
  the remote ([layer 4](04-remotes.md)).
- `beamtime block export` writes blocks as a package; packages are shared and installed as described
  in [Packages](#packages).

### Creating and reusing blocks

| Command (MCP tool) | Does |
|---|---|
| `beamtime block list` (`guide`, `keys`) | blocks available in a folder, with descriptions |
| `beamtime block promote <view> <block-id> <name>` | turns a view's working custom block into a library block |
| `beamtime block fork <name> <new-name>` | copies a block as a starting point; records `derived_from` |
| `beamtime block validate` / `block_save` | checks and saves a new block version (see below) |

`block_save` checks what "generalized" means, mechanically:

- **No hard-coded fields**: string literals in the code that match existing metric or config keys
  are flagged ("`val/acc` is hard-coded; make it a param").
- **A description** with when to use and when not to use is required.
- **Several parameter sets**: the block is rendered with each of its `examples` (at least two) and
  in the usual scopes (its folder, a single run, missing data).
- **No duplicates**: a block with a very similar description or the same queries is pointed out,
  with a suggestion to fork or extend it instead.

### Pinning, upgrades and migrations

Views are **pinned** to the block versions they were saved with. A view is part of the research
record: it should look tomorrow as it does today, unless someone decides to change it. Pinning also
keeps a block update cheap (one save, not a test run over every view) and works for blocks imported
from elsewhere.

- **Pins are written automatically.** `view_save` records the resolved block versions, including
  where each block lives, like a lockfile:

  ```yaml
  uses:
    phase-map: blocks/phase-map@20261025-101532-k3m9
  ```

  The view's body just writes `- phase-map: {...}`; the pin lives only in `uses`.
- **Referenced block versions are never deleted.** Block files are immutable anyway; cleanup skips
  every version a view still pins.
- **Upgrading is a deliberate step per view:**

  ```sh
  beamtime view outdated [folder]                  # views pinned to older block versions
  beamtime view upgrade <view> [--block phase-map] # upgrade one view
  beamtime view upgrade --all --dry-run            # overview, writes nothing
  ```

  `upgrade` applies the migration chain to that view's params, validates the view, renders it in all
  its scopes and shows screenshots before and after. Only if all of this passes does it save a new
  view version with the updated pin. The same is available as MCP tools.
- **A block version can carry a migration** for its params, used by `upgrade`:

  ```yaml
  migrations:
    - from: 20261025-101532-k3m9
      rename: {value: metric}
      add: {band: std}
      map: {curves: "[...value, 'train/loss']"}   # small expressions over the old params
  ```

  Migrations chain, so a view several versions behind is brought forward step by step.
- **Outdated pins are visible.** The UI marks views whose blocks have newer versions, and the guide
  asks agents (default) to check `outdated` when they edit a view anyway and to offer an upgrade.

`block_save` tests only the block itself: its example parameter sets, the scopes, and the
generalization checks above.

## Packages

Themes and block libraries can be shared as **packages** and installed from the command line. The
design follows pi's package manager (`pi install`): source prefixes, conventions instead of required
manifests, personal and project scope, per-package filters, and failures that degrade instead of
blocking.

```sh
beamtime install git:github.com/someone/beamtime-theme-atom-one        # a theme, latest
beamtime install git:github.com/lab/beamtime-physics-blocks@v1.2 -l    # a block library, into the project
beamtime install npm:@lab/beamtime-physics-blocks@1.2.0                 # the same from npm
beamtime install ./my-blocks                                            # a local folder
beamtime serve --with git:github.com/someone/beamtime-theme-nord        # try once, nothing saved
```

### Sources

| Prefix | Source | Pinning |
|---|---|---|
| `git:` | a git repository, optionally a subfolder (`git:github.com/lab/repo/tools/blocks@main`); plain `https://` URLs are treated as git | tags and commits stay fixed; branches are recorded with their commit |
| `npm:` | an npm package, fetched from the registry over HTTP; no Node.js needed | versioned specs stay fixed |
| a path | a local folder, used in place without copying; relative paths resolve from the file that declares them | none |

### Package contents

A package provides **themes** and **blocks** from conventional folders:

```
beamtime-physics-blocks/
  themes/*.json
  blocks/<name>/…          # the layout of a project's block library
```

No manifest is needed for that. A manifest declares other locations or metadata, either as
`beamtime-package.yaml` or, for npm packages, under a `beamtime` key in `package.json`:

```json
{
  "name": "@lab/beamtime-physics-blocks",
  "version": "1.2.0",
  "keywords": ["beamtime-package"],
  "beamtime": {"requires": {"beamtime": ">=1.0", "kit": 1}, "blocks": ["./src/blocks/*"], "themes": []}
}
```

The `beamtime-package` keyword makes npm packages findable, so npm's search serves as the gallery
(`beamtime search` queries it) without a registry of Beamtime's own. `beamtime block export` writes
a project's blocks as a package.

### Personal and project scope

- **Personal** (default): recorded in the user settings, `~/.config/beamtime/settings.yaml`
  ([settings](01-storage.md#settings)), available in every project. The natural place for themes.
- **Project** (`-l`, `--local`): recorded under `packages` in the project's `beamtime.yaml`, so every
  machine running Beamtime for the project (a laptop, a remote, a server) installs the same packages
  from the same pins into its cache on demand.
- **Views must be reproducible**, so `view_save` warns when a view uses a block from a personal
  package and offers to add the package to the project (`beamtime install -l`).
- A project entry replaces a personal entry for the same package. Packages are identified by npm
  name, by repository URL without the ref, or by absolute path, so the same package never loads
  twice.
- **Vendoring** (`--vendor`) copies a package into the log dir, for machines without network access;
  vendored packages travel with the views.

```yaml
# beamtime.yaml
packages:
  - git:github.com/lab/beamtime-physics-blocks@v1.2
  - source: npm:@someone/beamtime-themes
    themes: [themes/nord*.json]       # only these
    blocks: []                        # none
```

### Filtering

Like pi, each package entry can narrow what it loads, per kind: omit the key for everything, `[]` for
nothing, globs to select, `!pattern` to exclude. Filters only narrow what the package offers.

### Names

- Package blocks are used with the package name as prefix, so they never clash with built-in or
  project blocks: `- physics-blocks/phase-map: {...}`. A short alias can be set in the entry.
- Package themes are selected by name: `theme: atom-one`.
- `guide` lists installed package blocks alongside built-in and project blocks, so agents find them.

### Failures

If a package cannot be installed (no network, a removed tag), Beamtime warns, skips it and retries
next time; views using its blocks show error panels for those blocks only. `beamtime install` and
`beamtime update` exit with an error, so scripts notice.

### Safety

- **Nothing runs at install time.** Packages contain data (themes, YAML) and block code, and that
  code only ever runs in the sandbox of [Custom blocks](#sandbox), without network access. There
  are no install scripts and no dependencies that execute.
- **Integrity**: installs are verified against the recorded commit or content hash.
- **Validation on install**: themes are checked with `beamtime theme validate`, blocks render their
  `examples` once. A package with errors is reported and not activated.
- **Project packages are confirmed once.** The first time Beamtime meets packages declared by a
  project (for instance after cloning a repository), it lists them and asks before installing.

### Commands

| Command | Does |
|---|---|
| `beamtime install <source> [-l] [--vendor]` | install and record a package |
| `beamtime serve --with <source>` | use a package for one session without recording it |
| `beamtime remove <source>` | remove it; refuses while project views pin its blocks, unless `--force` |
| `beamtime update` | reconcile installations with the recorded entries; fixed refs don't move |
| `beamtime list` | installed packages with scope, source, version and pin |
| `beamtime search <words>` | packages with the `beamtime-package` keyword on npm |

## Many runs in one chart

A chart shows every run in its scope, one curve per run, each in its stable run color. Beyond about
eight curves that stops being readable. Four chart options handle it:

| Option | Result | Individual runs visible | Good for |
|---|---|---|---|
| `color: <field>` | one chart, curves colored by the field's value | yes | spread and outliers within groups |
| `facet: <field>` | one small chart per value, shared axes | yes | structure within each group |
| `group: [<fields>]` | one aggregated curve per group: mean plus a band (`band: minmax \| std \| stderr \| none`) | no | comparing groups clearly |
| `seeds: config.seed` | shorthand for grouping by every config key except the seed | no | merging repetitions of the same setting |

- **Grouping only makes sense over runs that differ in noise.** If other config keys vary within a
  group (e.g. grouping by optimizer while the learning rate varies), the mean mixes good and bad
  settings and the band shows that spread, not noise. `validate` warns when keys other than the
  seed vary within a group; combining `group` with `facet` resolves it.
- **Groups are averaged per bucket.** Runs log at different steps, so aggregation uses the same
  fixed bucket edges as previews and downsampling (layers 1 and 3).
- **Runs of different length** make the tail of a group curve rest on fewer runs. The number of runs
  per bucket is shown in the tooltip, and the band fades where fewer than half of the group's runs
  contribute.
- **`validate` lints charts with more than about eight curves** and suggests `color`, `facet`,
  `group` or `seeds`.

## Baselines

A view can mark reference runs. Tables then get delta columns, stat tiles show the difference, and
charts draw baseline runs in a distinct style (dashed, neutral color).

```yaml
baseline: {where: {run.tags: {has: baseline}}}           # one baseline for all runs

baseline:                                                # matching baselines for ablations
  where: {config.warmup: 0}
  match: [config.lr, config.seed]
```

- **`where`** selects the baseline runs.
- **`match`** pairs every run with the baseline run that has the same values for the listed keys, so
  "warmup 500, lr 3e-4, seed 2" is compared with "warmup 0, lr 3e-4, seed 2". Without `match`,
  every run is compared with the mean of all baseline runs.
- A run without a counterpart shows no delta; several possible counterparts are a `validate`
  warning.
- The baseline is inherited with the view. Later, predictions can use the same concept
  (`ref: baseline`), so proposals and views compare runs the same way.

## Later

- **Params**: typed variables the reader can change in the UI for declarative widgets (a metric
  picker, a value filter). Custom blocks can already build such controls with placeholder queries;
  for widgets, params are deferred until the renderer and the screenshot loop are stable.
- **Free runtime queries** in custom blocks, if agents need patterns placeholders cannot express.
- **Community gallery in the UI** (post-v1). Settings → Appearance → *Browse community themes* and
  Settings → Blocks → *Browse community blocks*, backed by a central, curated index of community
  packages, as Obsidian does for its plugins and themes:
  - **The index** is a public git repository (`beamtime-community`) with `themes.json` and
    `blocks.json`, each entry naming a package source, author, description and screenshots.
    Contributions arrive as pull requests and are reviewed.
  - **Automated checks on every submission**: the package installs, themes pass
    `beamtime theme validate`, blocks render their `examples` in the sandbox, and screenshots are
    present.
  - **Previews before installing**: themes are data, so the UI can apply one to a sample view live;
    blocks render their examples on synthetic data in the sandbox.
  - **Installing from the UI** does exactly what `beamtime install` does (personal by default,
    project on request), and `beamtime search` queries the same index.

  v1 prepares for it: the package format and the install logic live in the core library, and
  `serve` exposes install, remove and list in its API ([layer 4](04-remotes.md#protocol)), so the UI
  can call them later. Until the index exists, npm's `beamtime-package` keyword serves as the gallery.

## Agent loop

The same loop is available as MCP tools and as CLI commands:

| MCP tool | CLI | Does |
|---|---|---|
| `keys`, `guide` | `beamtime keys`, `beamtime guide` | what exists in the folder; the design guide, examples and defaults |
| `view_validate` | `beamtime view validate` | checks a draft (see below) and returns structured findings: error or warning, block id, location, suggested fix |
| `view_render` | `beamtime view render` | screenshots of the page and of each block, optionally per scope; MCP returns images directly, the CLI writes PNGs |
| `view_save` | `beamtime view save` | writes the draft as a new version into `view/` |

1. Read `keys` and `guide`.
2. Write a draft: the view YAML, custom code, data files.
3. `view_validate` and fix until no errors remain.
4. `view_render`, look at the screenshots, answer the checklist, improve; one or two rounds.
5. `view_save`.

**Drafts** live outside `view/` (in the cache, or a path the agent chooses), so iterating creates no
versions; only `save` does, and the history holds intended states only.

**Rendering runs where the agent works**, usually on the laptop, with a headless browser
(Playwright with Chromium, part of the `serve` install). For a remote folder, the renderer gets its
data through remote queries ([layer 4](04-remotes.md)) and `save` sends the version to the remote,
like every write.

### Validation

`view_validate` runs three stages and stops at the first that has errors:

1. **Static.** View schema; every query parses, its fields exist and placeholder types are sound;
   custom code parses and exports `render`; no imports outside `bt`; no network APIs; code size
   below a limit; no inline numeric data beyond a small limit, so numbers come from queries.
2. **Rendered, in several scopes.** The view is rendered headless in:
   - the folder it is defined for;
   - a single run below it, because views are inherited down to runs;
   - a folder where its data is missing (an empty or synthetic scope), because inherited views meet
     folders their author never saw.

   In each scope: no exceptions, no console errors, rendering within a time limit, no blank blocks,
   placeholder queries exercised once with example values from the folder, and the shared
   selection set once to a run from the folder, so highlighting code runs too. The most dangerous
   failure of free code is working exactly where it was written and breaking elsewhere; this stage
   targets it.
3. **Layout and design checks**, measured in the browser without a model: content overflowing its
   block, clipped text, overlapping elements, insufficient contrast, colors that don't come from the
   theme, charts with more than about eight curves.

Screenshot critique with the checklist (clipped labels, readable legend, distinguishable runs, title
matches content, no empty areas) is the agent's own step after validation passes.

### At display time

If a custom block throws in a reader's browser anyway, only that block is replaced by an error panel
naming it; the frame and every other block stay intact. The panel links to the block's code and the
error, so an agent can fix it.

## Agent instructions

Agents get Beamtime's instructions from `beamtime guide` in the CLI and the `guide` tool in MCP: the
design guide, example views (with custom blocks), the kit reference, anti-patterns and default
behavior.

**Users override defaults where they already keep agent instructions**, not in a Beamtime-specific
file: a repo's `CLAUDE.md` or `AGENTS.md`, a global instruction file, or a nested file in a
subfolder. Agents load these files themselves and weigh them above tool output, so an override
needs no mechanism in Beamtime. For that to work, the guide:

- **marks its defaults as defaults**, e.g. "default: custom blocks may be used without asking", so an
  agent can tell which statements a user may change;
- **asks agents to reuse first and generalize second** (default): check the library before writing a
  block, fork the closest block if none fits, and save a generalized version of any new block that
  solves a problem likely to recur (fields as params, working for one run and many, degrading on
  missing data); one-off blocks stay in their view;
- **says that the user's own instructions take precedence** over these defaults.

By default, agents use widgets and custom blocks freely. Beamtime's documentation offers a short
snippet for users who want something else:

```markdown
## Beamtime
- Ask me before adding custom blocks to a view.
- In beamtime/scaling/, plot every result against config.n_params on log-log axes.
```

If Beamtime later starts agents itself, e.g. from a button in the web UI, those agents won't see the
user's instruction files. A setting in `beamtime.yaml` pointing to them can solve that then.

## Evaluation (outline)

A harness like the query-form experiment, with tasks from realistic log dirs. Layers: validation
pass rate and rounds, data fidelity of the queries, a per-task checklist judged on screenshots, and
occasional human pairwise preference to calibrate the judge. It also answers open design questions
empirically, such as examples versus rules, or whether a second screenshot round pays off.

## Decisions

- Agents build views freely: declarative widgets and custom code blocks are both first-class, and
  custom blocks need no user consent by default; users can restrict this in their own instructions.
- Custom blocks are ES modules in a sandboxed iframe, built on the `bt` kit with Preact and `htm`;
  bundled libraries are Vega and Vega-Lite, D3, uPlot and KaTeX, all served locally.
- All data comes through declared queries; placeholders supply values at runtime. There is no free
  query API.
- `view_validate` renders every draft headless in several scopes (its folder, a single run, missing
  data) before layout checks and screenshots.
- Drafts live outside `view/`; only `view_save` creates a version. Rendering runs where the agent
  works.
- `repeat` for blocks and `facet`, `color`, `group`, `seeds` for charts are in v1; params come later.
- Views are nested trees with optional ids.
- Baselines are first-class, with optional matching.
- The built-in catalog has about 25 blocks, each usable in YAML and as a kit component with the same
  props, including `importance` (correlation and η² per config field).
- Blocks are linked through one shared run selection per view, in v1.
- Themes are token sets in JSON files with light and dark pairs and inheritance; the default is
  clean and quiet (GitHub/VS Code style); VS Code themes can be imported; the viewer's choice wins
  over the project default.
- Run colors are stable by hash with collision resolution within a view; numeric fields color by a
  sequential scale.
- Themes and block libraries are packages, installed pi-style with `beamtime install` from `git:`,
  `npm:` or local paths, personal by default and per project with `-l`. Nothing runs at install
  time; npm's `beamtime-package` keyword is the gallery.
- Reusable blocks form a project library in `blocks/` folders, inherited down the tree and used like
  widgets. Built-in widgets are the built-in library on the same kit.
- Views are pinned to block versions (`uses`, written on save). Upgrades are deliberate, per view
  (`view upgrade`), with migrations, validation, rendering in all scopes and before/after
  screenshots.
- Agents are instructed to reuse library blocks first and to save generalized versions of new
  blocks.
