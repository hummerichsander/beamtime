# Layer 5: Views

Status: **draft, under discussion.** This part collects prior art and derives principles and a
first sketch of the view format. Widget catalog, theme, escape hatches, rendering and agent
instructions follow in later parts.

A view is what a folder shows: a page built mostly by agents from Beamtime's building blocks.
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

1. **The view owns the data context; widgets name fields.** A view's scope is the viewed folder plus
   view-level filters, so most widgets need no `from` or `where`.
2. **Widgets express intent; Beamtime produces the chart.** The agent picks a widget and binds
   fields (`line: {y: val/loss, color: config.lr}`); Beamtime generates the Vega-Lite with correct
   defaults: step on x, consistent run colors, overplotting control, log scales where requested.
3. **A small catalog with descriptions.** About 15 widgets, each a msgspec struct in one
   discriminated union (`type`), no unknown keys, enums for every presentation choice, and a
   "when to use / when not to use" text in the JSON schema.
4. **Beamtime owns the look.** No colors, fonts or pixel sizes in a view. Runs keep their color
   across every widget and page. The same tokens drive widgets, the Vega-Lite `config` and CSS
   variables for HTML widgets.
5. **Few layout primitives, no coordinates.** Section, row, auto-fitting grid, tabs (not nested),
   and repeat. Agents can predict flow layouts without a screenshot; absolute grids cause overlaps
   and noisy diffs.
6. **Freedom needs the user's consent.** Widgets are the default. Before using a Vega-Lite or HTML
   widget, the agent asks the user, saying what it wants to show and why no widget fits. Users can
   change this default in their own agent instructions (see
   [Agent instructions](#agent-instructions)). `validate` lists every escape-hatch widget in its
   summary, so a view's use of them is always visible.
7. **Strict, deterministic validation before any screenshot.** Errors carry the widget id and a
   suggested fix. Screenshot critique is a short, checklist-driven second stage.
8. **Everything addressable.** Every node can carry an `id`, used by validation errors, screenshots
   and targeted edits.
9. **Inherited views must degrade gracefully.** A widget whose data doesn't exist in the viewed
   folder collapses into a one-line notice instead of an empty chart.

## A first sketch

```yaml
version: 1
title: Learning-rate sweep
finding: Warmup removes the loss spike for every learning rate above 1e-4.

filters:
  run.status: {ne: failed}

metrics:
  val/acc: {label: Validation accuracy, unit: "%", higher_is_better: true}
  train/loss: {label: Training loss, scale: log}

baseline:
  where: {config.warmup: 0}
  match: [config.lr, config.seed]

body:
  - row:
      - stat: {id: best-acc, field: metric.val/acc.max, best: true}
      - stat: {id: runs, field: count}
  - section:
      title: Curves
      body:
        - line: {id: loss, y: train/loss, color: config.lr, smooth: 0.6,
                 caption: Training loss per learning rate.}
        - line: {id: by-optimizer, y: val/loss, group: [config.optimizer.name], band: std,
                 caption: Validation loss per optimizer, mean and spread over runs.}
  - repeat:
      over: config.optimizer.name
      body:
        - stat: {field: metric.val/acc.max, best: true, caption: Best run with $value.}
        - line: {y: val/acc, color: config.lr}
  - table:
      id: runs-table
      columns: [run.name, config.lr, config.warmup, metric.val/acc.max]
      sort: [-metric.val/acc.max]
```

- **The view is a nested tree.** Layout nodes contain widgets; any node may carry an `id`, which
  validation errors, screenshots and references use. A flat list of elements plus a separate layout
  (A2UI, Grafana v2) helps streaming generators, but Beamtime's agents write and edit a file with
  ordinary tools, where a nested tree reads better. If deep views turn out hard to edit,
  `beamtime view edit` can gain operations by id without changing the format.
- **`finding`**: the one-sentence key result, shown under the frame.
- **`filters`** and **`metrics`** are inherited together with the view; `metrics` gives labels,
  units, scales and `higher_is_better`, so stat tiles, tables and axes agree.
- **`baseline`** marks reference runs (see [Baselines](#baselines)).
- **`repeat`** repeats a block of widgets once per value of a field, or per subfolder. Each copy's
  scope is narrowed to the runs with that value; the widgets inside don't change, and `$value`
  names the current value in captions. A view written once thereby covers values that appear
  later. For a single chart split by a field, `facet` is better (shared axes).

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

- **Params**: typed variables the reader can change in the UI (a metric picker, a value filter),
  referenced as `$name` in widgets, with unset params dropping their clauses. Deferred until the
  renderer and the screenshot loop are stable, because a screenshot only shows the default value,
  so agents cannot check the other states.

## Agent workflow (outline)

1. `beamtime keys` for what exists in the folder.
2. Write the view, guided by a short design guide (400–800 tokens), 3–5 complete example views, the
   widget JSON schema and a list of anti-patterns.
3. `beamtime view validate`, in order: schema, queries parse and return data, fields exist with
   compatible types, generated Vega-Lite compiles, lint rules (too many series, log scale over
   non-positive values, missing captions or units, empty widgets), HTML widget sandbox and library
   list.
4. `beamtime view render --screenshot`: one image of the page and one per widget, answered against a
   fixed checklist (clipped labels, readable legend, distinguishable runs, title matches content,
   no empty panels). At most two rounds.
5. `beamtime view save` writes the new version.

## Agent instructions

Agents get Beamtime's instructions from `beamtime guide` in the CLI and the `guide` tool in MCP: the
design guide, example views, anti-patterns and default behavior.

**Users override defaults where they already keep agent instructions**, not in a Beamtime-specific
file: a repo's `CLAUDE.md` or `AGENTS.md`, a global instruction file, or a nested file in a
subfolder. Agents load these files themselves and weigh them above tool output, so an override
needs no mechanism in Beamtime. For that to work, the guide:

- **marks its defaults as defaults**, e.g. "default: ask the user before using a Vega-Lite or HTML
  widget", so an agent can tell which statements a user may change;
- **says that the user's own instructions take precedence** over these defaults.

Beamtime's documentation offers a short snippet to paste into an instruction file:

```markdown
## Beamtime
- Vega-Lite widgets are fine without asking; HTML widgets still need my confirmation.
- In beamtime/scaling/, plot every result against config.n_params on log-log axes.
```

These are instructions, not enforcement. Beamtime cannot know whether the user was asked; it makes
the result visible instead (the `validate` summary, and a marker on escape-hatch widgets in the UI).

If Beamtime later starts agents itself, e.g. from a button in the web UI, those agents won't see the
user's instruction files. A setting in `beamtime.yaml` pointing to them can solve that then.

## Evaluation (outline)

A harness like the query-form experiment, with tasks from realistic log dirs. Layers: validation
pass rate and rounds, data fidelity of the queries, a per-task checklist judged on screenshots, and
occasional human pairwise preference to calibrate the judge. It also answers open design questions
empirically, such as examples versus rules, or whether a second screenshot round pays off.

## Decisions

- Escape-hatch widgets (Vega-Lite, HTML) need the user's consent by default; users override the
  default in their own agent instructions.
- `repeat` for blocks and `facet`, `color`, `group`, `seeds` for single charts are in v1; params
  come later.
- Views are nested trees with optional ids.
- Baselines are first-class, with optional matching.
