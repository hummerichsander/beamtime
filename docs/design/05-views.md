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
- **`custom`** is a block of agent code (see [Custom blocks](#custom-blocks)).

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

Every custom block gets a global `bt`:

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
   and placeholder queries exercised once with example values from the folder. The most dangerous
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
