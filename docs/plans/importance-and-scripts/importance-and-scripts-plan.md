# Importance, scripts and block reuse

Base commit `cf08e67`, branch `main`. Proposed 2026-11-22, based on the agent benchmark in
`bench/agents/compare/` (182 sessions plus four revisions of a script arm) and on the design already written for
`importance` in `docs/design/05-views.md` § `importance` (wave 2) and `docs/design/08-cli-mcp.md` § Reading. No
breaking changes.

Run a ticket with `/run-ticket docs/plans/importance-and-scripts/importance-and-scripts-plan.md <ID>` in a fresh
session; review tickets marked `+ review` with `/review-ticket … <ID>` on a stronger model.
`ticket.py status …` shows what's done and what's next.

## Goal

- **Done means:**
  - `beamtime importance <group> --target <field>` and the `importance` MCP tool answer with one row per config
    field: Spearman rank correlation, η², and the run count the row rests on; below ten runs a notice instead of
    numbers. The `importance` view block shows the same numbers, compiled to the same query.
  - An agent can write Python against `from beamtime import bt` and call any non-user-only operation as a
    function whose answer is a plain dict in a variable.
  - `beamtime block list <group>` shows, besides the library blocks, the custom blocks living in saved views that
    are candidates for promotion, each with its group and the `block promote` command.
  - The agent guide states ops-first: the operations compute the statistics; Python joins, filters and formats
    the answers they return.
  - The benchmark reports, per task, where the script arm beat MCP on the sessions both ran, excluding tasks whose
    prompt restates an operation's own procedure — so the arm keeps working as the instrument that finds missing
    query-language constructs rather than as a competing access path.
- **Confirmed by:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`;
  `cd web && npm ci && npm test && npm run build`; `uv run beamtime importance long/schedules --target config.lr`
  on a synth log dir answers with both measures; the benchmark's script arm imports the shipped shim.
- **Out of scope:** promoted operations of any kind (no `tool` family, no saved op definitions, no Python op
  validator), the needs registry, importing anything from a remote or a git URL, `importance` for non-numeric
  targets, and interactions between config fields (both measures look at one field at a time, as the spec says).
  Also out of scope: acting on any gap the detector finds beyond `importance` — a candidate becomes work only once
  the missing construct can be named, and running the detector batch is a user-run step, not a ticket.

## Findings

Evidence: **reproduced** (run), **real data** (seen in the user's data), **code** (read, not run).

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | "Which setting drives this metric" has no operation; agents roll their own statistics | `importance_kind` raises `QueryError` and `LIVE_KINDS` excludes it | code: `src/beamtime/query/kinds.py` 756, `src/beamtime/query/models.py` 194 | A21 A22 A23 |
| 2 | On `drivers` the script arm beat MCP (0.69× tokens), the only task where a real gap explains it | same as 1 | reproduced: 3 seeds, 4 arm revisions | A22 |
| 3 | 12/42 script sessions computed statistics by hand against MCP's 6/42; on `stale-verdicts` 3/3 against 0/3 | nothing states ops-first where every arm sees it; `rules_block()` has no such line | reproduced | C22 |
| 4 | The `check-all` "win" is a benchmark artifact, not a gap: `beamtime check` already does it | the task prose spells out the whole t-interval procedure because the `files` arm has no `check` | real data: `bench/agents/compare/tasks/check-all.yaml` | E21 |
| 5 | An agent building a page cannot see custom blocks in other groups' views, so it writes a new one | `listing` iterates `Library.names` only; the empty-state line already advertises `block promote` | code: `src/beamtime/ops/blocks.py` 40–66 | D21 |
| 6 | Scripts are not a supported path; the shim exists only as a benchmark prop copied into a session root | never shipped | code: `bench/agents/compare/script/bt.py` | C21 |
| 7 | Task-level differences are unreadable at one rep: `divergence` ran 3/3/2 turns in one script-arm revision and 2/6/12 in the next, on identical data | 3 seeds × 1 rep is too few for per-task inference; `--reps` defaults to 1 | reproduced: two revisions | E22 |

## Brief

- **Importance** (A21–A23, B21–B22): `stats.py` gains `spearman` and `eta_squared` in pure Python beside the
  t-interval primitives; `importance_kind` composes them; one registry `Op` named `importance` with answer kind
  `importance`; the `importance` view node compiles to that query so the UI and MCP share one set of numbers.
  `stats.py` stays the only home of a statistic.
- **The shim** (S21, C21–C22): `src/beamtime/bt.py`, `from beamtime import bt`. Every non-user-only op becomes a
  module attribute via `__getattr__`; `Context.make(caller="view")` so answers arrive whole; reads are cached
  under a new `.beamtime/bt-cache/` folder in the project; writes and `status`/`wait`/`resume`/`logs` are never cached.
- **Block reuse** (S21, D21): `block list` gains a `candidates` section built by scanning saved views the way
  `src/beamtime/ops/views.py:outdated` already does, grouping `m.Custom` nodes by equal declared `queries`.
- **Gap detection** (E21–E22): the script arm stays in the benchmark as the instrument that finds missing
  query-language constructs. `Task.states_procedure` marks a task whose prompt restates an operation's own
  procedure, and `tables.gaps` reports the paired script-against-mcp comparison over the rest, so a win is read as
  a candidate gap only when it cannot be explained by the task's own wording.
- **Spec first** (S21): the shim and the candidate listing are new; they are written into the design before their
  code lands. `importance` is already specified — implement what is written, do not redesign it.

Done, for every ticket: its Done line holds; its Check passes; the spec documents say what the code does; its
heading is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` (4 xdist workers; `-n0`
   serially). Run the named subset while working, the full suite before the commit. Web work also needs
   `cd web && npm ci && npm test && npm run build`.
