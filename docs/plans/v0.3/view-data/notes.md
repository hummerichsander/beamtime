# View data: survey notes

Base commit `fb352bd`. What was run while planning, so tickets start from it.

## Reproduction (2026-11-15)

A throwaway test (removed afterwards) on the `project` fixture, `scaling/lr-sweep`:

1. A custom block with `queries: {t: {file: {path: data/fit.csv}}}`, the CSV in the draft's `data/`:
   `view validate` says ok, `view save` succeeds. The saved YAML still says `path: data/fit.csv`, the view
   folder holds only `code/<sha8>-c.js`, and validating the saved view (or the page) fails with
   `t: no file 'data/fit.csv' in scaling/lr-sweep/view`. Cause: `write_version` (`src/beamtime/ops/views.py`
   548–580) copies `data_table.file` and `custom.code` only; `data_refs` (118–135) lists the same two, so
   `view new` from a saved view and the remote bundle (`bundle`, 248–259) miss these files as well.
2. Validator messages for `data_table: {file: ...}` (`src/beamtime/views/validate.py` 139–151):

   | Reference | Message today | Fix today |
   |---|---|---|
   | `../x.csv`, `/etc/hosts` | `'../x.csv' leaves the draft` | none |
   | `data/none.csv` | `no data file 'data/none.csv'` | `put it in <draft folder>` (not the path to write) |
   | `fit.csv` (file is `data/fit.csv`) | `no data file 'fit.csv'` | `put it in <draft folder>` |
   | `data/fit.xlsx` (exists) | `main: file: unsupported format '.xlsx'; use csv, json or parquet` | none |
   | empty CSV | `main: fit.csv is empty; a CSV starts with a header row` | none |
   | `lr;acc` semicolon CSV | **ok**: one column named `lr;acc` | – |
   | custom query `data/missing.csv` | `t: no file 'data/missing.csv' in draft 'j'` | none |
   | custom query `/abs/missing.csv` | `t: no file '/abs/missing.csv' in draft 'k'` (not "outside") | none |
   | custom query with an extra key `columns` | **ok**, the key is dropped silently (`compile.py` 361–363) | – |
   | `scatter: {file: ...}` | `unknown field 'file'` | `see beamtime guide blocks` |

3. A 200,000-row CSV validates in 0.23 s; no size limit exists for data files. The only limit is the
   16 MB remote bundle (`BUNDLE_LIMIT`, `ops/views.py` 24, `check_size` 293–307).
4. `number_or_text("")` returns `""`, so an empty cell (pandas' NaN) is a string in a numeric column.
   `nan`/`inf` become floats; `serve` encodes them as `null` (msgspec), MCP as `NaN` (`json.dumps`).
5. PyArrow is not a dependency (not in `serve` either); `.parquet` raises `pip install pyarrow` at query time.

## Where agents fail today (code and transcripts)

- The guide mentions data files in two lines only: `analysis.md:33–34` and the fixed defaults line
  (`guide/__init__.py` 162–163): "`data_table: {file: data/<name>.csv}`". Nothing says how a custom block
  declares a `file` query (only `kit.md:21` lists `file` among the kinds), what its result looks like, that
  `bt.chart.Scatter`/`Bar` take it (they index `answer.columns`, `web/src/bt/shapes.ts` 23–36) and `Line`
  does not (it needs `curves`), or that the file belongs to the page that saves it.
- The bench agents have `Read,Write,Edit,Glob,Grep` and no shell (`bench/agents/run.py` 27): an agent can
  put an external CSV into a draft only by reading it and retyping it with Write. No tool copies a file.
- No bench task uses a data file; no transcript in `bench/agents/runs/` writes into a draft's `data/`
  (grep over all `transcript.jsonl`: only the guide's own text mentions `data_table: {file: ...}`).
- Scoring: `score_view` validates the saved view without a `data_dir` (`score.py` 324–335), so a missing
  data file shows up as a query error of the saved view, which the bench would catch (item 1).
