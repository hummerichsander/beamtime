# Pages and views

Every group and run has a page. Without anything else, it shows the most important curves, the runs
and the notes. A **view** replaces that with a page made for one question: *which learning rate is
best*, *where did this run go wrong*.

## Ask your agent

*"Build a page for scaling/lr-sweep that shows which learning rate works best."*

The agent writes a draft, checks it, looks at a screenshot of it, and saves it. Every saved view is
a new version; the page's history lists them, and older versions stay viewable.

## Change a page in the browser

- Chart settings (smoothing, log scale, grouping by a config value, the x axis) are in the bar above
  each chart. **Save as view** keeps them for everyone.
- **Add a chart** at the end of the curves picks any logged metric.
- **Add text** puts a written panel at the top; click it to edit.

## Build one yourself

A view is a YAML file of blocks:

```yaml
title: Learning-rate sweep
finding: lr 3e-4 gives the best final val/acc.
body:
  - line: {y: val/acc, by: config.lr, caption: "Mean over seeds per learning rate."}
  - scatter: {x: config.lr, y: metric.val/acc.last, x_scale: log}
  - table: {columns: [run.name, config.lr, metric.val/acc.max], sort: [-metric.val/acc.max]}
```

```sh
beamtime view new scaling/lr-sweep        # a draft in .beamtime/drafts/lr-sweep/view.yaml
beamtime view validate lr-sweep           # checks it, runs its queries
beamtime view render lr-sweep             # a screenshot
beamtime view save lr-sweep               # the page shows it now
```

`beamtime guide blocks` lists every block and its options.

## Custom blocks

When no built-in block fits (a heatmap, a phase diagram), a **custom block** is a small piece of
JavaScript that draws with D3 or Beamtime's chart kit, in a sandbox. Agents write these; `beamtime
guide kit` describes the kit. A custom block worth keeping becomes a **library block** that other
groups can use: `beamtime block promote`, and `block export` / `block import` to share it between
projects.