2. Generated files: any change under `web/` requires the rebuilt `src/beamtime/serve/static/` in the same commit
   (CI fails on a stale bundle; the shell must stay under 120 KB compressed). **B22 is the only ticket that
   rebuilds the bundle**, so nothing else may touch `web/`.
3. Rules: CLAUDE.md's Python style applies (3.10+ unions, lowercase generics, `:param`/`:return:` docstrings,
   comments only for a non-obvious *why*). Keep the CLI path light — no module-level PyYAML, NumPy or
   `importlib.metadata` in anything `beamtime runs` loads (`tests/test_budgets.py`). No NumPy or SciPy anywhere
   in this plan: `stats.py` is pure Python with `math.fsum`.
4. Spec: `docs/design/` is the spec. A deviation is decided and written back in the same commit. Never
   regenerate `tests/golden/schema1/`.
5. Ticket budget: **140k tokens** per ticket session. Split a ticket that would exceed it.
6. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading.

## Order

```
S21 ─┬─ C21 ─ C22 ─ E21 ─ E22   shim, guide, benchmark, then the gap detector
     └─ D21                     block candidates

A21 ─ A22 ─ A23 ─ B21 ─ B22   importance; B22 alone rebuilds the bundle

                        Z21   close, then E23 adds tasks and runs the detector
```

S21 blocks only C and D; the importance chain is already specified and can start at once. What's left runs in this
order: S21 A21 A22 A23 B21 B22 C21 C22 D21 E21 E22 Z21 E23

## Decisions taken; say if you want otherwise

1. **No promoted operations** (your decision): no `tool` family, no saved op definitions, no needs registry.
   Rejected: mirroring the block library at the ops layer, because the evidence collapsed to one real gap
   (finding 1) once `check-all` turned out to be a benchmark artifact (finding 4), and because a 15-line flat
   concatenation of ops is not the same economic object as a 100-line block that must validate and render.
   Shipping the shim is a prerequisite for that family anyway, so this sequences the work rather than forking it.
2. **`importance` is a query kind, not a promoted tool** (your decision): numbers in a shared research record must
   not have local dialects, and a group-up-to-root tool is shadowable by name. Rejected: shipping it as an
   example tool.
3. **The statistic is the one already specified**: Spearman rank correlation for numeric fields, η² on quantile
   bins for the share of variance explained, one field at a time, a notice below ten runs
   (`docs/design/05-views.md` § `importance`). Rejected: choosing a different measure now, because the block and
   the query must agree and the spec already fixed both.
4. **`from beamtime import bt`** (your decision): namespaced and discoverable. Rejected: a top-level `bt` package,
   which would claim a very generic import name.
5. **The shim caches reads under `.beamtime/`** (your decision): every script is a fresh interpreter, so without
   it a second look at the same data costs another call. Rejected: dropping the cache (measured cost in turns) and
   making it opt-in (every agent pays by default).
6. **Candidates extend `block list`** (your decision): the agent already calls that op before building a page, so
   discovery lands at the right moment with no new MCP tool. Rejected: a separate op, which only helps when the
   agent remembers it.
8. **The script arm stays, as a gap detector rather than a competing access path** (your decision): every task
   where code beats MCP is read as a candidate missing construct in the query language, and becomes work only once
   that construct can be named. Rejected: retiring the arm after this plan, because it is the only standing
   instrument that finds these; and treating any win as a gap, because finding 4 shows a task can restate an
   operation's own procedure and look like one.
