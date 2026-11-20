# Pages and views

Every group and run has a page: curves in sections by metric prefix (`train/`, also `val.` or
`val_`), the runs and the notes. A **view** replaces it with a page for one question, like *which
learning rate is best*.

## Ask your agent

*"Build a page for scaling/lr-sweep that shows which learning rate works best."*

The agent drafts, checks, screenshots and saves it. Each save is a new version in the page's history.

## Change a page in the browser

- The bar above each chart holds its settings (smoothing, scale, grouping, x axis, color);
  **Save as view** keeps them for everyone.
- **Color by** offers varying config keys and run fields (status, tags, name, folder); a sweep of one
  hyperparameter is colored by it by default.
- **Scale** defaults to log when all values are positive and span more than two decades; pick one to
  fix it, or write `scale:` in a view.
- **Markers**: `auto` (marked while a curve has at most 30 points), `on` or `off`.
- Logged images have a scrubber; click one to zoom, pan and download.
- **×** hides a chart ("n hidden · show" brings it back); **Add a chart** adds any metric without one.
- **Add text** puts an editable written panel at the top.

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
beamtime view validate lr-sweep           # check it and run its queries
beamtime view render lr-sweep             # a screenshot
beamtime view save lr-sweep               # the page shows it now
```

`beamtime guide blocks` lists every block and its options.

## Custom blocks

When no built-in block fits (a heatmap, a phase diagram), an agent writes a **custom block**: a
small piece of sandboxed JavaScript that draws with D3 or Beamtime's chart kit (`beamtime guide
kit`). `beamtime block promote` makes it a **library block** other groups can use; `block export`
and `block import` share it between projects.
