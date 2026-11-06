# Layer 5: Views

Status: **reviewed; v1 scope per the [overview](00-overview.md#scope)**

A view is what a group shows: a page that agents build freely, from declarative widgets and from
their own code.
[Layer 1](01-storage.md#views-in-storage) fixes where views live and how they are versioned; [layer 3](03-index.md#query-language) defines the queries they get their data from.

## Prior art: dashboards as code

| Tool | Format and layout | Data binding | Interactivity | Lesson |
|---|---|---|---|---|
| W&B workspaces and reports | Server-held JSON, editable via Pydantic classes; sections of panels, reports as blocks plus panel grids with `x, y, w, h` | the container owns a run set (filters, grouping); panels only name metric keys | run selection, grouping and smoothing cascade to all panels | closest to Beamtime's group-relative views; not diffable; panels with unknown keys render blank |
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

1. **Agents build views freely; robustness comes from contracts, building blocks and checks.** Custom
   code is a first-class part of a view. What keeps views correct and consistent is the data contract
   (declared queries), Beamtime's kit and theme, the sandbox, and validation before saving.
2. **The view owns the data context.** A view's scope is the viewed group plus view-level filters.
   All data, for widgets and custom code alike, comes through declared queries relative to that
   scope, so live updates work everywhere.
3. **Two ways to build, freely mixed.** Declarative widgets are the fast path: the agent states intent
   (`line: {y: val/loss, color: config.lr}`) and Beamtime produces the chart with correct defaults.
   Custom blocks are code for everything else.
4. **Beamtime owns the look.** One theme drives widgets, the kit, the charts' style and CSS
   variables. Views contain no colors, fonts or pixel sizes; custom code takes them from the theme.
5. **Few layout primitives, no coordinates**: section, row, auto-fitting grid, tabs (not nested), and
   `repeat` (wave 2). Inside a custom block, layout is the agent's.
6. **Strict, deterministic validation first.** Errors carry the block id, the location and a
   suggested fix. Screenshots come after, as the agent's own check.
7. **Everything addressable.** Every node can carry an `id`, used by validation errors, screenshots
   and edits.
8. **Degrade, never break.** A block without data in the viewed group shows a one-line notice; a
   custom block that throws shows an error panel; the frame and every other block stay intact.

## The view format

```yaml
schema: 1
title: Grokking under weight decay
finding: Generalization jumps once weight decay exceeds 0.1, independent of model size.
author: claude-opus-5-5
user: ada

filters:
  run.status: {ne: failed}

metrics:
  val/acc: {label: Validation accuracy, unit: "%", higher_is_better: true}
  train/loss: {label: Training loss, scale: log}

body:
  - row:
      - stat: {id: best-acc, field: metric.val/acc.max, aggregate: best}
      - stat: {id: runs, aggregate: count}
  - custom:
      id: grokking-map
      code: code/3f9a21c0-grokking-map.js
      kit: 1
      libs: [d3]
      queries:
        runs:   {runs: {select: [run.id, config.weight_decay, config.n_params, metric.val/acc.max]}}
        detail: {series: {from: $run, y: [train/acc, val/acc]}}
  - line: {id: by-wd, y: val/acc, by: [config.weight_decay], band: std,
           caption: Validation accuracy per weight decay, mean and spread over runs.}
  - phase-map: {x: config.weight_decay, y: config.n_params, value: metric.val/acc.max}

uses:                                    # written by view_save
  phase-map: blocks/phase-map@20261025-101532-k3m9
```

- **A nested tree.** Layout nodes contain blocks; any node may carry an `id`. Agents write and edit a
  file with ordinary tools, where a nested tree reads better than a flat list plus a layout.
- **`finding`** is the one-sentence key result, shown in the frame ([layer 7](07-web-ui.md#shell)).
- **`filters`** narrow every query of the view; `metrics` gives labels, units, scales and
  `higher_is_better`, so widgets, the kit and axes agree.
- **A page shows its own view.** A group or run shows its own newest view, else Beamtime's built-in
  default; views are not inherited by subgroups or runs, so a sweep's view never turns up as a
  one-row table on a run page.
- **`author`** and **`user`** identify who saved the version.
- **`custom`** is a block of agent code ([Custom blocks](#custom-blocks)); its `code` path is relative
  to the `view/` folder. Library blocks are used by name, like widgets ([Block library](#block-library)).
- **`uses`** pins library block versions; `view_save` writes it.
- **Nodes** are one-key mappings from the block name to its props (`- line: {y: val/loss}`). A layout
  takes its children as a list (`- row: [...]`), or as `children` next to its own props
  (`- grid: {columns: 2, children: [...]}`). `tabs` takes sections; each section is a tab, named by its
  `title`. A node without `id` gets one from its block and main prop (`line-val-loss`), numbered when
  that repeats.

### Data

- Every query a block uses is **declared in the YAML**, in the object form of
  [layer 3](03-index.md#query-language), relative to the viewed group. Widgets declare theirs
  implicitly; custom blocks list them under `queries`.
- Queries without placeholders are **prefetched** and kept live: when runs change, the affected
  queries are re-run and the block re-renders.
- Queries may contain **placeholders** (`$run`, `$start`, `$end`). Their shape is fixed and validated
  statically; only values are supplied at runtime (`bt.useData("detail", {run: id})`), checked
  against the placeholder's type. This covers clicking into a run, step-window sliders and
  selections.
- **Data files** stored with the view (`view/data/<sha8>-<name>.parquet`) are read through the `file`
  query ([layer 3](03-index.md#query-kinds)). They describe the group that defines the view. Their
  provenance (the script that made them) is recorded in a note.
- There is no free query API: code cannot read files, call the network or query anything it hasn't
  declared.

## Built-in blocks

The built-in blocks are Beamtime's own block library, written on the `bt` kit. Each exists with the
same name and props as a YAML widget and as a kit component (`line` in YAML, `bt.chart.Line` in
code).

### Common props

| Prop | Meaning |
|---|---|
| `id` | address for validation errors, screenshots and edits |
| `title` | a short heading; optional |
| `caption` | one or two sentences on what the block shows; required on charts |
| `span` | width in a grid: `1` (default), `2` or `full` |
| `from`, `where` | narrow or shift the block's scope; rarely needed. `from` is relative to the page (`.`, `sub/group`) or a run id |
| `depth` | `1` for the runs directly in the group only, leaving out subgroups' runs |

Props reference **metric keys** (`val/loss`) where a block plots a series over steps, and **fields**
(`config.lr`, `metric.val/acc.max`, `run.status`; [layer 3](03-index.md#fields)) where it works with
one value per run.

### Catalog

Wave 1 is in v1; wave 2 follows in v1.1 ([overview](00-overview.md#scope)).

**Layout**: `section` (titled, collapsible), `row` (side by side, wrapping), `grid` (auto-fitting by
`min_width`, or fixed `columns`), `tabs` (not nested); wave 2: `repeat` (a block of widgets per value
of a field or per subgroup, each narrowed to its runs; `$value` names the value in captions).

**Curves over steps**

| Block | Wave | Purpose | Key props |
|---|---|---|---|
| `line` | 1 | metric curves over steps, time or another metric | `y`, `x`, `color`, `by`, `band`, `seeds`, `smooth`, `raw`, `scale` (`linear`, `log`, `symlog`), `ymin`, `ymax`, `steps`, `outliers`, `legend`; wave 2: `facet`, `highlight` |
| `histogram` | 1 | a logged distribution (a table with `bin_start`, `bin_end`, `count`), one outline per run | `key`, `step` (`last` or a step); wave 2: `all` as a step-by-bin heatmap |

**One value per run**

| Block | Wave | Purpose | Key props |
|---|---|---|---|
| `scatter` | 1 | two fields against each other | `x`, `y`, `color`, `x_scale`, `y_scale`, `fit` (`linear`, `log`, `power`), `seeds`; wave 2: `size` |
| `bar` | 1 | a field per category | `x`, `y`, `by`, `error` (`std`, `stderr`, `minmax`), `sort` |
| `stat` | 1 | one number | `field`, `aggregate` (`best`, `mean`, `last`, `count`); wave 2: `delta` against the baseline |
| `table` | 1 | runs as rows, fields as columns | `columns`, `sort`, `limit`, `highlight_best`, `sparkline` (a metric per row, from previews) |
| `heatmap` | 2 | a value over two config axes | `x`, `y`, `value`, `aggregate` (`mean`, `max`, `min`) |
| `parallel` | 2 | many config fields and one or two metrics | `fields`, `color` |
| `compare` | 2 | two runs or groups: config diff and metric deltas | `a`, `b` (run ids or `where` filters), `fields` |
| `importance` | 2 | how strongly config fields relate to a target metric | `target`, `fields` |

**Logged data**: `data_table` (`key` and `step`, or `file` for a data file stored with the view;
`limit`), `images` (`key`, `step`: `last` or a step; wave 2: `slider`), `text` (`key`, `step`). All
wave 1.

**Research context** (wave 1)

| Block | Purpose | Key props |
|---|---|---|
| `proposal` | the group's proposal: statement, each prediction with result, effect and interval, plan progress, research status, verdict, superseded versions | `of` (default `.`) |
| `memory` | the group's memory, with its links | `of` |
| `groups` | the child groups with status, check, verdict, run counts and a chosen field | `depth` |
| `timeline` | notes and run events in time order | `types`, `limit` |
| `note` | a short text, optionally as a callout (`info`, `warning`, `success`) | `text`, `kind` |
| `markdown` | a text panel in Markdown with math, edited in place in the UI | `text` |
| `notes` | the newest notes, current versions only | `types`, `limit` |
| `output` | the tail of a run's captured output | `run`, `lines`, `rank`, `open` |
| `config` | a run's config as a tree (filter, what varies marked), or on a group the config keys that differ between its runs | `run`, `open` |

**Code** (wave 1): `custom`. There is no free chart-spec block: charts beyond the widgets are custom
blocks on `bt.chart` (uPlot) or D3 ([Charts](#charts)).

### `importance` (wave 2)

For each config field: the Spearman rank correlation with the target (numeric fields) and the share
of the target's variance explained by grouping on the field (η², numeric fields in quantile bins). It
compiles to the `importance` query, so agents get the same numbers over MCP. Both measures look at
one field at a time and miss interactions; the block says so and shows how many runs it rests on.
Below about ten runs it shows a notice instead of bars.

### Linking blocks (wave 2)

A selection in one block highlights the same runs in every other block of the view. One shared
selection per view (a set of run ids, kept in the URL); interactive blocks (`table`, `scatter`,
`heatmap`, `parallel`, `line`, `bar`) set it on click; each block reacts with `on_selection`:
`highlight` (default), `filter` or `ignore`. Custom blocks take part through `bt.useSelection()`.

Part of this arrived early, in v1: hovering a run highlights it in every block of the view (table
rows, legends, charts), and hiding a run hides it in every chart ([layer 7](07-web-ui.md#charts)).

### Behavior with one run, many runs and no data

| Situation | Behavior |
|---|---|
| no run in scope logs the field or key | a one-line notice naming what is missing |
| a single run | curves, `stat`, `table`, logged data and context blocks render normally; `scatter`, `bar`, `heatmap`, `parallel` show a notice that they compare runs |
| more than about eight curves | rendered, plus a `validate` lint suggesting `color`, `by`, `seeds` or `facet` |
| more rows than `limit` | the first rows and a count of the rest |
| a running run | rendered from current data; values that can still change are marked |

### Schema and compilation

Every block is a msgspec struct; together they form one tagged union, and the JSON schema served to
agents is generated from it. Each block's schema carries a description written for agents, with
when to use and when not to use it.

YAML blocks compile to declared queries plus a kit component: `line: {y: val/loss, color: config.lr}`
becomes a `series` query for `val/loss` over the block's scope and a `bt.chart.Line` with
`color: "config.lr"`. The YAML form and the kit form therefore behave identically.

## Many runs in one chart

A chart shows every run in its scope, one curve per run in its stable run color. Beyond about eight
curves that stops being readable:

| Option | Result | Runs visible | Good for |
|---|---|---|---|
| `color: <field>` | curves colored by the field's value | yes | spread and outliers within a setting |
| `by: [<fields>]` | one curve per combination of values: mean plus a band (`band: minmax \| std \| stderr \| none`) | no | comparing settings |
| `seeds: config.seed` | aggregating by every config key except the seed | no | merging repetitions |
| `facet: <field>` (wave 2) | one small chart per value, shared axes | yes | structure within each value |

- **Aggregating only makes sense over runs that differ in noise.** `validate` warns when keys other
  than the seed vary within an aggregate.
- **Aggregates are averaged per bucket**, on the fixed bucket edges of previews and downsampling.
- **Runs of different length**: the tooltip shows how many runs contribute per bucket, and the band
  fades where fewer than half of the aggregate's runs contribute.

## Baselines (wave 2)

A view can mark reference runs; tables get delta columns, stat tiles show the difference, and charts
draw baselines dashed and neutral.

```yaml
baseline: {where: {run.tags: {has: baseline}}}        # one baseline for all runs
baseline: {where: {config.warmup: 0}, match: [config.lr, config.seed]}   # matching, for ablations
```

`match` pairs every run with the baseline run that has the same values for the listed keys; without
it, runs are compared with the mean of all baseline runs. A run without a counterpart shows no delta;
several possible counterparts are a `validate` warning. Baselines belong to views only; predictions
compare with their own `a` and `b` ([research record](09-research-record.md#predictions)).

## Custom blocks

A custom block is an ES module written by the agent, stored with the view as
`view/code/<sha8>-<name>.js` (immutable, named by content hash).

```js
// grokking-map.js
const {html} = bt.preact;

function GrokkingMap() {
  const runs = bt.useData("runs");
  // the run hovered in this table or any chart of the page, else the first one.
  const selected = bt.useHovered() ?? runs.rows[0]?.["run.id"];
  const detail = bt.useData("detail", {run: selected});
  return html`
    <${bt.ui.Grid} columns=${2}>
      <${bt.ui.Table} data=${runs} columns=${["config.weight_decay", "metric.val/acc.max"]} />
      <${bt.chart.Line} data=${detail} y=${["train/acc", "val/acc"]}
                        caption="Train and validation accuracy of the selected run." />
    <//>`;
}

export default function render(root) {
  bt.preact.render(html`<${GrokkingMap} />`, root);
}
```

### The `bt` kit API

The kit is a small, versioned JavaScript API. A block declares the major version it was written for
(`kit: 1`); Beamtime keeps serving older majors as long as blocks use them. The kit exists only as
Preact components and functions; there is no separate imperative widget API.

**Entry point.** `export default function render(root)` is called once; re-rendering on data changes
is handled by the kit's hooks.

**Data**

| Function | Returns |
|---|---|
| `bt.useData(name, values?)` | hook: the result of a declared query, with `values` for placeholders; re-renders on updates |
| `bt.data(name)` | the current result of a prefetched query |
| `bt.subscribe(name, callback)` | calls `callback(result)` on every update; returns an unsubscribe function |

Results carry `status` (`ready`, `loading`, `error`) and `meta` (freshness, downsampled, truncated).
The kit reshapes the columnar answers of layer 3 for code: runs as `{columns, rows}` with rows as
objects keyed by field; curves as a list of `{run, key, group, x, y}` or, aggregated or downsampled,
`{run, key, group, x, min, max, last, mean, count}`.

**Components.** `bt.ui` holds layout, tables, stats and context blocks (`Grid`, `Row`, `Tabs`,
`Section`, `Table`, `Stat`, `Note`, `Config`, `Images`, …); `bt.chart` holds charts (`Line`, `Scatter`, `Bar`,
`Histogram`, and in wave 2 `Heatmap`, `Parallel`, `Importance`). Each has the props of its YAML form
and takes its data as a prop. The run hovered anywhere on the page is shared: `bt.hover(run)` sets
it, `bt.useHovered()` follows it (row selection callbacks on components come later).

**Theme, formatting and the rest**

| Function | Purpose |
|---|---|
| `bt.theme.tokens` | the theme's colors; also as CSS variables (`--ink`, `--muted`, …) |
| `bt.theme.runColor(id)`, `bt.theme.groupColor(field, value)` | stable colors for runs and group values |
| `bt.theme.runDash(id)` | a run's line style |
| `bt.theme.scale(kind)` | the colormaps as `sequential`, `diverging`; `categorical` |
| `bt.theme.mode`, `bt.theme.onChange(cb)` | light or dark, and a callback when it switches |
| `bt.fmt.value(v)` | values formatted compactly (full values in tooltips) |
| `bt.fmt.step(n)`, `bt.fmt.duration(s)`, `bt.label(field)` | readable steps, durations and labels |
| `bt.chart.line(el, spec)` | draws curves on uPlot with the theme's axes, grid, fonts and run colors; synced crosshair, hover focus, zoom ([Charts](#charts)) |
| `bt.link.run(id)`, `bt.link.group(path)` | URLs to runs and groups, opened in the main window |
| `bt.useSize()` | the block's width |
| `bt.warn(message)` | a warning shown by `validate` and on the block |
| `bt.useSelection()` (wave 2) | the view's shared run selection |
| `bt.preact` | `h`, `render`, `html` (htm), hooks |
| `bt.lib` | the libraries listed in the block's `libs`: `d3`, `uplot`, `katex` |

### Sandbox

- Each custom block runs in its own iframe with `sandbox="allow-scripts"` (no same-origin access) and
  a content security policy that allows scripts only from Beamtime's static files and no network
  requests. Data, run images and size changes travel over a `postMessage` bridge, which `bt` wraps.
- **Static library files are public.** A sandboxed iframe has no origin and sends no token, so the
  bundled JavaScript is served without the token of mode 2 ([layer 7](07-web-ui.md#security)); data
  only ever arrives through the bridge.
- **Each block loads only the libraries it declares** in `libs`. Preact and the kit are small; D3,
  uPlot and KaTeX load only where needed, from the browser cache after the first block.
- **Height** follows the content through the bridge, with a guard against resize loops: a block whose
  height keeps changing is fixed at its last height and reported by `bt.warn`.
- Sandboxing protects readers from views that others committed to a shared repository.
- **The code travels over the bridge.** The page fetches a block's code with the token and posts its
  text into the frame (`/static/kit/frame.html`), which imports it from a `blob:` URL; code files
  never get a public URL. Inside the frame, the kit's data hooks are subscriptions the page answers
  from its own cache, so live updates reach custom blocks like any other block; only reading
  operations pass the bridge.

### Charts

Every chart is drawn by **uPlot**: the built-in widgets, `bt.chart` in custom blocks, and the default
view. One small chart library keeps the dependencies few and the charts consistent, and it stays fast
with hundreds of runs and thousands of points per curve.

- **Data only from declared queries.** uPlot draws arrays it is given and loads nothing itself, so no
  URL loading or expression evaluation has to be locked down.
- **The theme styles the charts**: axes and grid from `muted` and `line`, fonts from the type tokens,
  run colors from the categorical palette, bands from the run color with transparency.
- **Interactions** (synced crosshair, hover focus, legend toggles, zoom with exact refetch, smoothing,
  aggregation, settings per chart and per view) are described in [layer 7](07-web-ui.md#charts).
- **Figures** leave in the light theme: PNG on a transparent or white background, CSV, and a
  vector PDF drawn by the server with matplotlib in the project's `figure_style` style sheets
  (scienceplots' `[science, nature]` by default; the `figures` extra). `figure_style` may also
  name the project's own `.mplstyle` files by their path from the project root, and the settings
  page lists them next to the built-in sheets.
- Wave-1 widgets beyond curves (`scatter`, `bar`, `histogram`) use uPlot's point and bar paths.

## Theme

Beamtime owns the look of every view; views never contain colors, fonts or sizes. The design system
([design/README.md](../../design/README.md)) defines it, and `design/tokens.json` is its source of truth.

### Tokens

| Group | Tokens |
|---|---|
| Surfaces | `paper`, `surface`, `line`, `border` |
| Text | `ink`, `muted` |
| Accent and state | `accent`, `good`, `bad`, `warn` |
| Data | `data-1` to `data-6` with line styles `dash-1` to `dash-6` |
| Type | `serif`, `sans`, `mono`; the styles `title`, `heading`, `statement`, `prose`, `caption`, `body`, `small`, `number`, `code` |
| Shape | `space-1` to `space-4`, `radius`, `radius-pill`, `margin`, `measure`, `measure-short`, `stroke-data`, `stroke-rule`, `stroke-icon` |

The web UI, built-in blocks, the chart style and the CSS variables of custom blocks all read the same
tokens. Type styles are classes in the markup; stylesheets never set a size.

### Theme files

```json
{"schema": 1, "name": "Atom One Dark", "type": "dark",
 "colors": {"paper": "#282c34", "ink": "#abb2bf", "accent": "#61afef"}}
```

- A theme recolors the fixed layout: **colors only**, by token name, as `#rrggbb`. Tokens it leaves out
  keep the default of its `type`. Fonts, sizes and spacing can't be themed, because type classes fix them.
- **`type`** is `light` or `dark`. `x-light.json` and `x-dark.json` form the pair `x`; a single file is
  used in both modes.
- **Where themes come from**: `~/.config/beamtime/themes/` for the user's own, and `themes/` next to
  `beamtime.yaml` for a project's. `beamtime` is the built-in pair from the tokens.
- **Choosing**: `theme:` in the user settings or the project's `beamtime.yaml`
  ([layer 1](01-storage.md#settings)); a viewer's choice of mode in the UI wins for that viewer.
- Unknown tokens and bad values are reported on the settings page and ignored.

### The default theme

Warm and quiet, like a lab notebook: off-white paper (`#faf9f6`) or warm charcoal (`#1e1e1c`), ink
rather than black, one ink-blue accent, no gradients. XCharter for what people read, IBM Plex Sans for
the interface, IBM Plex Mono for code and margin labels; the fonts ship with the frontend. Color is
reserved for data and status. Exported figures use the light variant.

### Colors for runs and groups

- **Runs** get a stable style: a hash of the run id picks a preferred slot of six; within a view,
  collisions move later runs (in id order) to the next free slot. A slot is a color and a line style,
  in charts, legends and table swatches alike. Beyond six runs, slots repeat: group runs instead.
- **Groups** colored by a categorical field use the same slots in sorted value order; by a numeric field
  with more than six values, the `colormap` setting ordered by value.
- **Colormaps** are matplotlib's, sampled into `src/beamtime/views/colormaps.json` by
  `scripts/colormaps.py`. `colormap` and `colormap_diverging` choose them; `bt.theme.scale` reads them.
- **Selection** dims other runs to a fixed 20 %.

## Block library

Custom blocks that prove useful become **library blocks**: named, described and parameterized, and
usable in any view like a built-in widget.

### Definition

```yaml
# beamtime/blocks/phase-map/20261025-101532-k3m9.yaml
schema: 1
name: phase-map
description: >
  Heatmap of a final metric over two config axes; click a cell to see that run's curves.
  Use for sweeps over two hyperparameters. Not for more than two axes or for single runs.
params:
  x:      {kind: field}
  y:      {kind: field}
  value:  {kind: field}
  curves: {kind: metrics, default: [train/acc, val/acc]}
examples:
  - {x: config.weight_decay, y: config.n_params, value: metric.val/acc.max}
  - {x: config.lr, y: config.batch_size, value: metric.val/loss.min}
queries:
  runs:   {runs: {select: [run.id, $x, $y, $value]}}
  detail: {series: {from: $run, y: $curves}}      # $run remains a runtime placeholder
code: code/3f9a21c0-phase-map.js                  # relative to the block's group
kit: 1
libs: [d3]
derived_from: null
author: claude-opus-5-5
user: ada
```

A view uses it like a widget: `- phase-map: {x: config.weight_decay, y: config.n_params, value: metric.val/acc.max}`.
Params are fixed when the view is written; placeholders stay runtime values. The block's schema is
generated from `params`, so uses are validated like built-in widgets, and `guide` lists library
blocks with their descriptions.

### Location

- Library blocks live in `blocks/<name>/` at the log dir root (the whole project) or in any group
  (that group and below). A block further down overrides one of the same name further up; built-in
  names cannot be overridden.
- Blocks live in the same source as the views using them, so a remote view finds its blocks on the
  remote.
- `beamtime block export <name> [group] --to <dir>` writes `<dir>/blocks/<name>/` with every version
  and its code; `beamtime block import <group> --from <path | git-url[@ref]>` copies the
  `blocks/<name>/` folders of a project, an exported folder or a git repository (cloned shallowly)
  into the group, keeping version ids so pins stay valid, and records the source and commit in
  `blocks/<name>/_imported.json`. Exporting into a git repository makes a shareable library; both are
  user commands.

### Creating and reusing blocks

| CLI | MCP | Does |
|---|---|---|
| `beamtime block list [group]` | `block_list` | blocks available in a group, with descriptions |
| `beamtime block promote <view> <block-id> <name>` | `block_promote` | turns a view's working custom block into a library block |
| `beamtime block fork <name> <new-name>` | `block_fork` | copies a block as a starting point; records `derived_from` |
| `beamtime block show <name> [group] [--version]` | `block_show` | a block's definition and code |
| `beamtime block validate <draft>` | `block_validate` | checks a block draft |
| `beamtime block save <draft>` | `block_save` | saves a new block version |

Block drafts live in `.beamtime/drafts/blocks/<name>/` (`block.yaml` and `code.js`); `promote` and
`fork` write one, and `save` writes the version into `blocks/<name>/` of the log dir root, or of
`--group`.

`block_validate` and `block_save` check what "generalized" means:

- **No hard-coded fields**: string literals in the code that match existing metric or config keys are
  flagged ("`val/acc` is hard-coded; make it a param").
- **A description** with when to use and when not to use.
- **At least two `examples`**, each validated statically and, where a browser is available, rendered
  once in the group the block is saved in.
- **No duplicate queries**: a block whose declared queries equal an existing block's is pointed out.

### Pinning and upgrades

Views are **pinned** to the block versions they were saved with, so a view looks tomorrow as it does
today unless someone decides to change it.

- `view_save` writes the resolved versions into `uses`; referenced block versions are never deleted.
- `beamtime view outdated [group]` lists views pinned to older block versions; the UI marks them.
- `beamtime view upgrade <view> [--block <name>]` re-pins to the newest version and validates the
  view. If the new version's params differ, validation reports what to change, the agent adjusts
  the view, and saves it. Automatic param migrations are a later addition.
- The guide asks agents (default) to check `outdated` when they edit a view and offer an upgrade.

## Agent loop

The loop is available as MCP tools and CLI commands ([layer 8](08-cli-mcp.md)):

| MCP | CLI | Does |
|---|---|---|
| `keys`, `guide` | `beamtime keys`, `beamtime guide` | what exists in the group; the design guide |
| `view_new` | `beamtime view new <group> [--from <example>] [--name <draft>]` | starts a draft: from an example, else from the group's current view (its own, or the built-in default written out as YAML) |
| `view_validate` | `beamtime view validate <draft>` | structured findings: error or warning, block id, location, suggested fix |
| `view_render` | `beamtime view render <draft>` | screenshots of the page and of each block as JPEG, the page capped to 2,520 px tall and the rest named in `cut`; the CLI writes the files, MCP returns images |
| `view_save` | `beamtime view save <draft>` | writes the draft as a new version into `view/` |

1. Read `keys` and `guide`; check the library.
2. Write a draft: the view YAML, custom code, data files.
3. `view_validate` until no errors remain.
4. `view_render`, answer the screenshot checklist, improve; at most two rounds.
5. `view_save`.

**Drafts** live outside `view/`, in `.beamtime/drafts/<name>/` of the project root (`view.yaml`, and
`data/` for data files), so iterating creates no versions and agents edit drafts with their own file
tools. `.beamtime/` carries its own `.gitignore`, so drafts stay out of git. `view_new` records the draft's group in
`_draft.json`; the other operations take the draft's name. **Rendering runs where the agent works**, with the headless renderer of
[layer 7](07-web-ui.md#screenshots-and-the-headless-renderer); for a remote group, data comes
through remote queries and `save` sends the version to the remote. **The draft stays with the
agent; the check and the write happen on the source** ([layer 4](04-remotes.md#drafts-on-a-remote)):
`view_new` reads the group's current view through `view_show` and a `view_files` read; `validate`
and `save` pack the draft's YAML, files and block drafts into one bundle and call the API-only
`view_check` or `view_put` there, which unpack it as drafts in a folder of their own and run the same
static validation and `write_version`. Rendering stays local: the renderer's own ephemeral `serve`
answers `view` and `code` for the draft itself, and calls the API-only `view_compile` on the source to
get the compiled tree (so pins and library blocks resolve there), while every other query routes to
the source as usual. Block drafts work the same way: `block_promote` and `block_fork` fetch the code,
and `block_validate`/`block_save` send the draft to the API-only `block_check`/`block_put`, so a
library block is checked and saved on the source whose group it is checked against.

### Validation

1. **Static, always.** The view schema; every query parses, its fields exist and placeholder types are
   sound; custom code parses, exports `render`, imports nothing outside `bt`, uses no network APIs,
   stays below a size limit, contains no inline numeric data beyond a small limit, and uses no color
   literals outside `bt.theme`. These checks are lexical (no JavaScript parser in Python): an
   exported `render`, no `import`, no `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`,
   `sendBeacon`, `importScripts` or `Worker`, at most 64 KB, at most 200 numeric literals in a row,
   no `#hex`, `rgb(` or `hsl(` colors. Syntax errors surface in the render and, for readers, as the
   block's error panel.
2. **One render, when a browser is available.** The draft is rendered headless once, in the group it
   is saved for: no exceptions, no console errors, rendering within a time limit, no blank blocks,
   placeholder queries exercised once with example values. In the same render, layout is measured
   without a model: content overflowing its block, clipped text, overlapping elements, charts with
   more than about eight curves.

The renderer uses a browser that is already installed: Playwright's Chromium, else Chrome, else
Edge. Beamtime never downloads one. Without a browser (e.g. on a login node with mode 2), validation
runs the static stage, says that the render was skipped and which command installs a browser
(`uv run playwright install chromium`, a user command), and `view_save` still works.

### At display time

If a custom block throws in a reader's browser, only that block is replaced by an error panel naming
it, with a link to its code and the error; the frame and every other block stay intact.

## The agent guide

`beamtime guide` and the `guide` tool give agents everything they need to build views: short design
guidance, a few complete examples, deterministic checks and a fixed screenshot checklist, which the
research shows work better than long rule lists.

### Progressive disclosure

| Call | Returns | Size |
|---|---|---|
| `guide` | workflow, design principles, defaults, and an index of the other parts | ~1.5k tokens |
| `guide examples [name]` | the example views, or one with commentary | ~1k each |
| `guide blocks [name]` | the catalog, or one block's schema and description | ~1.5k / ~300 |
| `guide kit` | the `bt` kit API | ~2k |
| `guide queries` | the query language | ~1.5k |
| `guide checklist` | the screenshot checklist | ~300 |
| `guide anti-patterns` | common mistakes with fixes | ~800 |
| `guide <group>` | additionally: the group's metrics and varying config, its current view; from M7 library blocks and outdated pins | – |

### Workflow

1. Look at the group: `memory_show`, `keys`, its proposal and notes, its current view.
2. Check the library for blocks that fit (default: reuse first).
3. Write a draft: the question the view answers decides the blocks.
4. `view_validate` until it passes; `view_render` and the checklist, at most two rounds.
5. `view_save`; save generalized versions of new reusable blocks to the library.

### Design principles

- **Lead with the finding.** `finding` states the result in one sentence; the first blocks support
  it, details follow.
- **One block, one question.** A chart that answers two questions is two charts.
- **Choose the block by the question**:

  | Question | Block |
  |---|---|
  | How did a run evolve? | `line` over steps |
  | Which setting is best? | `table` sorted by the metric, `stat` for the best |
  | How does a metric depend on one parameter? | `scatter`, with `seeds` and a fit if it helps |
  | How do two parameters interact? | `heatmap` (wave 2), or `scatter` colored by one |
  | Which hyperparameters matter? | `importance`, then `parallel` (wave 2) |
  | Does a change help? | `bar` or `table` grouped by the change; baselines with `match` (wave 2) |
  | What does a run produce? | `images`, `text`, `data_table` |
  | Where does the research stand? | `proposal`, `groups`, `timeline`, `memory` |

- **Tame many runs** with `color`, `by` or `seeds`.
- **State the setup in captions**: what was varied, what was held fixed, how many runs.
- **Units, labels and scales** go into the view's `metrics` once.
- **Don't overclaim.** If the proposal's check is pending, provisional, insufficient or failed, the
  finding says so; verdicts belong in notes.
- **Interactive only when it helps**: detail-on-click for exploration, not decoration.

### Defaults

Marked as defaults that the user's own instructions may override ([Agent instructions](#agent-instructions)):

- Custom blocks may be used without asking.
- Reuse library blocks first; fork the closest one before writing from scratch.
- Save generalized versions of new reusable blocks to the library; keep one-off blocks in their view.
- When editing a view, check `outdated` and offer to upgrade pinned blocks.
- At most two screenshot rounds per draft.
- Ask the user to start `beamtime serve --no-ui` when live data is needed and no daemon runs.
- Never run commands that change the project or the machine; give the user the exact command
  ([layer 8](08-cli-mcp.md#policy)).

### Examples

Five complete example views ship with Beamtime, each with a commentary, and double as templates
(`beamtime view new --from <example>`):

| Example | Shows |
|---|---|
| `sweep` | a learning-rate sweep: finding, best-run stat, curves colored by the swept field, accuracy against learning rate with seeds merged, run table |
| `ablation` | runs grouped by the change, grouped bars with error bars, the proposal with its predictions and checks |
| `run` | a view of one run's page: its metrics, output tail, logged samples |
| `direction` | a research direction: `groups` overview of its sweeps, `timeline` of decisions and verdicts, memory, proposal |
| `custom` | a custom block with click-to-detail, theme colors and graceful degradation |

### Screenshot checklist

Answered yes or no for every block in the screenshots:

1. Is every label, tick and legend entry fully visible?
2. Can the runs or groups in each chart be told apart?
3. Does each title or caption match what the block shows?
4. Is any block empty or showing only a notice where data was expected?
5. Do axes use sensible scales (log for quantities spanning orders of magnitude)?
6. Does the first screen show the finding and the evidence for it?
7. Is anything decorative that carries no information?

### Anti-patterns

`validate` detects those marked ✓:

| Mistake | Fix |
|---|---|
| ✓ more than about eight curves in one chart | `color`, `by`, `seeds` |
| ✓ aggregating runs that differ in more than noise | aggregate by the varying key too |
| ✓ colors, fonts or sizes in custom code | `bt.theme`, `bt.fmt`, CSS variables |
| ✓ numbers written into code | declare a query |
| ✓ a block that breaks without data | handle `status` and empty results |
| ✓ log scale over values that can be zero or negative | a linear scale, or a symlog transform |
| strong smoothing that hides spikes | lower `smooth`, or show raw and smoothed |
| comparing runs of different length without saying so | a `steps` window, or a note in the caption |
| a finding stronger than the check | state what the check says |
| a chart where a table or a single number would do | `table` or `stat` |

## Agent instructions

**Users override defaults where they already keep agent instructions**, not in a Beamtime-specific
file: a repo's `CLAUDE.md` or `AGENTS.md`, a global instruction file, or a nested file in a
subfolder. Agents load these themselves and weigh them above tool output. For that to work, the guide
marks its defaults as defaults and says that the user's own instructions take precedence. A snippet
in Beamtime's documentation shows how:

```markdown
## Beamtime
- Ask me before adding custom blocks to a view.
- In beamtime/scaling/, plot every result against config.n_params on log-log axes.
```

If Beamtime later starts agents itself, those agents won't see the user's files; a setting pointing
to them can solve that then.

## Evaluation harness

A harness measures how well agents build views with the guide, the kit and the tools, and catches
regressions when any of them changes. It lives in `bench/views/` and follows the query-form
experiment and ArtifactsBench (render, screenshot, judge against a per-task checklist).

- **Synthetic log dirs with planted truth.** A generator builds realistic log dirs from a seed:
  sweeps, ablations, scaling series, diverging and killed runs, logged samples, proposals and notes.
  The correct findings are known (warmup helps above a learning rate; one run diverged at step 1200).
  The same generator provides demo data (`beamtime demo`) and test fixtures.
- **40–60 tasks** across categories, each with a log dir, a prompt in a researcher's words, the facts
  the view must get right, and a checklist of 5–10 concrete items.
- **Running**: each task goes to an agent with Beamtime's MCP tools; the harness records tool calls,
  validation and screenshot rounds, tokens and time.

| Score | Measures | How |
|---|---|---|
| Validity | does the saved view validate; how many rounds | deterministic |
| Fidelity | do the queries cover the required runs and metrics; does `finding` state the truth without overclaiming | queries deterministic; a model judge for the finding |
| Checklist | the task's items, yes or no | a vision model on the screenshots, item by item |
| Robustness | does the view render in a single run, a subgroup and without data | deterministic |
| Preference | which of two views a researcher prefers | humans, occasionally, to calibrate the judge |

Item-by-item judging is used because vision models agree with experts on concrete questions but not
on overall aesthetics. The harness answers design questions empirically (do examples help, is a
second screenshot round worth it, how models compare, do custom blocks pay off) and guards releases:
about ten tasks run on every change to the guide, kit or built-in blocks, the full suite before
releases. The generator and task definitions are built early; scoring follows the first renderer.

## Implementation notes

Decided while building custom blocks and the library (milestone M7):

- **The kit is the built-in blocks.** Inside the frame, `bt.ui` and `bt.chart` render the same
  components as the page; `bt.useData(name, values)` returns a result that also carries its call, so
  a component given `data` subscribes to the same answer.
- **Placeholders** are `$name` strings in a declared query; `useData` substitutes the values given
  and refuses a query whose placeholders are unfilled. Library-block params are substituted when the
  view compiles; what remains (such as `$run`) are runtime placeholders.
- **Library blocks in a view** parse without the project: a node whose name is no built-in block
  (lowercase, digits, `-`) is a library use, and the page's library resolves it when the view
  compiles, into a `custom` node with the params filled into the block's queries. Number, string
  and bool params reach the code as `bt.params`. A missing block or unfitting params make the page
  fall back to the default view with the reason, and are errors in `view_validate`.
- **Saving** pins every library block a view uses to its newest version unless the view already
  pins it; drafts keep their view's pins, so editing a view never upgrades it unasked.
  `view_upgrade` re-pins, validates and writes a new version; the page offers the same as a button.
- **Block checks**: the description must say when to use the block and when not; two examples at
  least, each run as a use in a view of the draft's group (and rendered by `block_validate`);
  metric keys and config fields written into the code are errors, fixed ones in the queries
  warnings; a block declaring the same queries as another is pointed out.
- **Chart features in the frame**: kit charts are the built-in blocks, and what the sandbox can't do
  goes through the page over the bridge, so they behave as on the page: tooltips; the hovered run
  shared with the page in both directions; zoom; downloads (the frame renders PNG or CSV, the page
  saves it after checking type, size and name, at most one a second); PDFs (the page draws them
  with its token); Expand (the page's dialog shows the chart, whose calls only read); and chart
  settings, which come from the page's preferences and go back to them, so they persist and are part
  of Save as view. Every custom block has a toolbar from the page: Download saves what it draws (an
  SVG with the theme's colors written in, or its canvas as PNG), Expand opens it in the dialog.
- **Readiness**: the page counts a frame as busy until it reports its first render, an error, or
  15 s; frame errors are logged by the page as `[block <id>] …`, so the renderer reports them, and the
  frame reports blank and overflowing content for the layout checks.

Decided while building views (milestone M6):

- **No inheritance**: a page shows its own newest view, else the built-in default.
- **The model** is a msgspec tagged union on `block` (`beamtime/views/model.py`); YAML nodes are
  normalized to it, and errors name the node path (`body[2].children[0].line.y`).
- **Compiling** turns a view into a block tree (`{block, id, props, data, children}`, with `data`
  naming API calls). The built-in default is itself a view, built from what the page logged and
  compiled the same way, so `view new` writes it out as it shows.
- **Drafts** live in `.beamtime/drafts/<name>/` with a `_draft.json` naming their group; block
  drafts in `.beamtime/drafts/blocks/<name>/`. A block draft's examples render in the view draft
  `block-<name>`, a name users' drafts can't take.
- **`custom`** was accepted by the schema in M6 and runs since M7 (see above).
- **Save as view** in the UI writes the charts with their settings (metrics, x axis, smoothing,
  aggregation, band, scale, outliers), the charts a viewer added, and the title and finding, as a
  new version with the local account as author. Hidden runs stay the viewer's own.
- **History**: the version list, a line diff of two versions' YAML, and both rendered side by side;
  `?v=<version>` shows an older version.
- **The renderer** is a client of `serve`: it serves the project on a free local port with a fresh
  token for the call and opens the draft with `?render=1` (the view without the shell, no live
  updates). It waits until no API call or chart build is pending, then measures the layout in the
  page. Screenshots go to `.beamtime/renders/<draft>/`; over MCP they return as images. They are
  JPEG (quality 75: readable at a fraction of PNG's bytes on a real page); a page shot is clipped
  to at most `SHOT_HEIGHT` (2,520 px) tall, since height is what costs an agent's visual tokens, and
  the answer's `cut` names the blocks that fall below it, so an agent never judges what it never
  saw. A block shot is never cut. `beamtime view render <draft> --block <id>` shows one block that
  was cut off. `render_page` (the view-task harness's judge) stays full height and uncapped.
- **Drawn charts**: `scatter`, `bar` and `histogram` draw their marks on uPlot's axes and grid
  (a draw hook), with the same tooltips, hover highlight and PNG export as `line`.

Decided while building themes (milestone M5):

- **Theme files** are JSON with `colors` only, by the design system's token names; the default pair
  comes from `design/tokens.json`.
- **Pairs by name**: the `theme` setting `lab` selects `lab-light` and `lab-dark`; the name of a single
  file serves both modes. A broken setting (a missing theme, an invalid file)
  falls back to the default pair and shows the problem in the settings page.
- **Resolution** happens in Python: a theme's colors over the tokens of its `type`. The page receives
  both variants and switches between them with the system preference or the viewer's choice (kept in
  the browser).
- **Run colors**: an FNV-1a hash of the run id picks one of the six run slots (a color and a line style); runs are
  placed in id order and move to the next free slot on a collision, over all runs of the viewed
  group, so a run keeps its style across the blocks of a view. Beyond six, slots
  repeat. Group values use the same slots in sorted order, or the `colormap` setting's ramp for more
  numeric values than the palette has colors.

## Later

- **Wave 2** (v1.1): `heatmap`, `parallel`, `compare`, `importance`, `repeat`, `facet`, baselines,
  linked selection.
- **Packages** (v1.1): themes and block libraries shared as packages, installed pi-style:
  `beamtime install git:github.com/lab/beamtime-physics-blocks@v1.2 [-l]`, `npm:` sources, local
  groups; conventional `themes/` and `blocks/` folders with an optional manifest; personal by
  default, per project with `-l` (recorded in the settings with a pin); per-package filters;
  package blocks used with the package name as prefix (`physics-blocks/phase-map`); nothing runs at
  install time; failures degrade to error panels; npm's `beamtime-package` keyword as the gallery
  (`beamtime search`).
- **Theme tooling**: importing VS Code themes (workbench colors to tokens, ANSI colors to the
  categorical palette), `beamtime theme validate` (contrast, color-blindness simulation), a
  high-contrast pair and a print theme.
- **Block param migrations**: declared `rename`/`add` steps applied by `view upgrade`.
- **Params**: typed variables the reader can change for declarative widgets.
- **Free runtime queries** in custom blocks, if placeholders prove too narrow.
- **Community gallery** in the UI (Settings → Appearance / Blocks → browse), backed by a curated
  index repository with automated checks and previews, as Obsidian does.

## Decisions

- Agents build views freely from declarative widgets and custom code blocks; custom blocks need no
  consent by default.
- A page shows its own newest view, else the built-in default; views are not inherited.
- Drafts live in `.beamtime/drafts/`; rendering uses an installed browser and never downloads one.
- All data comes through declared queries, with placeholders for interaction; data files are read
  through the `file` query.
- Built-in blocks exist as YAML widgets and kit components with the same props; wave 1 is v1.
- Custom blocks are ES modules in sandboxed iframes on the `bt` kit (Preact components only), loading
  only the libraries they declare.
- All charts are uPlot; there is no Vega-Lite and no `vega` block. Figures are PNG with CSV data.
- Validation is static always, plus one headless render where a browser is available; screenshots are
  the agent's own check.
- Themes are token files with light and dark pairs and `extends`; the default is a warm, quiet
  notebook look with a serif for reading.
- Run colors are stable by hash with collision resolution within a view.
- Reusable blocks form a library in `blocks/`, used like widgets; views pin block versions and upgrade
  deliberately.
- The guide is disclosed progressively, with five examples, a checklist and anti-patterns; users
  override its defaults in their own instruction files.
- An evaluation harness on synthetic log dirs with planted truth guards view quality.