7. **Views stay out of the SQL index**: the candidate scan walks the tree exactly as `src/beamtime/ops/views.py:outdated`
   already does. Rejected: indexing views, which is a far larger change than this plan's one listing needs.

## S. Spec

### S21. Write the shim and block candidates into the design (sonnet) — code

- **Touches:** `docs/design/08-cli-mcp.md` (§ Reading table ~l. 29, § Views and blocks ~l. 70, § Policy ~l. 267),
  `docs/design/05-views.md` (§ Creating and reusing blocks l. 539–562), `docs/design/01-storage.md` (what
  `.beamtime/` holds).
- **Read:** `docs/design/08-cli-mcp.md` § Operations (l. 24), § Policy (l. 267); `docs/design/05-views.md`
  § Block library (l. 487).
- **Check:** `uv run pytest -q tests/test_docs.py`; `uv run ruff check .`.
- **Done:** the three documents describe `from beamtime import bt`, the new `.beamtime/bt-cache/` location and the
  candidates section of `block list`; `tests/test_docs.py` passes.
- **Risks:** `docs/reference/cli.md` is generated and a test checks it is current → regenerate only if a CLI flag
  changed (it has not, in this ticket); the design tables are read by later tickets → keep the names exactly as
  C21 and D21 will use them.
- **Stop if:** the spec already says something incompatible with decisions 4–7; come back rather than changing the
  decision.

`importance` needs no design work — it is already specified in both documents. Only the shim and the candidate
listing are new.

1. In `08-cli-mcp.md` § Reading, add no row (the shim is not an operation). Add a short subsection after
   § Shared conventions: **Scripts** — agents may write Python against `from beamtime import bt`, which exposes
   every non-user-only operation as a function returning its answer as a dict; the caller is `view`, so answers
   are whole and unpaged; reads are cached in a new `.beamtime/bt-cache/`, writes and `status`, `wait`, `resume`,
   `logs` never are. State the rule it serves: the operations compute the statistics, Python joins, filters and
   formats them.
2. In `08-cli-mcp.md` § Policy, add one bullet: scripts are subject to the same rules as tools — no user-only
   operations, writes stay additive.
3. In `05-views.md` § Creating and reusing blocks, state that `block list` also reports promotion candidates:
   custom blocks in saved views, grouped by equal declared queries, with the group and the `block promote`
   command. Note that a block appearing in two groups is the signal.
4. In `01-storage.md`, add the `bt-cache` folder (new, made at runtime) to what `.beamtime/` holds (local, not committed, safe to delete).

## A. Importance: the query

### A21. Rank correlation and η² in `stats.py` (sonnet + review) — code

- **Touches:** `src/beamtime/record/stats.py` (new `spearman`, `eta_squared`, `rank`; beside `mean` 130,
  `variance` 138), `tests/record/test_stats.py`.
- **Read:** `docs/design/05-views.md` § `importance` (l. 193–200); `docs/design/03-index.md` § the pure-Python
  read path.
- **Check:** `uv run pytest -q tests/record/test_stats.py`; then
  `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`.
- **Done:** `spearman` reproduces hand-computed values on a monotone pair (1.0), an anti-monotone pair (−1.0) and
  a known tied example; `eta_squared` is 0.0 when every bin has the same mean and 1.0 when within-bin variance is
  zero; both return `None` rather than raising on degenerate input.
- **Risks:** ties in the ranks → midranks, `test_spearman_ties`; fewer than three distinct values → `None`,
  `test_spearman_degenerate`; a bin holding one run → it still counts toward the grand mean,
  `test_eta_squared_singleton_bin`; zero total variance → `None`, not a division by zero,
  `test_eta_squared_constant_target`.
- **Stop if:** the spec's wording leaves the binning ambiguous in a way a test cannot pin down.

Pure Python with `math.fsum`, no NumPy and no SciPy — `stats.py` is on the light CLI path and is the one home of a
statistic in Beamtime.

1. `rank(xs: Sequence[float]) -> list[float]`: competition-free midranks, so tied values share their average rank.
2. `spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None`: Pearson correlation of `rank(xs)` and
   `rank(ys)`, computed with `math.fsum`. `None` when either side has fewer than three values, when lengths
   differ, or when either rank vector is constant.
3. `eta_squared(bins: Sequence[Sequence[float]]) -> float | None`: between-group sum of squares over the total
   sum of squares, both with `math.fsum`. `None` when the total is zero or fewer than two bins are non-empty.
4. Tests give each function hand-computed values written out in the test, not regenerated from the code.

### A22. The `importance` query kind (sonnet + review) — code

