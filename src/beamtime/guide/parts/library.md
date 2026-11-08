# Library blocks

Custom blocks that prove useful become library blocks: named, described, with params, used in any
view like a built-in block (`- phase-map: {x: config.lr, y: config.wd, value: metric.val/acc.max}`).
`block_list <group>` shows what a group can use; `block_show <name>` its params and code.

`block_promote <group> <block-id> <name>` and `block_fork <name> <new-name>` write a draft `.beamtime/drafts/blocks/<name>/block.yaml`. Replace fixed fields with `$params`, read
field names from the query's columns and values from `bt.params`, say when to use it and when not,
and give at least two examples:

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

`block_validate <draft>` also checks generality; `block_save <draft>` writes a version at the log dir
root unless `group` says otherwise, and saving the same draft again makes a newer one. Views pin the
versions they were saved with: when you edit a view, `view_outdated` names newer pins and
`view_upgrade <group>` re-pins after validating.
