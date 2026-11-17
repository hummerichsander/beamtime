# Agent efficiency: complete answers, fewer turns, a smaller MCP surface

Base commit `f359ffe`, branch `v0.3-benchmark`. Proposed 2026-11-17, based on the transcripts of the wide batches
(`bench/agents/runs/compare-20261117-162537` sonnet, `compare-20261117-171307` haiku; summary in
`docs/plans/v0.3/benchmark-wide/benchmark-wide-plan.md` § Run summary (Y86)) and the interview after it. Breaking
changes are allowed; they are listed in [Breaking changes](#breaking-changes).

Run a ticket with `/run-ticket <this file> <ID>` in a fresh session; review tickets marked `+ review` with
`/review-ticket <this file> <ID>` on a stronger model. `ticket.py status <this file>` shows what's done and what's
next.

## Goal

The outcome this plan commits to, checked against at the end and in every review:

- **Done means:** an agent working through Beamtime gets complete answers on a half-built index, starts on its
  question after one call, answers long-series questions with run-table fields instead of an export and a script,
  and pays for a smaller MCP tool list. In the benchmark, cli and mcp sessions on the six wide tasks cost at most
  1.5x the tokens of plain files, per model, with no loss of score on any task.
- **Confirmed by:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q -n 2`; a rerun of cli and
  mcp on all 14 tasks, sonnet and haiku, seeds 7 8 9 (168 sessions), compared with the wide batches in
  [Findings](#findings) (X91).
- **Out of scope:** results pages, figures and the README (U71, U72 of the benchmark plan); changes to the files and
  TensorBoard setups or to the tasks and grader (their format misses are a separate decision); new MCP tool
  families; the web UI.

## Findings

Evidence: **real data** (the wide transcripts), **code** (read, not run; the ticket starts with a failing test).
Token figures are sonnet means on the six new tasks; a session costs about its API calls times its context.

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | cli 101k, mcp 84k, files 35k, tensorboard 34k tokens per session; 7.9 and 5.1 calls against 3.7 and 3.4 | turns, not answer size: re-read tool results cost at most 4k per session, output about 0.2k | real data | all |
| 2 | `series --points all` exported 4 of 8 runs in `best-checkpoint` (cli and mcp, seed 7); agents re-exported. "N runs not yet indexed" appears in 69 of 72 cli/mcp sessions | `catch_up` stops ingesting streams after 0.2 s; `run_curve` (`src/beamtime/query/kinds.py` 280) returns `None` for a run without columns, as if it had no such metric | real data, code | E91 |
| 3 | Sessions start on a half-built index | `setups.warm` runs `beamtime runs`, which also catches up for only 0.2 s | code | E92 |
| 4 | 1.8–2.2 calls (sonnet), 2.9–3.5 (haiku) before the first question: `memory_show`, `status`, `guide`, `guide analysis`, `guide queries`, `--help` | the rules block says "Start each session with `memory_show`, then `status`… read the [guide topic] you need" (`src/beamtime/guide/rules/rules.md` l. 7) | real data | E93, E94, E95 |
| 5 | Every cli/mcp agent on the long-series tasks exported and then wrote pandas; files agents did it in one script | no field gives "value of A at B's best step" or "first step it blew up" | real data | E97, E98 |
| 6 | mcp agents spent 2–3 calls probing the export's JSON layout; the CSV is long (`run,name,metric,monotone,source,raw,x,y`) | the export answer names only path, format, rows and bytes (`src/beamtime/ops/reading.py` `export` 745) | real data | E96 |
| 7 | mcp's first call has 14.1k context against 8.3k for cli | 20 tool definitions, 12.3k characters; the `where` text repeats in several schemas | real data | E99 |

## Brief

What the tickets build together, so a session doesn't rediscover the design:

- **Complete reads** (E91): `Columns` (`src/beamtime/query/select.py` 55) is the one way a query reads a run's streams. Before it
  opens a run's column files it calls `Index.ensure_streams(run_id)`, which ingests that run's streams when they are
  stale, whatever the catch-up budget. A query never answers from a run whose streams it skipped.
- **Freshness stays honest:** `Freshness.deferred` holds the ids catch-up skipped; `query.run` drops from it the runs
  the query ingested itself, so "N runs not yet indexed" counts only runs the answer didn't read.
- **One start call** (E93, E94): `status` answers the memory's text with its version; the rules block says to start
  with `status` for work sessions and to go straight to the narrowest tool for a question about data. A short table
  "question → tool or field" sits in the rules block; `guide` topics remain for writes and views.
- **Errors teach** (E95): a CLI usage error prints the operation's whole help, so `--help` is never needed upfront.
- **Exports read in one step** (E96): series CSV is wide, one row per run and step; every export answer lists the
  file's columns and its first row.
- **Series fields** (E97, E98): `metric.<key>.nonfinite_step`, `metric.<key>.rise_step:<k>` and the step-reference
  window `metric.<a>[<b>.<step stat>]` are run-table fields like any other, usable in `select`, `where`, `sort` and
  `to`; they are computed from columns (so E91 applies).
- **Small MCP surface** (E99): the rendered tool list stays under 8,000 characters (about 4k tokens at the 2.1
  characters per token measured in the wide batch); shared texts appear once, in the server instructions.

Done, for every ticket: its Done line holds; its Check passes; the spec documents say what the code does; a
`CHANGELOG.md` bullet under 0.3.0 says what changed for users; its heading is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check .`; the ticket's tests with `uv run pytest -q -n 2
   <paths>`; the full suite `uv run pytest -q -n 2` (about 6–7 min) once before the commit. Unset `VIRTUAL_ENV`
   first; uv is `~/.local/bin/uv`. More than 2 workers runs out of memory. `tests/serve/test_browser.py::
   test_main_metrics_are_pinned_in_the_ui` is flaky under load; rerun it alone before calling it a failure.
2. Generated files: `docs/reference/cli.md` is generated by `uv run python docs/site/reference.py` (a test checks it);
   rebuild it after any change to CLI flags or summaries (E95, E97, E98, E99). These tickets therefore run one after
   another. Nothing in `web/` changes.
3. Rules: CLAUDE.md applies. Keep NumPy, PyYAML and `importlib.metadata` off the CLI path (`tests/test_budgets.py`).
   Never touch `tests/golden/`. `src/beamtime/guide/rules/history/` holds released texts; never edit it (the current
   `rules.md` is unreleased).
4. Spec: `docs/design/03-index.md` (§ Freshness l. 163, § Fields l. 211, § Answers l. 446) and
   `docs/design/08-cli-mcp.md` (§ Reading l. 29, § MCP l. 163). A deviation is written back in the same commit.
5. Ticket budget: 140k tokens per session; split a ticket that would exceed it.
6. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading. The hash stays in git (`ticket.py status`).

## Order

```
E91 ─ E92                       complete reads, then the harness
E93 ─ E95 ─ E96 ─ E97 ─ E98 ─ E99   one at a time (cli.md, registry texts)
E94                             the rules block, after everything it names
X91                             rerun and compare
```

The tickets run in this order: E91 E92 E93 E95 E96 E97 E98 E99 E94 X91.

## Decisions taken; say if you want otherwise

1. **Measure on a rerun of all 14 tasks** (your decision): cli and mcp, sonnet and haiku, seeds 7 8 9. Target: mean
   tokens on the six new tasks at most 1.5x the wide batch's files setup of the same model (sonnet 35k → 52k, haiku
   82k → 123k), the mean score per setup not below the wide batch's, and no task's mean score lower by more than
   0.34 (one of three seeds). The interview said 336 sessions; the count is 168 (14 x 2 x 3 x 2). Rejected: the new
   tasks only, which can't show a regression on the old eight.
2. **Queries ingest the runs they read** (your decision). Rejected: naming the missing runs (agents still pay
   turns); a larger budget then naming (two code paths).
3. **The harness indexes fully before a session** (your decision), the state a running daemon keeps. Rejected:
   measuring the cold start only.
4. **Orientation: all four changes** (your decision): `status` includes the memory, the analysis table goes into
   the rules, help comes with the error, and questions about data skip the start ritual.
5. **Wide series CSV and columns in every export answer** (your decision). Breaking for the CSV layout. Rejected:
   a `--wide` flag (agents would have to know it); columns only (agents still reshape).
6. **Trim MCP schemas to under 8,000 characters** (your decision: about 4k tokens). Rejected: fewer core tools
   (write tasks would pay a `tools_more` call).
7. **Series operations as run-table fields** (your decision), not a new query kind: `nonfinite_step`,
   `rise_step:<k>` and step-reference windows.
8. **`rise_step:<k>`**: the first step whose finite value exceeds k times the minimum of the finite values before
   it, or whose value is non-finite; `None` when neither happens. k is a positive number; `rise_step` alone means
   k = 10. Rejected: an absolute threshold (scales differ per metric; `where` already compares values).
9. **A step-reference window** `metric.<a>[<b>.<s>]` with `s` one of `min_step`, `max_step`, `last_step`,
   `nonfinite_step`, `rise_step:<k>` is the value of `a` logged at that step of the same run, or the last value of
   `a` before it when `a` has no point there; `None` when the step is `None` or `a` has no point at or before it.
   Rejected: `@` syntax (only `src/beamtime/format/place.py` parses `@`).
10. **`status` carries the memory's text** as `memory.text`; `memory_show` stays for older versions and the chain.

## E. Efficiency

### E91. Queries ingest the runs they read (sonnet + review) — real data, code — **done**

- **Touches:** `src/beamtime/index/index.py` (`Freshness` 26–70, `catch_up` 214–286, new `ensure_streams`),
  `src/beamtime/query/select.py` (`Columns` 55–80, `Context`), `src/beamtime/query/__init__.py` (`run` 15–60),
  `src/beamtime/ops/reading.py` (`Columns` use l. 877), `docs/design/03-index.md` § Freshness;
  `tests/index/test_index.py`, `tests/query/test_queries.py`.
- **Read:** `docs/design/03-index.md` § Freshness: the daemon (l. 163–200), § Indexing (l. 485–510).
- **Check:** `uv run pytest -q -n 2 tests/index tests/query tests/ops`, then the full suite.
- **Done:** on a log dir indexed with `catch_up(budget_s=0)`, `series` with `points: all` answers a curve for every
  selected run, and a windowed field has a value for every run; `meta.freshness.behind` counts only runs the answer
  did not read; a second query does no ingest.
- **Risks:** a running run whose streams grow between two queries is ingested again, not served stale
  (`test_ensure_running_run`); the daemon holds the index lock → `ensure_streams` waits for it, up to 30 s, then
  raises `QueryError("the index is busy; try again")` (`test_ensure_waits_for_lock`); a damaged `_metrics.jsonl`
  → the run is skipped and named in `freshness.damaged`, not a crash (`test_ensure_damaged_run`).
- **Stop if:** ingest of one 100k-step run takes more than 2 s on this machine (time it on the wide data set); the
  design then needs a decision.

1. Failing test first: `test_series_reads_every_run`, two runs, `catch_up(budget_s=0)`, `series` with
   `points: "all"` → today one curve is missing.
2. `Freshness.deferred: set[str]` (not dumped); `catch_up` adds each run it skips; `behind` becomes
   `len(deferred)`, and `behind_s` the max lag over them (as today).
3. `Index.ensure_streams(run_id: str) -> bool`: under the index lock (timeout 30 s), look up the row, call
   `ingester.stale(rel, run_mtime, row)`; when streams are stale, `ingest_streams(run_dir)`; return whether it
   ingested. Errors as `catch_up` handles them.
4. `Columns.__init__(*, index, run_id, ingested: set[str] | None = None)`: call `index.ensure_streams(run_id)` first;
   add the id to `ingested` when it ingested. `Context` gets `ingested: set[str]` (default empty) and every
   `Columns(...)` in `src/beamtime/query/` passes `ctx.ingested`.
5. `query.run`: before dumping, `freshness.deferred -= ctx.ingested` and recompute `behind`.
6. Spec § Freshness: a query reads every run it selects in full; the budget only bounds catch-up of the rest.

### E92. The harness indexes fully before a session (sonnet) — code — **done**

- **Touches:** `bench/agents/compare/setups.py` (`warm` 232–242), `tests/bench/test_compare_setups.py`,
  `bench/agents/README.md`.
- **Read:** none beyond the Brief.
- **Check:** `uv run pytest -q -n 2 tests/bench`.
- **Done:** after `prepare` of a `cli` or `mcp` session on the `wide` data set, `beamtime status` reports freshness
  without "not yet indexed".
- **Risks:** `reindex` is a user-only operation; the harness plays the user, which the README says
  (`test_warm_indexes_everything`).

1. `warm` runs `beamtime --root <root> reindex` instead of `runs`.
2. `test_warm_indexes_everything`: prepare a cli session on a small synth log dir with a 100k-step run; status has
   `behind == 0`.

### E93. `status` includes the memory (sonnet) — real data — **done**

- **Touches:** `src/beamtime/ops/reading.py` (`status` 1047–1079, `project_memory` 1131–1147),
  `src/beamtime/cli/format.py` (`render_status` 610–640), `docs/design/08-cli-mcp.md` (status row l. 33),
  `tests/ops/test_tools.py`, `tests/cli/test_commands.py`.
- **Read:** `docs/design/09-research-record.md` § Memory (l. 279; the memory is at most 6,000 characters, l. 385).
- **Check:** `uv run pytest -q -n 2 tests/ops tests/cli tests/mcp`.
- **Done:** `status` answers `memory: {version, notes_since, text}`; the CLI prints the memory's text below the
  status table; without memory, nothing is printed and `memory` is `None`.
- **Risks:** a memory file that fails to parse → `text: None` and the version still shown
  (`test_status_memory_unreadable`); an empty log dir (`test_status_without_logdir`).

1. `project_memory` adds `text`: the newest memory's body as `memory_show` gives it (same reader, no front matter).
2. `render_status`: after the existing memory line, a blank line and the text.

### E95. A usage error prints the operation's help (sonnet) — real data — **done**

- **Touches:** `src/beamtime/cli/__init__.py` (parser setup 212–230), `tests/cli/test_commands.py`,
  `docs/design/08-cli-mcp.md` § Errors name the way out.
- **Read:** `docs/design/08-cli-mcp.md` § Errors name the way out.
- **Check:** `uv run pytest -q -n 2 tests/cli tests/test_cli.py tests/test_docs.py`; `uv run pytest -q -n0
  tests/test_budgets.py`.
- **Done:** `beamtime series x --bogus` prints the full `series` help (flags with their one-line meanings) and the
  error line to stderr, exit code 2; `beamtime series --help` is unchanged.
- **Risks:** the top-level parser (`beamtime --bogus`) prints the top-level help, not a crash
  (`test_usage_error_top_level`); a missing required flag (`-y`) also prints the help (`test_usage_error_required`).

1. A small `ArgumentParser` subclass whose `error(message)` prints `self.format_help()` and then
   `f"{self.prog}: error: {message}"` to stderr and exits 2; use it for the top parser and every subparser
   (`parser_class=` on `add_subparsers`).

### E96. Exports read in one step (sonnet + review) — real data — **done**

- **Touches:** `src/beamtime/ops/reading.py` (`export` 745–786, `table_of` 790–836), `src/beamtime/cli/format.py`
  (`render_export` 237–244), `docs/design/08-cli-mcp.md` (file export row l. 244), `src/beamtime/guide/parts/
  analysis.md` (export row), `tests/ops/test_tools.py` (`test_to_writes_curves_one_row_per_point` 316 replaced).
- **Read:** `docs/design/08-cli-mcp.md` § Reading (l. 29–57), the file export row (l. 244).
- **Check:** `uv run pytest -q -n 2 tests/ops tests/cli tests/guide`.
- **Done:** a series CSV export has the header `run, name, step, <y1>, <y2>, …` (plus the `by` labels for grouped
  curves, and `lo`, `hi`, `n` per metric when the curves are not raw, as `<y>.lo`, …), one row per run and step
  where any metric was logged, empty cells where a metric has no point; the export answer has `columns` and
  `first_row`, and the CLI prints them on two lines after the path. JSON exports keep their layout and gain the
  same two fields in the answer (`columns` = the curve's keys for series JSON).
- **Risks:** metrics logged at different steps (val every 500, train every step) → rows at the union of steps with
  empty cells (`test_to_csv_union_of_steps`); a non-`_step` x → the column is named after x and `step` stays
  (`test_to_csv_other_x`); grouped curves → one row per group label and step (`test_to_csv_grouped`).

1. Failing tests first: the three Risks plus the answer fields.
2. `table_of` for series: group curves by (run or group labels); merge their points by step; header as Done.
3. `export` adds `columns` (the header) and `first_row` (the first row as a list, or `None`) for CSV, and for JSON
   the top-level keys of one curve or row.
4. Spec, guide row and CHANGELOG say the layout changed (Breaking changes).

### E97. Fields for the first non-finite step and the first rise (sonnet + review) — real data

- **Touches:** `src/beamtime/query/fields.py` (`STATS` 10–22, `parse_field` 123–190), `src/beamtime/query/read.py`
  (new `nonfinite_step`, `rise_step`), `src/beamtime/query/select.py` (`select_runs` windowed branch 215–240),
  `docs/design/03-index.md` § Fields, `src/beamtime/guide/parts/queries.md`, `tests/query/test_read.py`,
  `tests/query/test_queries.py`.
- **Read:** `docs/design/03-index.md` § Fields (l. 211–314).
- **Check:** `uv run pytest -q -n 2 tests/query tests/ops`; `uv run python docs/site/reference.py` then
  `uv run pytest -q tests/test_docs.py`.
- **Done:** `runs long/stability --select metric.train/loss.nonfinite_step,metric.train/loss.rise_step:10` on the
  wide data set gives each run's planted steps (compare with `bench/agents/compare/wide_truth.py`); the fields
  work in `where` and `sort`; `rise_step:0` and `rise_step:x` are errors that name the form.
- **Risks:** a run whose first value is NaN → `nonfinite_step` is its first step, `rise_step` too
  (`test_rise_first_value_nan`); all values equal → `None` (`test_rise_flat`); a negative running minimum, where
  "k times" turns the bar below the minimum → decision 8 stays literal, document it and test it
  (`test_rise_negative_min`).
- **Stop if:** the parse of `rise_step:<k>` collides with an existing field form.

1. `read.nonfinite_step(steps, values) -> int | None` and `read.rise_step(steps, values, k: float) -> int | None`,
   pure Python, one pass (decision 8).
2. `parse_field`: `nonfinite_step` joins the stats; `rise_step` and `rise_step:<k>` parse to `stat="rise_step"`,
   `arg=k` (new `Field.arg: float | None`); neither has an SQL expression, so they go the columns path like
   windowed fields.
3. `select_runs`: compute these fields from `Columns` (with E91's ingest).
4. Spec, `src/beamtime/guide/parts/queries.md` field table, CHANGELOG.

### E98. Step-reference windows (sonnet + review) — real data

- **Touches:** `src/beamtime/query/fields.py` (`parse_field`, `Field.window`), `src/beamtime/query/read.py`
  (new `value_at`), `src/beamtime/query/select.py` (`select_runs`), `docs/design/03-index.md` § Fields,
  `src/beamtime/guide/parts/queries.md`, `tests/query/test_read.py`, `tests/query/test_queries.py`.
- **Read:** `docs/design/03-index.md` § Fields (l. 211–314).
- **Check:** `uv run pytest -q -n 2 tests/query tests/ops`; `uv run python docs/site/reference.py` then
  `uv run pytest -q tests/test_docs.py`.
- **Done:** `runs long/schedules --select metric.val/loss.min_step,metric.train/loss[val/loss.min_step]` on the wide
  data set gives each run's best step and the train loss there, equal to `wide_truth.py`'s answer; numeric windows
  `[10:20]` behave as before.
- **Risks:** the referenced metric is missing in a run → `None` (`test_ref_missing_metric`); `a` has no point at
  the step → the last value before it (decision 9, `test_ref_between_points`); a reference to a non-step stat
  (`[val/loss.min]`) is an error naming the step stats (`test_ref_needs_a_step_stat`).

1. `parse_field`: a window body that is not `first:last` numbers parses as `<key>.<step stat>`; `Field.window` gets a
   `ref: Field | None`. Windowed stats keep working; a ref window takes no further stat (the value at the step).
2. `read.value_at(steps, values, step) -> float | None` by bisection.
3. `select_runs`: resolve the referenced step per run (from the card for `min_step`, `max_step`, `last_step`, from
   columns for the E97 stats), then `value_at` on `a`'s column.
4. Spec, guide field table, CHANGELOG.

### E99. A smaller MCP tool list (sonnet + review) — real data

- **Touches:** `src/beamtime/mcp/server.py` (`instructions` 34–62, `schema` 64–77, `slim` 98–120, `tools` 140–163),
  `src/beamtime/ops/registry.py` (parameter descriptions), `tests/mcp/test_server.py`
  (`test_tool_definitions_under_3500_tokens` 139).
- **Read:** `docs/design/08-cli-mcp.md` § MCP (l. 163–200).
- **Check:** `uv run pytest -q -n 2 tests/mcp tests/ops tests/cli`; `uv run python docs/site/reference.py` then
  `uv run pytest -q tests/test_docs.py`.
- **Done:** the test, renamed `test_tool_definitions_under_8000_characters`, sums the JSON of the listed tools and
  the instructions and asserts under 8,000 characters (today 12.3k + 1.0k); every tool keeps every parameter.
- **Risks:** a shortened `where` description loses the operator list → the instructions carry it once and each
  schema says "see instructions: where" (`test_instructions_name_the_where_ops`); `decoded` still finds every
  property's type after the schema shrinks (`test_decoded_after_slim`).
- **Stop if:** under 8,000 characters needs dropping parameters or tools; come back with the closest result.

1. Measure per tool (name, description, schema) and list the ten largest in the commit message.
2. The `where` field text, the field examples and the `to` text move to the instructions once; schemas keep a
   short pointer.
3. `slim` also drops `default` values that equal the CLI default the agent never needs (`"."`, `"all"`, `"_step"`)
   only if the operation reads the same default when the key is absent (check in `decoded`'s callers).
4. CLI help texts come from the same registry: check `docs/reference/cli.md` still reads well.

### E94. The rules block points at the shortest path (sonnet + review) — real data

- **Touches:** `src/beamtime/guide/rules/rules.md`, `src/beamtime/guide/parts/analysis.md`,
  `src/beamtime/guide/rules.py` (only if a new placeholder is needed), `tests/guide/test_rules.py`,
  `tests/setup/test_stale.py`, `tests/setup/test_flow.py`, `bench/agents/compare/setups.py` (none expected; the block is rendered from the guide).
- **Read:** `docs/design/08-cli-mcp.md` § MCP (l. 163–200); `src/beamtime/guide/parts/analysis.md` (36 lines).
- **Check:** `uv run pytest -q -n 2 tests/guide tests/setup tests/mcp tests/bench`; print the block with
  `uv run python -c "import sys; sys.path.insert(0, 'bench/agents/compare'); import setups; print(setups.rules_block())"`.
- **Done:** the block says: start a work session with `status` (it includes the memory); for a question about data go
  straight to the narrowest tool; usage errors print the help, so no `--help` first. It holds a table of at most 12
  rows "question → tool or field", including `metric.<key>.min_step`, `rise_step`, `nonfinite_step`, the
  step-reference window and "export once (`to:`) for your own script"; the whole block stays under 3,000
  characters (today 1,420).
- **Risks:** the history matcher must still recognise 0.1.0 and 0.2.0 blocks (`test_release_of_history`); a block
  edited by hand still counts as edited (`test_update_keeps_a_rules_block_edited_by_hand`).
- **Stop if:** the table can't fit in 3,000 characters without dropping writes guidance; come back.

1. Rewrite the start line and the "Ask with the tools" line as Done says; keep the writes, launch and user-only lines.
2. The table: condensed from `src/beamtime/guide/parts/analysis.md` plus the new fields; `analysis.md` keeps the full table.

## X. Close

### X91. Rerun and compare (sonnet) — real data

- **Touches:** `docs/plans/v0.3/agent-efficiency/agent-efficiency-plan.md` (Findings: a "Rerun (X91)" table).
- **Read:** `docs/plans/v0.3/benchmark-wide/benchmark-wide-plan.md` § Run summary (Y86).
- **Check:** `uv run python bench/agents/compare/sessions.py --dry-run --setups cli mcp | tail -1` → 84 sessions;
  `uv run pytest -q -n 2`.
- **Done:** two batch folders (sonnet, haiku) with 84 graded records each, no leaks, `other_model` false; a table per
  model and setup: mean score, tokens, calls and cost on all tasks and on the six new ones, next to the wide
  batch's cli, mcp and files; the Goal's target checked per model (decision 1) and stated as met or not.
- **Risks:** an interrupted batch → rerun only the missing sessions into the same folder; a setup above target →
  report the per-task numbers and the three costliest transcripts' call lists, no fixes.
- **Stop if:** the pilot (seed 7, the six new tasks, cli and mcp, both models) shows a score below 1.0 on sonnet or
  any "not yet indexed" in a transcript; report before the full runs.

1. Pilot as Stop if says; then `sessions.py --setups cli mcp` and `sessions.py --setups cli mcp --model haiku`.
2. Tokens are the records' `tokens.total`; calls are distinct assistant message ids in the transcript.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| Series CSV export | long: `run,name,metric,monotone,source,raw,x,y`, one row per point and metric | wide: `run,name,step,<y>…`, one row per run and step | read with `pd.read_csv`; for the long form, `df.melt(id_vars=["run","name","step"])` |
| `status` answer | `memory: {version, notes_since}` | adds `memory.text` | none; readers ignore unknown keys |
| CLI usage errors | usage line and error | whole help and error | none |
| Rules block | "Start each session with `memory_show`, then `status`" | start with `status`; questions go to the narrowest tool; a tool table | `beamtime setup` updates unedited blocks |

## Not verified

- How long ingesting one 100k-step run takes (E91 times it; its Stop if).
- That characters per token is about 2.1 for tool schemas: from one comparison (mcp 14.1k vs cli 8.3k first-call
  context, 12.3k + 1.0k characters); X91 checks the first-call context again.
- That the orientation changes cut calls: inferred from the transcripts, measured only by X91.
- Whether agents use the new fields unprompted; the rules table (E94) is the only pointer to them.
