# Building a Beamtime view

A view is what a group (or run) page shows: a YAML file of blocks. A page shows its own newest
view, else the built-in default; views are not inherited by subgroups or runs.

## Workflow

Tools are named as over MCP (`view_new`); on the command line the same operation is
`beamtime view new`.

1. Look at the group: `keys`, `memory_show`, `proposal_show`, `notes`, `view_show` for its
   current view, and `block_list` for library blocks made for problems like this one.
2. Decide the one question the view answers; it decides the blocks (table below). **Built-in blocks
   come first:** write a custom block only once you have made sure that no built-in or library block
   can show it, or that it would look visibly worse (`guide kit`).
3. `view_new <group>` starts a draft in `.beamtime/drafts/<name>/view.yaml`: from the page's
   current view, or `--from sweep|ablation|run|direction|custom` (filled with the group's keys).
   Edit the file with your own tools.
4. `view_validate <draft>` until no errors remain. It runs every block's queries, so field and key
   names are checked against the real data, with suggestions; where a browser is installed it
   already renders once and returns the same layout findings as `view_render`, just without an
   image, so checking stays this cheap however many rounds it takes.
5. `view_render <draft>` to look at the page: answer the checklist (`guide checklist`) for every
   block, fix, render again: at most two rounds. A page taller than 2,520 px comes back clipped
   there; `cut` names the blocks below it, and `view_render <draft> --block <id>` shows one of
   them.
6. `view_save <draft> --message "..."`. The page shows it at once; older versions stay.

## Library blocks

Custom blocks that prove useful become library blocks: named, described, with params, used in any
view like a built-in block (`- phase-map: {x: config.lr, y: config.wd, value: metric.val/acc.max}`).

- `block_list <group>` shows what a group can use; `block_show <name>` its params and code.
- `block_promote <group> <block-id> <name>` turns a saved view's custom block into a block draft
  (`.beamtime/drafts/blocks/<name>/`); `block_fork <name> <new-name>` copies a block. Replace fixed
  fields with `$params`, read field names from the query's columns and values from `bt.params`,
  write when to use it and when not, and give at least two examples.
- `block_validate <draft>` checks it (and renders its examples); `block_save <draft>` writes a
  version, at the log dir root unless `group` says otherwise. Saving the same draft again makes a
  newer version.
- Views pin the versions they were saved with. When you edit a view, `view_outdated` names pins
  with newer versions; offer `view_upgrade <group>`.

## Design principles

- **Lead with the finding.** `finding:` states the result in one sentence; the first blocks carry
  the evidence for it, details follow.
- **One block, one question.** A chart that answers two questions is two charts.
- **Choose the block by the question:**

  | Question | Block |
  |---|---|
  | How did a run evolve? | `line` over steps |
  | Which setting is best? | `table` sorted by the metric, `stat` for the best |
  | How does a metric depend on one parameter? | `scatter` with `seeds` and a `fit` if it helps |
  | How do two parameters interact? | `scatter` colored by one |
  | Does a change help? | `bar` grouped by the change, with error bars |
  | What does a run produce? | `images`, `text`, `data_table` |
  | Where does the research stand? | `proposal`, `groups`, `timeline`, `memory` |

- **Tame many runs** (more than about eight curves) with `color: <field>`, `by: [<field>]` or
  `seeds: config.seed`.
- **State the setup in captions**: what was varied, what was held fixed, how many runs. Charts
  need a caption.
- **Units, labels, scales and direction** go into the view's `metrics:` once.
- **Don't overclaim.** If the proposal's check is pending, provisional, insufficient or failed,
  the finding says so; verdicts belong in notes.

## Format in brief

```yaml
schema: 1
title: Learning-rate sweep
finding: val/acc peaks at lr 3e-4 (0.93) and drops on both sides.
filters: {run.status: {ne: failed}}          # narrows every block
metrics:
  val/acc: {label: Validation accuracy, higher_is_better: true}
body:
  - row:                                      # layouts: section, row, grid, tabs
      - stat: {field: metric.val/acc.max, aggregate: best, title: Best accuracy}
  - grid:
      columns: 2
      children:
        - line: {y: val/acc, color: config.lr, caption: ...}
```

Every node is `- <block>: {props}`; layouts take a list of children, or `children:` next to their
props. Ids are optional (made from the block and its main prop) and name blocks in findings and
renders. Common props: `id`, `title`, `caption`, `span` (1, 2, full), `from` (a group relative to
the page, or a run id), `where`, `depth: 1` (only the group's own runs).

## Defaults

These are defaults; the user's own instructions (CLAUDE.md, AGENTS.md) take precedence.

- At most two render rounds per draft.
- Data the queries can't express goes into a data file in the draft's `data/`, shown with
  `data_table: {file: data/<name>.csv}`; record the script that made it in a note.
- Never run user commands (serve, install, settings); hand the user the exact command.

## More

`guide examples [name]` (sweep, ablation, run, direction, custom) · `guide blocks [name]` ·
`guide queries` · `guide checklist` · `guide anti-patterns` · `guide kit` (custom blocks: code for what
no built-in block shows).
With a group (`guide examples sweep --group <group>`), examples use its metrics and config.