- **Touches:** `src/beamtime/query/kinds.py` (`importance_kind` 756–762 replaced, `KINDS` 765–774),
  `src/beamtime/query/models.py` (`LIVE_KINDS` 194), `tests/query/test_queries.py`.
- **Read:** `docs/design/05-views.md` § `importance` (l. 193–200); `docs/design/03-index.md` § Query kinds;
  `src/beamtime/query/kinds.py` § `runs_kind` for how a kind selects and reads.
- **Check:** `uv run pytest -q tests/query/test_queries.py tests/record/test_stats.py`; then the full suite.
- **Done:** on a `synth` log dir, an importance query over a group with a swept numeric config key returns one row
  per varying config field with `spearman`, `eta_squared` and `n`; a group with fewer than ten finished runs
  returns `notice` and no rows; `importance` no longer raises and is in `LIVE_KINDS`.
- **Risks:** a non-numeric config field → no `spearman`, η² still computed by grouping on its values,
  `test_importance_categorical`; a field constant across runs → omitted, `test_importance_constant_field`; fewer
  than ten runs → notice, `test_importance_too_few_runs`; a run missing the target metric → excluded from `n`,
  `test_importance_missing_target`.
- **Stop if:** the target field resolves to something other than a single number per run; come back rather than
  inventing an aggregation.

`importance_kind` currently raises `QueryError("importance comes in v1.1; …")`. It composes existing pieces: the
same selection every other kind uses, then A21's two functions.

1. Select runs with the kind's `Selection`, finished and visible only; resolve `q.target` per run to one number
   through the existing field path used by `runs_kind` (a `metric.<key>.<agg>` or `value.<key>` expression).
2. The fields considered are `q.fields` when given, otherwise every `config.*` key that varies across the
   selected runs. Omit a field that is constant.
3. For a numeric field: `spearman(values, targets)`. For every field, numeric or not: `eta_squared` over bins —
   the distinct values for a categorical field, quantile bins for a numeric one (at most four bins, fewer when
   there are ties at the boundaries).
4. Below ten runs return `{"kind": "importance", "rows": [], "notice": "<n> finished runs; importance needs at
   least 10", "meta": …}`. Otherwise rows sorted by `abs(spearman)` then `eta_squared`, descending.
5. Each row carries `n`, the runs it rests on. Remove `importance` from the exclusion that builds `LIVE_KINDS`.

### A23. The `importance` operation (sonnet) — code

- **Touches:** `src/beamtime/ops/registry.py` (new `ImportanceParams` near `CheckParams`; new `Op` beside `check`
  966–974), `src/beamtime/ops/reading.py` (new `importance`), `src/beamtime/ops/answers.py` (an `importance`
  entry), `src/beamtime/cli/format.py` (`render_importance`), `tests/ops/`, `tests/cli/`.
- **Read:** `docs/design/08-cli-mcp.md` § Reading (the `importance` row, l. 29+); `src/beamtime/ops/registry.py`
  § `Op` (l. 747–770).
- **Check:** `uv run pytest -q tests/ops tests/cli tests/mcp`; then the full suite.
- **Done:** `uv run beamtime importance <group> --target <field>` prints a table; the `importance` MCP tool
  appears in `tools()` with a schema; `beamtime query '{"kind": "importance", …}'` gives the same answer.
- **Risks:** the answer must place its group for remotes → the group-answer pattern in `answers.py` (l. 162),
  `test_importance_remote_place`; a group with no runs → the notice, not an error, `test_importance_empty`;
  `--target` missing → an `OpError` naming it, not a traceback, `test_importance_needs_target`.
- **Stop if:** the answer needs a merge rule across sources that the existing `Answer` kinds do not cover.

The CLI row is already promised by the spec; this ticket fulfils it. The op is a thin wrapper, like every other
reading op: parameters subclass the query struct so a field is declared once.

1. `ImportanceParams` subclasses `src/beamtime/query/models.py:Importance` and adds `cursor` and `to`, exactly as the `runs`
   and `series` params do.
2. The `Op`: `name="importance"`, `kind="importance"`, `render=f"{F}:render_importance"`, `positional=("group",)`,
   summary one line naming both measures.
3. `render_importance` prints one row per field: field, spearman (or `—`), η², n; the notice instead of the table
   when there are no rows.

## B. Importance: the view block

### B21. The `importance` view node (sonnet) — code

- **Touches:** `src/beamtime/views/model.py` (new `Importance` node beside `Scorecard` 139),
  `src/beamtime/views/compile.py` (a case beside `m.Scorecard()` 195), `src/beamtime/views/validate.py` (a case
  beside l. 492), `tests/views/test_views.py`.
