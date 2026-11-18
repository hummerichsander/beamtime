# Data files: a table of your own on a group's page

Use this for a table that no query gives: your own analysis, a reference curve, someone's results. A
file is a snapshot: it is copied into the view and shown from there. Never retype a table by hand into
YAML or custom code. A table of logged runs is no data file: query it, or have a `runs` or `series`
query write the CSV with `to: x.csv` (`guide analysis`) instead of copying numbers from an answer.

{{agent.tools_more}}

## Recipe

1. Write the table tidy: one row per observation, a header row, units in the names (`lr`, `time_s`),
   comma-separated, inside the project: `df.to_csv("results/fit.csv", index=False)`.
2. `view_new <group> --name fit`: a draft of the page's current view, to add to.
3. `view_data fit results/fit.csv` copies it to `fit/data/fit.csv` and answers the columns, the row
   count, the first rows and the two lines to paste. A file outside the project is refused with the
   `cp` command for the user to run.
4. Show it as a table; `columns` narrows and orders it:

```yaml
- data_table:
    id: fit-table
    file: data/fit.csv
    columns: [lr, pred_acc]
    caption: "Predicted accuracy per learning rate, from results/fit.csv."
```

5. Draw it in a custom block: declare a `file` query and give the result to `bt.chart.Scatter` or
   `Bar` (copy the block into `code/fit-chart.js` of the draft):

```yaml
- custom:
    id: fit-chart
    title: Fit
    caption: "Predicted accuracy over the learning rate."
    code: code/fit-chart.js
    kit: 2
    queries:
      t: {file: {path: data/fit.csv, columns: [lr, pred_acc]}}
```

```js
const { html } = bt.preact;

function FitChart() {
  const t = bt.useData("t");
  if (t.status === "error") return html`<p class="notice error">${t.error}</p>`;
  if (t.status !== "ready") return null;
  return html`<${bt.chart.Scatter} id="fit" data=${t} x="lr" y="pred_acc" />`;
}

export default function render(root) {
  bt.preact.render(html`<${FitChart} />`, root);
}
```

6. `view_validate fit`, then `view_render fit` and look; `view_save fit --message "..."`.
7. `note_add` an `observation` naming the file and the script or person it came from; the view holds
   the snapshot, the note holds its provenance.

## What the block gets

`columns` (names, in the order of the query's `columns`) and `rows` as objects keyed by column; an
empty CSV cell is `null`. There are no `curves`: `Scatter` and `Bar` take such a result, `Line` does
not. Read column names from `t.columns` when the block should survive a changed table.

## Rules

- A changed file needs `view_data` again (the same name with other content is refused: use
  `--name`) and a new `view_save`.
- Paths are stored with the view and belong to the page that saves it; `view_save` copies every file
  the view names. A path starting with `$` is filled by the page and not checked.
- CSV is the format to use. JSON (a list of records, or `{column: [values]}`) works. Parquet works
  only where PyArrow is installed on the machine that serves the page.
- Above 2 MB the page loads the whole file (a warning); above 16 MB it is refused. Aggregate or
  downsample to what the view shows.

## Errors and fixes

| Finding | Fix |
|---|---|
| outside the draft | `view_data <draft> <file>` |
| no data file | write it to the path named, or `view_data`; the closest names are listed |
| not .csv, .json or .parquet | `df.to_csv(path, index=False)` |
| semicolon- or tab-separated | write it comma-separated, `index=False` |
| empty column name | a pandas index was written: `index=False` |
| no column `x` in the file | the finding lists the columns and the closest name |
| larger than 16 MB | aggregate or downsample |
