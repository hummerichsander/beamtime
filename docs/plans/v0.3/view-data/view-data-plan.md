# External data in views

Base commit `fb352bd`, branch `setup`. Proposed 2026-11-15, based on the user's request ("In case a UI should render
external data, e.g., from a csv file etc., there should be very clear instructions how this can be done
reliably"), the settled scope from the coordinator (snapshot only, `file` query, guide topic, example, validator
errors, a bench check), the code and a reproduction (`notes.md` next to this plan). No breaking changes; one addition
to the `file` query and one new operation, listed in [Breaking changes](#breaking-changes).

Run a ticket with `/run-ticket docs/plans/v0.3/view-data/view-data-plan.md <ID>` in a fresh session; review tickets
marked `+ review` with `/review-ticket docs/plans/v0.3/view-data/view-data-plan.md <ID>` on a stronger model.
`ticket.py status <this file>` shows what's done and what's next.

## Goal

- **Done means:** an agent asked to show a table it has (CSV, JSON or Parquet, made by its own script or handed
  over by the user) on a group's page follows one guide topic (`beamtime guide data-files`) and gets it right the
  first time: one call copies the file into the draft, `data_table`, a `bt.chart.Scatter`/`Bar` and a custom block
  read it through the `file` query, and the saved page shows the same table as the draft. Every usual mistake
  (a file outside the draft, an unknown format, a missing file, a wrong column, a too large file, a
  semicolon CSV) is a validator finding whose `fix` says exactly what to do.
- **Confirmed by:** `uv run pytest -q` (new tests named per ticket); `beamtime view new <group> --from data`
  validates, renders and saves clean; the bench task `view-external-csv` passes on Sonnet and Haiku (3 reps each),
  compared against a baseline run on the code before this plan (`report.py --base --new`), and the held-out
  `view-external-chart` is run once at the end.
- **Out of scope:** live references to files outside the view (datasets, designed in another session); data files
  in library blocks; YAML charts (`scatter`, `bar`, `line`) taking `file:` directly (question 1); any change in
  `web/`.

## Findings

Evidence: **reproduced** (run), **code** (read, not run; the ticket starts with a failing test). Details in
`docs/plans/v0.3/view-data/notes.md`.

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | A custom block reading a data file validates and saves, then the saved page fails: `no file 'data/fit.csv' in scaling/lr-sweep/view` | `write_version` copies only `data_table.file` and `custom.code`; `data_refs` lists only those two, so `view new` and remote bundles miss the file too | reproduced | J61 |
| 2 | A semicolon CSV validates as one column `lr;acc`; an empty cell is the string `""` | `read_table` uses `csv.reader` defaults; `number_or_text("")` returns `""` | reproduced | J62 |
| 3 | No way to check a column name: a custom query's extra keys are dropped silently, `data_table` shows whatever comes | `File` has `path` only; `compile.declared` keeps `path` only | reproduced | J62 |
| 4 | Agents without a shell must retype an external CSV with Write to get it into a draft | no operation copies a file into a draft | code (`bench/agents/run.py` 27) | L61 |
| 5 | 5 of 8 data-file mistakes give no fix or a vague one (`put it in <folder>`); a 200k-row file passes; no size limit | `validate.structure` 139–151 has two checks; custom `file` queries are checked only by running them | reproduced | L62 |
| 6 | The guide covers data files in two lines; nothing on the `file` result, charts from it, or provenance | no topic | code | N62 |
| 7 | No bench task uses a data file, so nothing measures the guide on it | – | code (grep over all transcripts) | U61, U62, U63 |

## Brief

- **The file query** (J62): `{file: {path, columns?}}`; `columns` narrows and orders the answer and names the closest
  existing column when one is wrong. `data_table` gets the same `columns` prop. The limits and formats live in
  `src/beamtime/query/files.py`: `FORMATS = (".csv", ".json", ".parquet")`, `WARN_BYTES = 2 << 20`,
  `MAX_BYTES = 16 << 20` (the remote bundle limit, so every saved view can also be saved on a remote).
- **Data refs** (J61): one function, `views.model.file_refs(body) -> list[str]` over YAML form, lists every
  `data_table.file`, every custom query's `file.path` and every `custom.code`; `data_refs`, `write_version`, the
  bundle and `view new` all use it, so a file referenced anywhere is copied everywhere.
- **`view data`** (L61): `beamtime view data <draft> <file> [--name]`, MCP `view_data`: copies a file from inside the
  project into `<draft>/data/<name>`, checks format and size, reads it, and answers the ref, columns, row count,
  the first rows and the two YAML snippets to paste. It is an agent write (drafts only, never the log dir).
- **Findings** (L62): `validate.data_file_checks(ref, at, data_dir)` is the one check for a data reference, called for
  `data_table.file` and each custom `file` query; every finding has a `fix`.
- **Example and guide** (N61, N62): example `data` (`view new --from data`), with `src/beamtime/guide/examples/data/reference.csv` and
  `src/beamtime/guide/examples/code/reference-chart.js`; topic `data-files` (`src/beamtime/guide/parts/data-files.md`, under 100 lines) with one recipe
  end to end; the `beamtime-views` skill names it.
- **Bench** (U61–U63): tasks may bring `files:` into the project; `facts.file` scores that the saved view answers a
  `file` query with the fixture's columns and rows.
- Invariant: a data file is a snapshot stored with the view as `view/data/<sha8>-<name>`; it belongs to the page that
  saves it, and its provenance is a note.

Done, for every ticket: its Done line holds; its Check passes; the spec documents say what the code does; its heading
is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check .`; the tests each ticket names while working; the full
   `uv run pytest -q` (4 xdist workers) before the commit. Browser tests (`tests/serve/test_render.py`) run here
   (Playwright Chromium is installed).
2. Generated files: `docs/reference/cli.md` from `uv run python docs/site/reference.py` after any registry change
   (`tests/test_docs.py`); skills are generated by `scripts/build-plugin` into `build/` and not committed. No ticket
   touches `web/`, so no bundle rebuild.
3. Shared files serialize: `src/beamtime/ops/registry.py` (J62, L61, N61, N62) and `src/beamtime/views/validate.py`
   (L62, N61); run the tickets in the Order below, one at a time.
4. Rules: CLAUDE.md's Python style; no module-level PyYAML/NumPy imports on the CLI path (`tests/test_budgets.py`);
   `src/beamtime/query/files.py` stays standard library (PyArrow imported lazily).
5. Never touch: `docs/plans/setup/`, `docs/design/10-setup.md`, and the uncommitted changes of another session in
   `docs/design/00-overview.md`, `01-storage.md`, `04-remotes.md`, `08-cli-mcp.md`, `09-research-record.md`.
   Tickets edit `docs/design/03-index.md` and `05-views.md` only; the `08-cli-mcp.md` row for `view data` waits for
   Z. Commit only your own files (`git add <paths>`, never `git add -A`).
6. Spec: `docs/design/05-views.md` and `03-index.md`; a deviation is written back in the same commit.
7. Ticket budget: 140k tokens per session (assumed default); split a ticket that would exceed it.
8. Bench runs (U62, U63) use the user's Claude subscription: U62 is 6 agent runs, U63 about 12 plus 6 held out, each view
   run with two judge calls. Don't start more than the ticket names.
9. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading.

## Order

```
U61 ─ U62                    harness, then the baseline on today's code
     J61 ─ J62 ─ L61 ─ L62     product: refs, the file query, the tool, the findings (registry, validate.py)
               N61 ─ N62     example, guide topic
                    U63     measure again, refine once, held-out run
                    Z      close
```

What's left runs in this order: U61 U62 J61 J62 L61 L62 N61 N62 U63 Z

## Decisions taken; say if you want otherwise

1. **Snapshot only** (given): files are copied into the view on save; live references are out of scope.
2. **Topic name `data-files`** (assumed): `guide data` would read as the `data` query (logged tables). Rejected:
   `data`, `external-data`.
3. **A `view data` operation** (assumed): copies a file into the draft in one call. Rejected: telling agents to copy
   with their own tools, because agents without a shell retype the file (finding 4) and nothing checks it on the way
   in.
4. **`view data` reads only files inside the project root** (assumed), like every other agent write; a file outside
   gets an error with the user's `cp <file> <root>/` command. Rejected: any readable path, because MCP would then copy
   arbitrary files (`~/.ssh`) into a page that is served (question 2).
5. **Column checks through `columns`** on the `file` query and `data_table` (assumed): declared columns are checked
   when the validator runs the query, with the closest name suggested. Rejected: lexical checks of column strings in
   custom code, which can't tell a column from a caption.
6. **Size limits** (assumed): a warning above 2 MB ("the page loads the whole file"), an error above 16 MB (the remote
   bundle limit). Rejected: a row limit, because column count varies.
7. **CSV dialect** (assumed): comma-separated with a header row; a header without commas but with `;` or a tab is an
   error naming `df.to_csv(path, index=False)`; an empty cell reads as `null`. Rejected: sniffing and accepting any
   delimiter, because a decimal comma (`0,5`) then reads as text without an error.
8. **Charts from a file go through a custom block** with `bt.chart.Scatter` or `Bar` (tier 2) in this plan
   (assumed); `bt.chart.Line` needs curves and is not offered for files. YAML charts with `file:` are question 1.
9. **Recommend CSV** in the guide; JSON (records or `{columns: {...}}`) works; Parquet only where PyArrow is
   installed on the serving machine, which the validator says.
10. **Measure before and after** (assumed): a baseline batch on today's code (U62) before any product or guide change,
    so U63's delta is the plan's effect.

## J. The file query and data refs

### J61. Every data reference is copied: save, view new, bundles (sonnet + review) — reproduced

- **Touches:** `src/beamtime/views/model.py` (new `file_refs`, next to `yaml_walk`), `src/beamtime/ops/views.py`
  (`data_refs` 118–135, `write_version` 548–580, `bundle` 248–259 unchanged but now complete);
  `tests/views/test_custom.py`.
- **Read:** `docs/design/05-views.md` § Data sources (l. 148–152), § Agent loop "Drafts" (l. 633–651);
  `docs/plans/v0.3/view-data/notes.md` § Reproduction item 1.
- **Check:** `uv run pytest -q tests/views/test_custom.py tests/views/test_views.py tests/remote -k "file or data or
  bundle or custom"`, then the full suite.
- **Done:** a draft whose custom block declares `{file: {path: data/fit.csv}}` saves to a view that validates clean
  statically (no `data_dir`) and answers the file through the page; `view new` from that saved view copies the
  file; `bundle(ctx, d)["files"]` contains it.
- **Risks:** the same file referenced by `data_table` and a custom query is stored once and both refs point at it
  (`test_shared_data_file_is_stored_once`); a `$placeholder` as `path` is not a file and is left alone
  (`test_file_placeholder_is_not_copied`); a file under a library block (`Use`) is not touched.
- **Stop if:** `write_version` turns out to be called with views whose custom queries are already hashed from another
  page (then the ref must be copied from that page's `view/`, not the draft).

1. `file_refs(body: list[Any]) -> list[str]` in `src/beamtime/views/model.py`: over YAML form (via `yaml_walk`), returns
   `data_table.file`, `custom.code` and for each `custom.queries.<name>` of the form `{file: {path: str}}` the path,
   skipping strings that start with `$`; in document order, without duplicates.
2. `data_refs(text)` parses the YAML and returns `file_refs(body)`; its error handling stays.
3. `write_version`: for each `m.Custom` with `data_dir`, after `n.code`, rewrite `q["file"]["path"]` of every file
   query through `copy_data(data_dir / path, folder)`; keep a dict `copied: dict[str, str]` so one draft file is
   copied once.
4. Tests: the reproduction from `notes.md` as `test_custom_file_query_survives_save`, plus the two risks.
5. Spec: 05-views.md l. 148: "Data files ... read through the `file` query, by `data_table` (`file`) or a custom
   block's declared query; saving copies each under its content hash."

### J62. The file query reads tables reliably and checks columns (sonnet + review) — reproduced

- **Touches:** `src/beamtime/query/files.py` (`file_kind` 15–36, `read_table` 39–74, `number_or_text` 77–85, new
  `FORMATS`, `WARN_BYTES`, `MAX_BYTES`, `pick_columns`), `src/beamtime/query/models.py` (`File` 164–168),
  `src/beamtime/ops/registry.py` (`FileParams` 91–96), `src/beamtime/ops/reading.py` (`file` 155–175),
  `src/beamtime/views/model.py` (`DataTable` 152–158), `src/beamtime/views/compile.py` (`DataTable` 200–209,
  `declared` 361–363); `tests/query/test_queries.py`, `tests/views/test_views.py`; `docs/reference/cli.md`
  (generated).
- **Read:** `docs/design/03-index.md` § Query kinds, `file` (l. 430–437).
- **Check:** `uv run pytest -q tests/query/test_queries.py tests/views/test_views.py tests/test_docs.py
  tests/ops/test_registry.py`, then the full suite.
- **Done:** `{file: {path, columns: [acc, lr]}}` answers those two columns in that order; `columns: [acc ]` raises
  `QueryError` naming `'acc'` as the closest and listing the file's columns; a `;`-separated CSV raises with the
  `to_csv` fix; an empty cell is `None`; `data_table: {file, columns}` compiles to a call carrying `columns`.
- **Risks:** a quoted header cell containing `;` in a comma CSV is fine (`test_semicolon_inside_quotes`); a ragged
  row raises naming its line number (`test_ragged_csv_row`); JSON records with missing keys still give `None`s
  (existing `test_file`); a BOM at the start of a CSV (Excel) does not end up in the first column name
  (`test_csv_bom`).
- **Stop if:** another reader of `read_table` (grep it) depends on `""` for empty cells.

1. `read_table`: read CSV with `encoding="utf-8-sig"`; if the header row has one cell and it contains `;` or `\t`,
   raise `QueryError(f"{name} looks {sep}-separated; write it comma-separated: df.to_csv(path, index=False)")`;
   a row whose length differs from the header raises `f"{name} line {i}: {n} cells, the header has {k}"`; duplicate
   or empty header names raise (`"an empty column name is usually a pandas index: df.to_csv(path, index=False)"`).
2. `number_or_text("")` returns `None`.
3. `pick_columns(columns, rows, wanted, name) -> tuple[list[str], list[list[Any]]]`: `wanted is None` returns the
   input; an unknown name raises `QueryError(f"no column {w!r} in {name}; its columns: {', '.join(columns)}." +
   closest(w, columns))`.
4. `File.columns: list[str] | None = None`, `FileParams.columns` the same with a description; `file_kind` and the
   draft path in `reading.file` call `pick_columns`.
5. `DataTable.columns: list[str] | None` (description "file only: which columns, in order"); compile passes
   `columns` for `file` tables and keeps `columns` in `declared` for custom `file` queries; any other key of a custom
   `file` query raises `SchemaError(f"{n.id}: a file query takes path and columns")`.
6. `FORMATS`, `WARN_BYTES = 2 << 20`, `MAX_BYTES = 16 << 20` as module constants, used by L62 and L61; the `case other`
   message uses `FORMATS`.
7. Spec: 03-index.md `file` section: `columns`, the CSV dialect (decision 7), empty cells.

## L. Getting a file into a draft, and the findings

### L61. `view data`: copy a file into a draft and describe it (sonnet + review) — code

- **Touches:** `src/beamtime/ops/registry.py` (new `ViewDataParams` after `ViewNewParams` 280–288, new `Op` after
  `view new` 1001–1009), `src/beamtime/ops/views.py` (new `add_data` after `write_draft_files`; the `lines` of
  `write_draft_files` 106–113 name `view data`); `tests/views/test_views.py`, `tests/ops/test_registry.py` if it
  lists tools; `docs/reference/cli.md` (generated); `docs/design/05-views.md` § Agent loop table (l. 618–626).
- **Read:** `docs/design/05-views.md` § Agent loop (l. 614–651); `docs/design/08-cli-mcp.md` rule 6 (l. 22).
- **Check:** `uv run pytest -q tests/views/test_views.py tests/ops tests/mcp tests/test_docs.py`, then the full
  suite.
- **Done:** `call("view data", {"draft": "d", "file": "external/x.csv"})` writes `<draft>/data/x.csv` byte-identical
  and answers `{ref: "data/x.csv", columns, rows: <count>, head: <first 3 rows>, lines}` whose lines carry
  `data_table: {file: data/x.csv}` and the custom query snippet; the MCP server lists `view_data`.
- **Risks:** a file outside the project root (`/etc/hosts`, `../x.csv`) is refused with the user's `cp` command
  (`test_view_data_refuses_outside_files`); the same name with different content is refused naming `--name`, the same
  content is a no-op (`test_view_data_names`); an `.xlsx` or a file over `MAX_BYTES` is refused before copying
  (`test_view_data_checks_format_and_size`); a remote draft (`@box/...` group) works, the copy is local.
- **Stop if:** the registry gives agents no write to drafts without `drafts=True` semantics you can reuse.

1. `ViewDataParams`: `draft: Draft`, `file: str` (description "a CSV, JSON or Parquet file inside the project"),
   `name: str | None` (default: the file's name; must match `^[\w.-]{1,120}$`).
2. `Op(name="view data", kind="view data", drafts=True, params=ViewDataParams, impl=f"{V}:add_data",
   positional=("draft", "file"), summary="Copy a data file into a view draft's data/ and show its columns.")`.
3. `add_data(ctx, p)`: resolve `file` against `ctx.root`; outside the root → `OpError(f"{file} is outside the
   project; ask the user to copy it in: cp {file} {ctx.root}/", code=2)`; suffix not in `FORMATS` → error naming
   them and `df.to_csv(path, index=False)`; size over `MAX_BYTES` → error ("aggregate or downsample to what the view
   shows"); read with `read_table` (a `QueryError` becomes `OpError` code 2, message kept); copy with
   `write_created`; over `WARN_BYTES` add a line.
4. Answer `lines`: `copied <file> to <draft>/data/<name>: <n> rows, columns a, b, c`; `data_table: {file: data/<name>,
   columns: [...]}`; `custom queries: <stem>: {file: {path: data/<name>, columns: [...]}}`; `record where it came
   from in a note (note_add, type observation)`.
5. Spec: the agent-loop table gets the `view_data` row; the `08-cli-mcp.md` row is Z's.

### L62. One check per data reference, with a fix for each mistake (sonnet) — reproduced

- **Touches:** `src/beamtime/views/validate.py` (`structure` 139–151, `custom_checks` 230–296, new
  `data_file_checks`); `tests/views/test_views.py`; `docs/design/05-views.md` § Validation (l. 652–690).
- **Read:** `docs/plans/v0.3/view-data/notes.md` § Reproduction item 2 (the table of today's messages).
- **Check:** `uv run pytest -q tests/views`, then the full suite.
- **Done:** a parametrized `test_data_file_findings` covers each row below with its message and fix, for
  `data_table.file` and a custom `file` query alike.
- **Risks:** a saved view (no `data_dir`) skips the file checks and relies on the query run, as today
  (`test_saved_view_with_missing_file`); a custom `file` query with a `$placeholder` path is an error, not a crash;
  findings are not doubled by the query run (a reference that failed the static check is not run).
- **Stop if:** a check needs the draft's name in the fix and `structure` doesn't have it (pass it in; don't guess).

1. `data_file_checks(ref: str, at: dict[str, Any], data_dir: Path) -> list[Finding]`, errors unless stated:

   | Case | Message | Fix |
   |---|---|---|
   | absolute, or leaves the draft | `{ref!r} is outside the draft; a view reads only files stored with it` | `` `view_data <draft> {ref}` copies it in as data/{basename} `` |
   | `$...` | `a file path can't be a placeholder` | `name the file: data/<name>.csv` |
   | missing, `data/{ref}` exists | `no file {ref!r}` | `write file: data/{ref}` |
   | missing | `no data file {ref!r}` + closest names in `data/` | `` write it to {data_dir}/{ref}, or `view_data <draft> <file>` `` |
   | suffix not in `FORMATS` | `{ref}: Beamtime reads .csv, .json and .parquet` | `save it as CSV: df.to_csv(path, index=False)` |
   | `.parquet`, no PyArrow | warning `{ref}: reading Parquet needs PyArrow where the page is served` | `write CSV instead` |
   | over `MAX_BYTES` / `WARN_BYTES` | error / warning `{ref} is {x:.1f} MB; the page loads the whole file` | `aggregate or downsample to the rows the view shows` |

2. Call it from `structure` for `data_table.file` (replacing 141–151) and from `custom_checks` for every file query.
3. Query-time errors (`read_table`, `pick_columns`) keep coming from `queries`; they carry their fix in the message.
4. Spec: the Validation section lists the data-file checks in one sentence.

## N. Example and guide

### N61. The `data` example: a data file in a table, a chart and a custom block (sonnet) — code

- **Touches:** new `src/beamtime/guide/examples/data.yaml`, new `src/beamtime/guide/examples/data/reference.csv`,
  new `src/beamtime/guide/examples/code/reference-chart.js`, `src/beamtime/guide/__init__.py` (`EXAMPLES` 32),
  `src/beamtime/ops/registry.py` (`ViewNewParams.from_` 284–287), `src/beamtime/views/validate.py` (a warning when a
  data file equals a shipped example file), `src/beamtime/guide/parts/overview.md` (l. 16–18 and the index row
  l. 105); `tests/guide/test_guide.py`, `tests/serve/test_render.py`, `tests/views/test_views.py`;
  `docs/reference/cli.md` (generated).
- **Read:** `src/beamtime/guide/examples/custom.yaml` and `src/beamtime/guide/examples/code/phase-map.js` (the pattern);
  `src/beamtime/guide/parts/kit-api.md`.
- **Check:** `uv run pytest -q tests/guide tests/views tests/serve/test_render.py tests/test_docs.py`, then the full
  suite.
- **Done:** `view new <SWEEP> --from data` validates with no errors and no wording lints
  (`test_examples_validate_and_label_their_sections` covers it once `data` is in `EXAMPLES`), renders without
  blank blocks (`test_data_example_renders`), and saves to a page whose two data references are hashed and answer
  (`test_data_example_saves`); a saved draft whose file is still the example's gets the warning.
- **Risks:** `prune` drops the `data_table` when a placeholder in it comes out empty (keep placeholders out of
  file nodes); the example copies the CSV through `example_file("data/reference.csv")` (it does, via `data_refs`
  after J61); the custom code reads columns from the result, never hard-coded names except through `columns`.
- **Stop if:** the render needs a change in `web/` (out of scope; report it).

1. `reference.csv`: 8 rows, header `x,y,source`, plainly made-up reference values; the example's comment says to
   replace it with the real table (`view_data`).
2. `data.yaml`: a `section` "reference" with `data_table: {id: reference-table, file: data/reference.csv, columns:
   [x, y, source]}` and a `custom` block `reference-chart` (`kit: 2`, queries `ref: {file: {path:
   data/reference.csv, columns: [x, y]}}` and `runs: {runs: {select: [run.id, "{{swept}}", "metric.{{main}}.{{stat}}"]}}`),
   captions saying what is compared.
3. `reference-chart.js` (about 30 lines): two `bt.chart.Scatter`s side by side in a `bt.ui.Row`, the file's and the
   runs', x and y from each result's `columns`; no colours, no inline numbers.
4. `validate`: warning `{ref} is still the example's data` (fix `replace it: view_data <draft> <your file>`) when the
   bytes equal `example_file(ref)`.
5. Overview: `--from sweep|ablation|run|direction|custom|data` and the examples row.

### N62. Guide topic `data-files` with one recipe end to end (sonnet + review) — code

- **Touches:** new `src/beamtime/guide/parts/data-files.md`, `src/beamtime/guide/__init__.py` (`TOPICS` 16–31,
  defaults line 162–163), `src/beamtime/ops/registry.py` (`GuideParams.part` 452–475),
  `src/beamtime/guide/skills.py` (`beamtime-views` topics l. 10), `src/beamtime/guide/parts/overview.md` (index
  l. 101–114), `src/beamtime/guide/parts/analysis.md` (l. 33–34), `src/beamtime/guide/parts/kit-api.md` (result row
  l. 5), `src/beamtime/guide/parts/kit.md` (l. 21); `tests/guide/test_guide.py`; `docs/reference/cli.md`
  (generated); `docs/design/05-views.md` § Progressive disclosure table (l. 694–710).
- **Read:** this plan's Brief; `src/beamtime/guide/parts/kit.md` l. 1–60; the answers of `view data` (L61) and the
  findings table of L62.
- **Check:** `uv run pytest -q tests/guide tests/test_docs.py`, then the full suite.
- **Done:** `beamtime guide data-files` prints the topic (≤ 100 lines); every YAML snippet in it parses
  (`test_yaml_snippets_parse`), every tool it names exists (`test_named_operations_exist`); the overview, the
  analysis part, the defaults line and the `beamtime-views` skill point to it; a test runs the recipe's commands
  in order on the `project` fixture with a CSV written by the test and saves a valid view (`test_data_files_recipe`).
- **Risks:** the recipe drifting from the tool's real answer (the test runs it); the part growing past 100 lines
  (the length test); telling agents to write the CSV by hand from query results, which the `runs ... to: x.csv`
  export does better (say so).
- **Stop if:** the recipe needs a step the tools don't have.

1. Sections: **When** (a table you have that no query gives: your own analysis, a reference, someone's results);
   **Recipe** (1 write the table tidy, one row per observation, header row, units in names, `df.to_csv(path,
   index=False)`, inside the project; 2 `view_new`; 3 `view_data <draft> <file>`; 4 `data_table: {file, columns}`;
   5 a custom block with `queries: {t: {file: {path, columns}}}` and `bt.chart.Scatter data=${t} x=... y=...`;
   6 `view_validate`, `view_render`, `view_save`; 7 `note_add` (observation) naming the file and the script or
   person it came from); **What the block gets** (`columns`, `rows` as objects, no `curves`; `Scatter` and `Bar`
   take it, `Line` doesn't); **Rules** (snapshot: a changed file needs `view_data` again and a new save; file
   paths are fixed, no placeholders; the file belongs to the page that saves it; CSV recommended, limits from
   decision 6); **Errors and fixes** (the L62 table in short).
2. `TOPICS`, `GuideParams`, the overview's index row `data-files`, `skills.py` adds `data-files` to `beamtime-views`.
3. analysis.md 33–34 and the defaults line end with "(`guide data-files`)".

## U. Measuring it

### U61. Bench: tasks bring files, scores check the file query (sonnet) — code

- **Touches:** `bench/agents/run.py` (`Task` 38–57, `project` 106–139), `bench/agents/score.py` (`score_view`
  269–308, new `covered_file`), new `bench/agents/fixtures/jax-sweep.csv`, new
  `bench/agents/tasks/view-external-csv.yaml`, new `bench/agents/tasks/view-external-chart.yaml`,
  `bench/agents/README.md` (task fields, facts table).
- **Read:** `bench/agents/README.md` (whole, 100 lines).
- **Check:** `uv run python bench/agents/run.py --help`; an offline check: build the project of
  `view-external-csv` with `project()`, save a view by hand with the fixture as a data file through `call`, and
  `score_view` gives `file: true` (a short script in the scratchpad; paste its output in the commit message).
- **Done:** `tasks(False, ["view-external-csv"])` loads; the project has `external/jax-sweep.csv`; a hand-saved
  view with the file scores `file: true`, one without scores `file: false` and `correct: false`.
- **Risks:** `robustness` runs the view on other pages, where the file query has no file: set `robust: false` on
  both tasks; a raw-read violation for reading `external/` (it is outside the log dir: check `LOGDIR`).
- **Stop if:** scoring needs the draft (it must score the saved view only).

1. `Task.files: dict[str, str]` (project path → fixture name under `bench/agents/fixtures`); `project()` copies them.
2. `jax-sweep.csv`: 15 rows `lr,seed,val_acc` (lr 1e-4, 3e-4, 1e-3, 3e-3, 1e-2; seeds 0–2), values close to the
   synth sweep's planted effect (best at 3e-4).
3. `facts.file: {columns: [lr, val_acc], rows: 15}`; `covered_file` compiles the saved view (`calls`), runs each
   `file` call and is true when one answer has those columns and that row count; part of `correct`; a reported
   (not scored) `provenance`: a new note in the group names `jax-sweep`.
4. `view-external-csv` (smoke): "My colleague ran the lr sweep in JAX; her results are in external/jax-sweep.csv.
   Put them on the scaling/lr-sweep page as a table next to our runs, and save the page." `view-external-chart`
   (`heldout: true`): the same, asking for a chart of her val_acc over lr against ours. Checklists of 4–5 items each.

### U62. Baseline on today's code (sonnet) — code

- **Touches:** new `docs/plans/v0.3/view-data/results.md`.
- **Read:** `bench/agents/README.md` § Run it, § The loop.
- **Check:** `uv run python bench/agents/run.py --tasks view-external-csv --reps 3` (Sonnet and Haiku, 6 runs).
- **Done:** `results.md` holds the stamp, the per-run table from `RESULTS.md`, and each failure classified
  (product, validator, error message, guide, task) with the transcript line that shows it.
- **Risks:** a judge usage limit leaves runs unscored: rerun `score.py <stamp>` later, never call a run failed for
  it.
- **Stop if:** the batch would start more than 6 agent runs.

Runs before J61, so the delta in U63 is this plan's effect. Don't change the guide or the code here.

### U63. Measure again, refine once, run the held-out task (sonnet + review) — code

- **Touches:** new `docs/plans/v0.3/view-data/results.md` (from U62), `bench/agents/MISTAKES.md`, at most
  `src/beamtime/guide/parts/data-files.md` and the messages of `src/beamtime/views/validate.py`, `src/beamtime/query/files.py` and `add_data`.
- **Read:** `results.md` (U62); `bench/agents/README.md` § The loop.
- **Check:** `uv run python bench/agents/run.py --tasks view-external-csv --reps 3`; then `uv run python
  bench/agents/report.py --base <U62 stamp> --new <stamp>`; after one refinement, the same again; finally `uv run
  python bench/agents/run.py --heldout --tasks view-external-chart --reps 3`; the full test suite.
- **Done:** `results.md` has the before/after table and the held-out result; `MISTAKES.md` has one row per failure
  class seen; `view-external-csv` correct in at least 5 of 6 runs, or the remaining failures are each named with
  the ticket that would fix them.
- **Risks:** fitting the guide to the task (read only `view-external-csv` transcripts while refining, never the
  held-out one); a fix in the guide for what a message should say (README's loop: fix the earliest class).
- **Stop if:** a failure needs a product change bigger than a message; report it instead.

## Z. Close

- **Touches:** `CHANGELOG.md` (0.3.0 section), `docs/design/08-cli-mcp.md` (the `view data` row next to `file`,
  l. 42), `CLAUDE.md` (Layout: `src/beamtime/query/files.py` reads data files with the limits; `guide/` gains the `data`
  example), this plan's Not verified.
- **Check:** `git status docs/design/08-cli-mcp.md` is clean before editing it (else stop and report);
  `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`.
- **Done:** the changelog lists `view data`, the `columns` parameter, the CSV dialect errors, the copied custom
  file queries and the `data-files` topic; the Goal's Confirmed-by checks pass.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| empty CSV cells | the string `""` | `null` | none; blocks already skip non-numbers |
| a custom `file` query with keys other than `path` | dropped silently | a schema error | remove the keys, or use `columns` |
| a `;`- or tab-separated CSV | one column | an error | write it comma-separated |

## Not verified

- That the headless renderer serves a draft's custom `file` query (the compiled call carries `draft`; seen in
  `compile.py` 361–363 and `reading.file`, not rendered). N61's render test checks it.
- That `bt.chart.Scatter` draws a `file` answer whose columns are not fields (`shapes.points` indexes `columns`,
  read, not rendered); its empty message speaks of runs ("Fewer than two runs log ..."), which may confuse. N61.
- That an agent over MCP can write into `.beamtime/drafts/` with its own Write tool in the bench (the existing view
  tasks do this for `view.yaml`). U62.
- How `remote` saves (`view_put`) treat the new custom file refs: covered by `data_refs` through the bundle, not run
  over ssh. J61's bundle test checks the bundle only.