- **Read:** `docs/design/05-views.md` § `importance` (l. 193–200), § Schema and compilation (l. 221).
- **Check:** `uv run pytest -q tests/views`; then the full suite.
- **Done:** a view with an `importance` block parses, compiles to one declared `importance` query and validates;
  an unknown param is rejected by `forbid_unknown_fields`.
- **Risks:** a block whose target names no metric → validation error naming the target,
  `test_importance_block_bad_target`; a group with too few runs → validation passes and the block carries the
  notice, `test_importance_block_few_runs`.
- **Stop if:** the compiled query shape disagrees with what A22 answers.

No new numbers here: the block compiles to A22's query so the UI and MCP cannot diverge.

1. `class Importance(Node, tag="importance")` with `target: str`, `fields: list[str] | None = None` and the
   common props the other blocks take.
2. `compile.py`: emit one declared query `{"kind": "importance", "from": …, "target": …, "fields": …}`.
3. `validate.py`: when the answer has `rows`, nothing to check; when it has `notice`, that is a valid state, not
   an empty-block error.

### B22. The `importance` block in the frontend (sonnet + review) — code

- **Touches:** new `web/src/blocks/importance.ts`, `web/src/blocks/index.ts` (import l. 17, registration l. 27),
  `web/test/`, and the rebuilt `src/beamtime/serve/static/`.
- **Read:** `docs/design/05-views.md` § `importance` (l. 193–200), § Behavior with one run, many runs and no data
  (l. 211); `design/README.md`; `web/src/blocks/scorecard.ts` as the nearest shape.
- **Check:** `cd web && npm ci && npm test && npm run build`, then from the root
  `uv run pytest -q tests/views tests/serve -m "not browser"` and `uv run pytest -q -m browser tests/serve`
  where Chromium is installed.
- **Done:** the block renders a bar per field with both measures; below ten runs it renders the notice instead of
  bars; it says in the block that the measures look at one field at a time and how many runs they rest on; the
  rebuilt bundle is committed and the shell stays under 120 KB compressed.
- **Risks:** a negative Spearman → the bar reads as magnitude with the sign shown, `importance.test.ts`; one field
  only → no layout collapse; no rows and no notice → the common empty state, not a blank box; raw colors or font
  sizes in the CSS → `scripts/check-design` and `tests/test_design.py` fail.
- **Stop if:** the shell exceeds its compressed budget.

This is the only ticket that touches `web/` and the only one that rebuilds the bundle, so it runs alone.

1. Colors and type come from the design tokens only — no raw values, no per-call overrides.
2. The notice path is the spec's: below about ten runs, a notice instead of bars.
3. State the caveat in the block itself, as the spec requires: one field at a time, interactions not shown, and
   the run count.

## C. The shim

### C21. Ship `from beamtime import bt` (sonnet + review) — code

- **Touches:** new `src/beamtime/bt.py` (from `bench/agents/compare/script/bt.py`), new `tests/test_bt.py`.
- **Read:** `docs/design/08-cli-mcp.md` § Scripts (written by S21); `bench/agents/compare/script/bt.py` as the
  prototype; `src/beamtime/ops/registry.py` § `Op` (l. 747–770).
- **Check:** `uv run pytest -q tests/test_bt.py tests/test_budgets.py tests/test_boundaries.py`; then the full
  suite.
- **Done:** `from beamtime import bt; bt.runs({"from": "."})` answers against a synth log dir;
  `bt.ops()` names every non-user-only operation and no user-only one; a user-only name raises `KeyError`;
  a second identical read is served from the new `.beamtime/bt-cache/` without calling the op; a write is never cached.
- **Risks:** a user-only op reached through `__getattr__` → `AttributeError`, `test_bt_hides_user_only`; `status`
  cached → staleness, `test_bt_never_caches_the_moment`; a non-JSON answer → saving is skipped, not an exception,
  `test_bt_skips_unserializable`; importing `bt` pulling PyYAML or NumPy onto the CLI path →
  `tests/test_budgets.py`.
- **Stop if:** `Context.make(caller="view")` turns out to page or cut an answer after all.

The prototype is proven at 1.06× MCP over 42 benchmark sessions. This ticket graduates it: same behaviour, a real
import path, the cache under `.beamtime/`, and tests it never had.

1. Move the module to `src/beamtime/bt.py`. `ROOT` is no longer the file's parent: resolve the log dir the way
   every op does, through `Context.make(root=...)` with the project root discovered as the CLI discovers it.
2. `CACHE = <root>/.beamtime/bt-cache`. Keep `FRESH = ("status", "wait", "resume", "logs")` and
   `cacheable(op) = not op.writes and op.tool not in FRESH`.
