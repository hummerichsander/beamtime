# Building a Beamtime view

A view is what a group (or run) page shows: a YAML file of blocks. A page shows its own newest
view, else the built-in default; views are not inherited by subgroups or runs.

## Workflow

Tools are named as over MCP (`view_new`); on the command line the same operation is
`beamtime view new`.

1. Look at the group: `keys`, `memory_show`, `proposal_show`, `notes`, and `view_show` for its
   current view.
2. Decide the one question the view answers; it decides the blocks (table below).
3. `view_new <group>` starts a draft in `.beamtime/drafts/<name>/view.yaml`: from the page's
   current view, or `--from sweep|ablation|run|direction` (filled with the group's keys). Edit the
   file with your own tools.
4. `view_validate <draft>` until no errors remain. It runs every block's queries, so field and key
   names are checked against the real data, with suggestions.
5. `view_render <draft>`, answer the checklist (`guide checklist`) for every block, fix, render
   again: at most two rounds.
6. `view_save <draft> --message "..."`. The page shows it at once; older versions stay.

## Design principles

- **Lead with the finding.** `finding:` states the result in one sentence; the first blocks carry
  the evidence for it, details follow.
- **One block, one question.** A chart that answers two questions is two charts.
- **Choose the block by the question:**

  | Question | Block |
  |---|---|
  | How did training go? | `line` over steps |
  | Which setting is best? | `table` sorted by the metric, `stat` for the best |
  | How does a metric depend on one hyperparameter? | `scatter` with `seeds` and a `fit` if it helps |
  | How do two hyperparameters interact? | `scatter` colored by one |
  | Does a change help? | `bar` grouped by the change, with error bars |
  | What does the model produce? | `images`, `text`, `data_table` |
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
`guide queries` · `guide checklist` · `guide anti-patterns` · `guide kit` (custom blocks, M7).
With a group (`guide examples sweep --group <group>`), examples use its metrics and config.