3. Keep `NAME_ERRORS` matching msgspec's exact phrasings only (`"Object contains unknown field"`,
   `"Object missing required field"`); a wider match catches Beamtime's own field errors and makes the message
   wrong — this was measured as a regression.
4. Keep the `author` default for writes, `ops()`, `params(name)` and the trailing-underscore keyword rule
   (`from_` → `from`).
5. Import nothing heavy at module level; `beamtime.mcp.server.schema` stays a lazy import inside `params`.

### C22. Ops-first in the guide and the rules block (sonnet) — code

- **Touches:** `src/beamtime/guide/rules/rules.md`, `src/beamtime/guide/parts/analysis.md`, new
  `src/beamtime/guide/parts/scripts.md`, `src/beamtime/guide/__init__.py` (the parts list, l. 18–31),
  `tests/guide/`.
- **Read:** `docs/design/05-views.md` § The agent guide (l. 653), § Defaults (l. 714);
  `docs/design/08-cli-mcp.md` § Scripts (written by S21).
- **Check:** `uv run pytest -q tests/guide tests/test_docs.py`; then the full suite.
- **Done:** `beamtime guide scripts` prints the new part; the rules block carries the ops-first rule, so every
  arm — MCP, CLI and scripts alike — receives it; `beamtime setup` writes the updated rules.
- **Risks:** the rules block has a release history (`src/beamtime/guide/rules/history/`) and `setup_note` flags an outdated
  one → add the new release file rather than editing a past one, `test_rules_release`; the block is read by the
  benchmark's `rules_block()` → E21 re-measures.
- **Stop if:** the ops-first wording cannot be written without naming a specific task or field.

Finding 3: 12/42 script sessions computed statistics by hand. The rule belongs where every arm sees it, not in a
benchmark-only section.

1. The rule, general and task-free: the operations already compute the statistics, intervals and per-run
   summaries, and every reader of the record shares the numbers they return. Python is for joining, filtering and
   formatting those answers, not for arriving at them: before computing a number yourself, look for the operation
   or field that returns it.
2. `parts/scripts.md`: when to write Python at all (joining several answers, reshaping, formatting), the import
   line, that answers are dicts, that reads are cached, and that `check` is the one path to a verdict.
3. Add `"scripts"` to the parts list in `src/beamtime/guide/__init__.py`.

## D. Block reuse

### D21. Promotion candidates in `block list` (sonnet + review) — code

- **Touches:** `src/beamtime/ops/blocks.py` (`listing` 40–66; new `candidates`), `src/beamtime/views/store.py`
  (a helper beside `saved` 39 if needed), `tests/views/test_library.py`, `tests/ops/`.
- **Read:** `docs/design/05-views.md` § Creating and reusing blocks (l. 539–562, as S21 extends it);
  `src/beamtime/ops/views.py` § `outdated` (l. 844–868) as the scan to copy.
- **Check:** `uv run pytest -q tests/views tests/ops tests/setup/test_scan.py`; then the full suite, and
  `uv run pytest -q -n0 tests/test_budgets.py tests/setup/test_scan.py::test_scan_is_fast_on_a_large_tree` on an
  idle machine.
- **Done:** with the same custom block in two groups' saved views, `block list` reports one candidate naming both
  groups and the `block promote` command; a custom block in one group only is reported as a candidate with a
  count of 1; a block already in the library is not reported; the empty state still reads as it does today.
- **Risks:** a view that does not parse → skipped, not an error, `test_candidates_skip_unparsable_view`; a
  dot-prefixed or underscore-prefixed folder → skipped like `outdated` does, `test_candidates_skip_hidden`; a
  large tree → the scan stays within the existing scan-speed budget, `test_scan_is_fast_on_a_large_tree`; a
  remote group → candidates are local only, `test_candidates_are_local`.
- **Stop if:** the scan cannot stay inside the scan-speed budget; come back before adding an index table
  (decision 7).

Finding 5: the empty-state line already advertises `block promote`, but nothing ever finds a candidate.
`duplicates` (l. 504) already treats equal declared queries as "the same block" — reuse that notion.

1. `candidates(ctx, group) -> list[dict]`: walk saved views with `base.rglob(c.VIEW)` and `store.saved`, exactly
   as `outdated` does; collect `m.Custom` nodes via `m.walk(view.body)`; key them by their declared `queries`.
2. A key already covered by a library block (equal `queries`) is dropped. The rest become candidates with their
   groups, a count, and `beamtime block promote <group> <block-id> <name>` for the first group.
3. `listing` keeps its `rows` for library blocks and gains `candidates` plus candidate `lines`; sort by count
   descending so a block seen in several groups comes first.
4. Keep the existing empty-state line for the library section.

## E. Benchmark

### E21. Point the script arm at the shipped shim and re-measure (sonnet) — code

- **Touches:** `bench/agents/compare/setups.py`, `bench/agents/compare/script/bt.py` (removed),
  `bench/agents/compare/grade.py` (`Task` 44–56), `bench/agents/compare/tasks/check-all.yaml`,
  `tests/bench/test_compare_setups.py`, `tests/bench/test_compare_grade.py`, `bench/agents/README.md`.
- **Read:** `bench/agents/README.md`; finding 4 above.
- **Check:** `uv run pytest -q tests/bench`; then the full suite.
- **Done:** `grade.Task` carries `states_procedure` and `check-all` sets it; the script setup no longer copies a `bt.py` into the session root and the section documents
  `from beamtime import bt`; the ops-first paragraph is gone from the section because C22 put it in the rules
  block every arm receives; `check-all` is marked in the task file as stating its own procedure, so it is not
  read as evidence of an ops gap.
- **Risks:** the section's parity with the MCP instructions → the test that compares them,
  `test_script_section_has_the_shipped_rules`; the shadow `beamtime` stub on PATH is still needed,
  `test_script_has_no_beamtime_command`; the session count changes → `tests/bench/test_compare_sessions.py`.
- **Stop if:** removing the section's ops-first paragraph leaves the script arm without a rule the MCP arm has.

Re-measuring is a separate, user-run step: this ticket only makes the arm runnable against the shipped shim.

1. Delete `bench/agents/compare/script/bt.py` and the `spec.api` copy step; keep the PATH shadow.
2. Rewrite the section's import line to `from beamtime import bt` and drop the ops-first paragraph, which
   `rules_block()` now carries.
3. Add `states_procedure: bool = False` to `grade.Task` and set it true in `check-all.yaml`: the prompt restates
   `check`'s own procedure because the `files` arm has no `check`, so the task is not evidence of an ops gap
   (finding 4). E22 reads this field.

### E22. The script arm as a standing gap detector (sonnet + review) — code

- **Touches:** `bench/agents/compare/tables.py` (new `gaps`, beside `goal` 141–167 and `results` 170),
  `bench/agents/README.md`, `tests/bench/test_compare_report.py`.
- **Read:** `bench/agents/README.md`; findings 2, 4 and 7 above.
- **Check:** `uv run pytest -q tests/bench`; then the full suite.
- **Done:** `results.md` carries a **Gaps** section pairing the script and mcp arms per task over the sessions both
  ran, excluding tasks marked `states_procedure`; with fewer than two reps the section says so instead of inviting
  action; `bench/agents/README.md` documents how to run the detector and how to read it.
- **Risks:** a batch without the script arm → the section is omitted, as `goal` omits itself,
  `test_gaps_without_script`; one rep → inconclusive rather than a candidate list, `test_gaps_needs_reps`; a task
  marked `states_procedure` → excluded even when script wins by a wide margin, `test_gaps_excludes_stated`; a task
  only one arm ran → not paired, `test_gaps_pairs_only`.
- **Stop if:** the batch's keys do not line up well enough to pair per task.

Finding 2 is the only real gap the benchmark found; finding 4 shows how easily a task is mistaken for one. This
ticket makes that distinction mechanical, so the arm keeps earning its cost after this plan.

1. `gaps(batch) -> list[str]`, built like `goal`: pair `script` and `mcp` rows on `(task, seed, rep)`; drop tasks
   whose `Task.states_procedure` is true; return `[]` when either arm is absent from the batch.
2. A task is a candidate when the median script tokens are at most `GAP_RATIO = 0.85` of mcp's over the paired
   sessions **and** its mean score is within 0.02 of mcp's — a cheaper wrong answer is not a gap.
3. When `meta["reps"] < 2`, head the section "inconclusive: one rep per task cannot separate a gap from session
   variance" and still list the rows, so the reader sees the data without being invited to act on it (finding 7).
4. Each candidate row: task, median script and mcp tokens, the ratio, both mean scores, and an empty **missing
   construct** column. The rule the README states: a candidate becomes work only when that column can be filled.
5. README: the detector run is `--setups mcp script --reps 3`; record for each candidate why it was accepted or
   rejected, so the next run starts from the last judgement.

## Z. Close

### Z21. Changelog and generated docs (sonnet) — code

- **Touches:** `CHANGELOG.md`, `docs/reference/cli.md` (generated), `CLAUDE.md` § Project specifics.
- **Check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`;
  `cd web && npm ci && npm test && npm run build`; `uv run python scripts/release.py` as far as it checks the tree.
- **Done:** the changelog lists `beamtime importance`, the `importance` block, `from beamtime import bt` and the
  `block list` candidates; `docs/reference/cli.md` is current (`uv run python docs/site/reference.py`); the Goal's
  "Confirmed by" commands all pass.
- **Risks:** `docs/reference/cli.md` drifts once `importance` has a CLI path → the test that checks it is current;
  a stale `src/beamtime/serve/static/` → CI fails, so confirm B22 committed the rebuild.
- **Stop if:** the Goal's "Confirmed by" commands do not all pass; report which, rather than adjusting the Goal.

1. Add the changelog entries under the unreleased heading, in the order the Goal lists them.
2. Regenerate `docs/reference/cli.md` with `uv run python docs/site/reference.py` and commit it.
3. Update CLAUDE.md § Project specifics to name `importance` as implemented and `beamtime.bt` as the scripting
   entry point.

## E. Benchmark, continued

### E23. More tasks, then the detector run (sonnet) — code

- **Touches:** four new `bench/agents/compare/tasks/*.yaml`, `bench/agents/compare/truth.py` (a truth function per
  new task), `bench/agents/compare/grade.py` (the truth table), `tests/bench/test_compare_truth.py`,
  `tests/bench/test_compare_sessions.py` (the session count), `bench/agents/README.md`.
- **Read:** `bench/agents/compare/tasks/check-all.yaml` as the shape **not** to copy (finding 4);
  `bench/agents/compare/truth.py` (l. 1–30) for how truth stays independent of the operations.
- **Check:** `uv run pytest -q tests/bench`; a dry run of
  `uv run python bench/agents/compare/sessions.py --dry-run --setups mcp script --reps 3`; then the full suite.
- **Done:** four new tasks load, grade against hand-checked truth and appear in a dry run with the right session
  count; none names an operation or restates one's procedure; the detector batch has been run and its `results.md`
  carries a **Gaps** section with three reps.
- **Risks:** truth computed by calling the operation under test → the benchmark would validate nothing, so truth
  reads the run files as `truth.py` already does, `test_truth_reads_files`; a prompt that restates a procedure →
  rewrite it rather than marking it, `test_tasks_state_no_procedure`; a task only some setups can answer → set
  `setups` explicitly; the session count changes → `tests/bench/test_compare_sessions.py`.
- **Stop if:** the batch would cost more than the user has approved — the run is the last step and needs their
  go-ahead, not the ticket's. Measured at the base commit, `--setups mcp script --reps 3` plans **252 sessions**
  over the 14 current tasks; with these four it is **324**, roughly $15 at the $8.71/182-session rate of the
  November batch. Quote the dry run's own count before asking.

The current 14 tasks were written before a code arm existed, so they may be biased toward what the query language
already expresses. These four probe areas none of them reaches, and are written without naming any operation.

1. Four new tasks, one per area the existing set does not cover: **cross-group** (comparing two groups' outcomes),
   **record history** (what changed in a group and when, from notes and the timeline), **logged tables** (an answer
   that lives in a data file rather than in metrics), and **run lifecycle** (hidden, restarted or copied runs).
2. Each prompt states the question a researcher would ask and the answer shape, and nothing about how to get it:
   no operation names, no field expressions, no procedure. All four keep `states_procedure` false.
3. Truth per task in `truth.py`, reading the run files directly. Where a statistic is involved, hand-write the
   expected value in `tests/bench/test_compare_truth.py` rather than only re-using the function the op calls.
4. Last, with the user's go-ahead: run `--setups mcp script --reps 3` over every task, committing nothing from
   `bench/agents/runs/`. Report the **Gaps** candidates and, for each, whether a missing construct can be named —
   that judgement is the detector's output, not the ratio.

## Breaking changes

None. `importance` answered only an error before; `block list` gains a section without changing its existing
`rows`; the shim is new.

## Not verified

- That `Context.make(caller="view")` returns every answer whole for every op the shim exposes — C21 tests it on
  the large-answer ops (`runs`, `series`, `logs`).
- That quantile bins are the right shape for η² on a swept numeric field with few distinct values — A22's
  `test_importance_constant_field` and a tied-boundary case pin the behaviour the spec leaves open.
- That the candidate scan stays within the scan-speed budget on a scale-M log dir — D21 runs that test explicitly.
- That the 12/42 hand-rolled-statistics rate is real rather than caused by `check-all`'s prose — E23's detector
  run is what settles it.
- That `GAP_RATIO = 0.85` separates a real gap from session variance at three reps — E23's run is the first
  calibration, and the README asks for the judgement to be recorded either way.
- That the four new tasks of E23 are free of the bias the existing set may carry; only their results will show
  whether they reach areas the query language does not express.
