# v0.3: hidden runs and sharper detection rules

Base commit `fb352bd`, branch `setup`. Proposed 2026-11-15, based on the user's request for "undercover" runs
(decided upstream: an init-time flag in `_run.json`, promotion by an authored file, agents may promote), items 1, 5,
9 and 10 of `docs/plans/v0.3/auto-detection-audit.md`, and a survey of the code at the base commit. Planned without
an interview (background run); every choice the user did not make is marked **assumed** in the Decisions and the
open ones are collected in [Questions for the user](#questions-for-the-user). The storage format gains one optional
field and one authored folder, read by every reader; no file is rewritten. Behaviour changes are listed in
[Breaking changes](#breaking-changes).

Run a ticket with `/run-ticket docs/plans/v0.3/record/record-plan.md <ID>` in a fresh session; review tickets marked
`+ review` with `/review-ticket docs/plans/v0.3/record/record-plan.md <ID>` on a stronger model.
`ticket.py status docs/plans/v0.3/record/record-plan.md` shows what's done and what's next.

## Goal

- **Done means:** a run started with `beamtime.init(..., hidden=True)` or `BEAMTIME_HIDDEN=1` is recorded as
  usual but left out of `runs`, `keys`, `series`, `groups` counts, `status` counts, the group tools, the web UI's
  tables, charts and tree, and every prediction, check, plan progress and proposal freeze, until someone promotes
  it (`beamtime run promote <run>` / `run_promote`, or the Promote button in the UI), after which it counts like
  any run. `--hidden` (and `hidden: true` in a query) shows hidden runs; a run named by id is always shown. A
  metric's direction comes from whole name tokens; the default view, the viewer's "mean over seeds" and
  validation use the one seed key `is_seed` finds; failure signatures ignore paths and quoted strings and see
  through a bare exception line; a lost run says how long its heartbeat has been silent.
- **Confirmed by:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` and the 3.10 SDK
  command (How to execute 1); `cd web && npm ci && npm test && npm run build` with a clean `git status`; the
  end-to-end test of U43 (`tests/record/test_hidden.py`): a hidden run in a `compare` group leaves the check
  `insufficient` and the proposal unfrozen, and after `run promote` both change; `tests/golden/schema1` unchanged
  (`git diff --stat fb352bd -- tests/golden` empty).
- **Out of scope:** hiding a run after it started (an op that writes `hidden: true`); deleting hidden runs from the
  UI or by agents; a `beamtime rm` over many runs; the audit's chart items 2, 3, 4, 6, 7 and 8 (the UI plan,
  `docs/plans/v0.3/ui/`); `docs/design/10-setup.md` and `docs/plans/setup/` (the setup session).

## Findings

Evidence: **code** (read at `fb352bd`, not run; each ticket starts with a failing test).

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | Test runs pollute tables, counts and checks; deleting is user-only | no notion of a run that doesn't count | code | U40–U46 |
| 2 | Every listing path goes through `scope_condition` (`query/select.py` 98–114) except `groups_kind` (`kinds.py` 666–669), `status` (`ops/reading.py` 1051–1054) and record membership (`record/proposals.py` 332–347) | one SQL filter covers almost everything | code | U42, U43 |
| 3 | A run's display name is already "authored file in the run, newest wins" (`c.NAME`, `ops/record.py` `name` 199–214, `index/ingest.py` `given_name` 296–311) | the pattern promotion copies | code | U41, U44 |
| 4 | `power`, `answer_acc`, `lower_bound`, `tower_*` read as lower-is-better | substring test in `views/defaults.py:309` `lower_is_better`, copied in `web/src/bt/fmt.ts:121` and `web/src/bt/prefs.ts:32` | code | N41 |
| 5 | `trainer.seed` groups as a seed but the default view never merges on it; `random_seed` counts nowhere | `SEEDS_FIELD = "config.seed"` (`views/settings.py:12`, generated into `web/src/bt/chart-defaults.ts:2`) vs `is_seed` (`query/distinguish.py:95`); `aggregate.py:28` also refuses a nested seed field | code | N42, N43 |
| 6 | One failure split by paths in its message; a bare re-raised type merges different failures | `failure_signature` (`query/facts.py:118`) keeps the last line only | code | N44 |
| 7 | "lost" reads as a verdict | the card answer (`ops/reading.py` `card` 851–915) has no heartbeat age | code | N45 |

## Brief

- **Hidden in the files** (U40, U41): `_run.json` gets `"hidden": true` only for a hidden run (absent means
  visible; `schema` stays 1, like `imported_from`). A run's `visibility/<id>.yaml` (`{schema: 1, hidden: false,
  reason?, author, user}`, `c.VISIBILITY`, run-only like `c.NAME`, kind `visibility` in `format/schema.py`
  `SCHEMAS`) overrides it; the newest valid version wins. `format/run.py` `run_hidden(run_dir, info) -> bool` is the
  one reader. The SDK writes the flag, never the folder; ops write the folder, never `_run.json`.
- **Hidden in the index** (U42): `runs.hidden INTEGER NOT NULL DEFAULT 0` (store `SCHEMA_VERSION` 4, the cache
  rebuilds itself), set by `ingest_meta` from `run_hidden`; `authored_mtime` watches `visibility/` too. Field
  `run.hidden` (`RUN_COLUMNS`). `query/models.py` `Selection.hidden: bool = False`; `scope_condition(ctx, depth,
  hidden=False)` adds `runs.hidden = 0` unless `hidden` or one run is named (`ctx.run_id`).
- **Hidden in the record** (U43): `Target.membership` always adds `runs.hidden = 0`, so members, `select`, checks,
  plan progress, `plan missing`, group status and freezing never see a hidden run.
- **Promotion** (U44): op `run promote` (`run_promote`), params `runs: list[RunId]`, `reason`, `author`; writes
  `visibility/<id>.yaml` per hidden run, refuses groups, reports runs that weren't hidden. Card answer gains
  `run.hidden`; `status` counts visible runs and adds `hidden` with the hint (decision 6).
- **Detection** (N41–N45): `lower_is_better` splits the leaf into tokens; `distinguish.seed_key(varying) -> str | None`
  is the one seed rule, exposed as `keys.config.seed`; `failure_signature` normalizes paths and quotes; the card
  carries `heartbeat_age_s` for lost runs.

Done, for every ticket: its Done line holds; its Check passes; the spec documents say what the code does; its heading
is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` (4 xdist workers, the full
   suite; on this machine single files take a minute or more, so run the named tests first). SDK and format on 3.10:
   `UV_PROJECT_ENVIRONMENT=/tmp/bt-venv310 uv run --python 3.10 pytest -q tests/sdk tests/format tests/synth
   tests/test_boundaries.py tests/test_cli.py`. Web: `cd web && npm ci && npm test && npm run build`.
2. Generated files: after a `web/` change commit the rebuilt `src/beamtime/serve/static/` (CI fails on a stale
   bundle; shell under 120 KB compressed), so N41, N43, N45 and U45 run one after another, and also one at a time with
   the UI plan's web tickets. After a change of `views/settings.py` `generated_ts` run `scripts/build-chart-defaults`.
   After a registry change run `uv run python docs/site/reference.py` (tests/test_docs.py checks
   `docs/reference/cli.md`). After a change of `guide/skills.py` run `scripts/build-plugin`.
3. Rules: CLAUDE.md style (docstrings with `:param:`, keyword-only constructors, no section comments). `sdk/`,
   `format/`, `synth/` stay Python 3.10 with stdlib and PyYAML. Never touch `tests/golden/schema1/`,
   `docs/design/10-setup.md`, `docs/plans/setup/`, or `src/beamtime/guide/rules/rules.md` (its history files belong to the setup
   plan's stale checks). Keep PyYAML off the plain `beamtime runs` path (`tests/test_budgets.py`): `run_hidden`
   imports `format.authored` inside the function, as `given_name` does.
4. Spec: `docs/design/` is the spec. U40 writes the hidden-run spec before any code; the A tickets update their own
   sections in the same commit. `docs/design/01-storage.md`, `08-cli-mcp.md` and `09-research-record.md` had
   uncommitted edits from the setup session when this plan was written: commit nothing of theirs, and stop if they
   are still uncommitted.
5. Ticket budget: 140k tokens per session (assumed; decision 12). Split a ticket that would exceed it.
6. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading.

## Order

```
U40 ─ U41 ─ U42 ─ U43 ─ U44 ─┬─ U45 (web, after N45) ─ U46 ─ U47
N44                       │
N42 ─────────────────────┤
N41 ─ N43 ─ N45 ────────────┘   web tickets serialize on the bundle
```

What's left runs in this order: U40 U41 U42 U43 U44 N44 N42 N41 N43 N45 U45 U46 U47

## Decisions taken; say if you want otherwise

1. **The name is `hidden`** (assumed; question 1): `init(hidden=True)`, `BEAMTIME_HIDDEN`, `--hidden`, field
   `run.hidden`, the UI word "Hidden". It says what it does in every listing. Rejected: `undercover` (the user's
   word; playful, and "undercover runs" reads oddly in an error message or a flag), `draft` (taken by view drafts),
   `test` (a run's purpose, not its visibility).
2. **The flag in `_run.json`, promotion in `visibility/`** (decided upstream): every file has one writer; the SDK
   owns `_run.json`. `visibility/<id>.yaml` holds `hidden: false` rather than being a bare "promoted" marker, so
   "newest wins" means something and a later hide op needs no new format (assumed). Rejected: a note type
   `promotion` (notes are the research record, would show in timelines and digests).
3. **`hidden` is written only when true; `schema` stays 1** (assumed): like `imported_from`, an absent field reads
   as visible, so every existing run reads as before and the golden fixtures stay byte-exact. Rejected: schema 2
   (would force a new reader branch for one optional key).
4. **Selection excludes hidden runs by default, one run named by id always shows** (decided upstream for the
   default; the by-id rule assumed): `card`, `output`, `resume`, `from: <run id>` and the run page work for a hidden
   run, so it can be inspected before promoting. Resolution by name or suffix also finds hidden runs. Rejected:
   hiding from `card` (a test run you can't inspect is useless).
5. **Hidden runs never count in the record, including freezing and `ref`** (decided upstream; freezing and `ref`
   assumed): a hidden test run must not freeze a group's proposal, or an agent's smoke test would force a
   `--reason` supersede. A `ref` pointing at a hidden run reads as missing. On promotion the run joins the version
   it recorded; `run promote` warns when that version's file no longer matches the run's recorded hash.
6. **`status` hints at old hidden runs** (assumed; question 2): when hidden runs older than 7 days exist,
   `status` says `hidden    N runs (K older than 7 days: promote with beamtime run promote <id>, or the user deletes
   them with beamtime rm <id>)`, listing up to 5 ids. Agents never run `rm`; the rules already make them hand the
   command over. Rejected: silence (hidden runs pile up unseen), a `gc` rule (deleting stays explicit).
7. **Resume keeps the run's visibility** (assumed): `init(hidden=...)` on a continued run is ignored with a
   `hidden` warning event when it differs. A requeued hidden job stays hidden.
8. **`run promote` takes several runs, never a group** (assumed): `beamtime run promote <run>...`; a group would
   promote whatever happened to be hidden there. Already visible runs are reported, not an error. No hide op in
   v0.3 (question 3).
9. **The UI shows hidden runs on demand** (assumed): the group header says "N hidden" when there are any; it links
   to `?hidden`, which lists them (name, status, age) above the view with a Promote button each; a hidden run's
   page shows a "Hidden" mark (`eye-off`, muted) and a Promote button. Charts and tables of views never include
   hidden runs; a view may opt in with `hidden: true` in a query. Rejected: a page-wide toggle that rewrites every
   query of the view (deep change to compile and every block).
10. **Direction tokens** (audit item 1): split the leaf (after the last `/`) on `_ . - /` and camelCase; lower is
    better when any token is in `loss losses err error errors ppl perplexity nll mse rmse mae wer cer`. `rmse`,
    `error(s)` and `losses` keep what the substring rule got right. The TS side reads the word list from the
    generated `chart-defaults.ts` and has one `lowerIsBetter` in `fmt.ts`; `prefs.ts` uses it.
11. **One seed rule** (audit item 5): `is_seed` accepts the leaves `seed`, `random_seed`, `rng_seed`;
    `seed_key(varying)` is the one varying `config.` key `is_seed` accepts when exactly one exists, else `None`;
    the default view, `settings.settle`, `validate.py` and the web's "mean over seeds" use it, falling back to
    `config.seed`; `aggregate.seed_groups` accepts nested config fields. When the UI plan's item 6 changes when the
    default view merges, it keeps calling `seed_key` (overlap, see N42).
12. **Ticket budget 140k** (assumed default).
13. **Failure signature** (audit item 9): quoted strings become `<str>`, absolute or relative paths (`/`, `~/`,
    `./`, `../`, `X:\`) become `<path>`, then numbers and hex `#`; a last line that is a bare type
    (`^[A-Za-z_][\w.]*:?$`) becomes `<type> (after: <line before>)`; the cut at 120 comes last.
14. **Heartbeat age** (audit item 10): the card answer carries `heartbeat_age_s` (int) for a lost run; the CLI
    card says `lost (no heartbeat for 7 min)`, the run header and drawer the same with the UI's `duration`.

## U. Hidden runs

### U40. Spec: hidden runs (sonnet + review) — code — **done**

- **Touches:** `docs/design/01-storage.md` (§ Directory l. 179, § `_run.json` l. 204–280, § Deleting and cleaning up
  l. 461–487, § Decisions), `docs/design/02-sdk.md` (§ `init` l. 56–80, § Resume l. 188), `docs/design/03-index.md`
  (§ Fields l. 211, § Selecting runs l. 269–306), `docs/design/09-research-record.md` (§ Versions l. 32, § The check
  l. 150, § Group status l. 258), `docs/design/08-cli-mcp.md` (§ Writing l. 58–67, § Shared conventions l. 115),
  `docs/design/07-web-ui.md` (§ Writing from the UI l. 307–335).
- **Read:** this plan's Brief and decisions 1–9; `docs/design/01-storage.md` § `_run.json` (`imported_from`, the
  precedent).
- **Check:** `uv run pytest -q tests/test_docs.py`; `git diff --stat` lists only `docs/design/` files of this ticket.
- **Done:** every bullet of the Brief's first four entries and decisions 2–9 is in a spec section; `10-setup.md`
  untouched; the line counts above refreshed in U41–U45 if the spec moved them.
- **Risks:** the setup session's uncommitted edits in the same files → stop (Stop if); a spec that contradicts
  "every file has one writer" (the SDK must never write `visibility/`) → reviewer checks 01-storage.
- **Stop if:** `git status --short docs/design` shows changes not made by this ticket.

Write the design before code (CLAUDE.md: a deviation is decided and written back before the code lands).

1. 01-storage: `hidden` in the `_run.json` example comment and a bullet: "**`hidden`** (optional, `true` only)…
   readers treat a missing field as visible, and the `schema` stays 1." Add `visibility/` to the run directory
   listing (`[authored]`) and a bullet next to the display name in § Deleting and cleaning up: "**Promoting a hidden
   run**: `beamtime run promote <run>` writes `visibility/<id>.yaml` (`{schema, hidden: false, reason, author,
   user}`); the newest version wins over `_run.json`."
2. 02-sdk § `init`: the `hidden` argument and `BEAMTIME_HIDDEN` (`1`, `true`, `yes`, any case; an explicit argument
   wins); § Resume: a continued run keeps its visibility (decision 7).
3. 03-index: field `run.hidden`; § Selecting runs: `hidden: false` (default) leaves hidden runs out of every kind,
   `true` includes them, a run named in `from` always counts; `groups` counts visible runs and has a `hidden` column.
4. 09-research-record: membership counts visible runs only (§ Versions: a version is frozen once a *visible* run
   records it; § The check; § Group status), decision 5's `ref` and promotion rules.
5. 08-cli-mcp: `beamtime run promote <run>...` ↔ `run_promote` in § Writing; `--hidden` in § Shared conventions;
   the `status` hint (decision 6).
6. 07-web-ui § Writing from the UI: decision 9 in two or three sentences, and "Promote" in the edit table.

### U41. The flag in the files and the SDK (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/format/constants.py` (`NAME` 27–28: add `VISIBILITY = "visibility"`),
  `src/beamtime/format/schema.py` (`SCHEMAS` 6–24), `src/beamtime/format/run.py` (`RunInfo` 25–49,
  `read_run_info` 52–92, new `run_hidden`), `src/beamtime/sdk/run.py` (`init` 1020–1087, `new_run` 1090–1180,
  `continue_run` 1183–1224), `tests/format/test_run.py`, `tests/sdk/test_run.py` (or the SDK test file that covers
  `init` arguments; `rg -n 'def test_.*key' tests/sdk`).
- **Read:** `docs/design/01-storage.md` § `_run.json` and § Deleting and cleaning up as U40 left them;
  `docs/design/02-sdk.md` § `init`.
- **Check:** `uv run pytest -q tests/format/test_run.py tests/sdk`; the 3.10 command (How to execute 1).
- **Done:** a script run with `hidden=True` and one with `BEAMTIME_HIDDEN=1` write `"hidden": true`; a default run's
  `_run.json` has no `hidden` key; `read_run_info(...).hidden` is `False` for every golden run; `run_hidden` honours
  the newest `visibility/` version.
- **Risks:** `BEAMTIME_HIDDEN=0` or `false` must not hide (`test_hidden_env_values`); a damaged newest `visibility/`
  file falls back to `_run.json`, never raises (`test_run_hidden_damaged_version`); resuming a hidden run with
  `hidden=False` keeps it hidden and warns (`test_resume_keeps_hidden`); `hidden="yes"` (not a bool) raises
  `ValueError` in `init` like bad `tags` (`test_hidden_must_be_bool`).
- **Stop if:** the SDK would need to write anything in `visibility/`.

1. `constants.VISIBILITY = "visibility"` with a comment like `NAME`'s (run-only, no group name reserved); `SCHEMAS`
   gains `"visibility": 1`.
2. `RunInfo.hidden: bool = False`; `read_run_info` reads `hidden=d.get("hidden") is True`.
3. `run_hidden(run_dir: Path, info: dict[str, Any] | RunInfo) -> bool`: newest version in `run_dir / VISIBILITY`
   (imports `newest`, `read_yaml_doc` inside, kind `visibility`); its `hidden` when it is a bool; else the flag
   from `info`. Damaged files (`SchemaError`, `ValueError`, `OSError`) fall back.
4. SDK `init(..., hidden: bool | None = None)` after `system_metrics`; docstring line; `None` reads
   `BEAMTIME_HIDDEN` (`strip().lower() in ("1", "true", "yes")`); pass it to `new_run(..., hidden=...)`, which adds
   `info["hidden"] = True` after `key` only when true. In `continue_run` path: if the resolved run's stored flag
   differs from an explicit `hidden`, `run.warn("hidden", "a continued run keeps its visibility")`.
5. Lightning (`src/beamtime/lightning.py:26`) passes `**kwargs` to `init`, so nothing changes there; mention
   `hidden` in its docstring only if it lists `init`'s arguments.

### U42. Hidden in the index and every selection (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/index/store.py` (`SCHEMA_VERSION` 10, `runs` table 14–36),
  `src/beamtime/index/ingest.py` (`ingest_meta` 104–133, `authored_mtime` 284–293), `src/beamtime/query/fields.py`
  (`RUN_COLUMNS` 26–35), `src/beamtime/query/models.py` (`Selection` 102–107), `src/beamtime/query/select.py`
  (`known_keys` 84–95, `scope_condition` 98–114, `check_known` 117–140, `select_runs` 185–242),
  `src/beamtime/query/kinds.py` (the `scope_condition(ctx)` call at 98, `groups_kind` 651–711),
  `src/beamtime/ops/reading.py` (`status` 1043–1070: counts only), `tests/query/test_queries.py`,
  `tests/index/test_index.py`.
- **Read:** `docs/design/03-index.md` § Selecting runs as U40 left it.
- **Check:** `uv run pytest -q tests/query tests/index tests/ops/test_ops.py`.
- **Done:** with one hidden and two visible runs in a group, `runs`, `keys`, `series`, `timeline`, `wait`,
  `diagnose` and `groups` counts see two; with `hidden: true` three; `{runs: {from: <hidden id>}}` sees it; writing
  a `visibility/` file and catching up flips `runs.hidden`; an old cache (schema 3) rebuilds.
- **Risks:** `check_known` must look at hidden runs when `hidden` is set, or `--hidden --where config.x=1` on a key
  only hidden runs have errors (`test_hidden_only_key`); the `depth` condition and the hidden condition combine with
  `AND` in the right order (`test_hidden_with_depth`); `groups --hidden` counts them, `groups` alone puts them in
  the `hidden` column only (`test_groups_hidden_column`); a promoted run reappears after `catch_up` without a
  `reindex` (`test_promotion_is_ingested`).
- **Stop if:** a kind selects runs without `scope_condition` or `select_runs` beyond the three in Findings row 2.

1. Table column `hidden INTEGER NOT NULL DEFAULT 0` after `heartbeat`; `SCHEMA_VERSION = 4`.
2. `ingest_meta`: `"hidden": int(run_hidden(run_dir, info))`; `authored_mtime` checks `(c.NOTES, c.NAME,
   c.VISIBILITY)`.
3. `RUN_COLUMNS["hidden"] = "hidden"`, so `run.hidden` is a field (it decodes to a bool; check `decode_cell`).
4. `Selection.hidden: Annotated[bool, msgspec.Meta(description="include hidden (test) runs")] = False`. It is a
   field of every kind with a selection; remotes get it only when true (see Not verified).
5. `scope_condition(ctx, depth="all", hidden=False)`: when `ctx.run_id is None and not hidden` append
   `" AND runs.hidden = 0"`. `known_keys(ctx, what, hidden=False)`, `check_known(ctx, fields, hidden=False)` pass it
   through; `select_runs` passes `sel.hidden`; `kinds.py:98` passes `q.hidden`.
6. `groups_kind`: the statuses query reads `hidden` too; counts use visible runs unless `q.hidden`; a new last
   column `hidden` counts the hidden runs below the path.
7. `status`: count visible runs only (`WHERE hidden = 0`); the hint is U44's.

### U43. Hidden runs never count in the record (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/record/proposals.py` (`Target.membership` 332–347), `src/beamtime/record/check.py`
  (`reference` 325–343), new `tests/record/test_hidden.py`.
- **Read:** `docs/design/09-research-record.md` § Versions, § The check, § Group status as U40 left them;
  `tests/record/test_end_to_end.py` for how runs and proposals are set up.
- **Check:** `uv run pytest -q tests/record tests/query`.
- **Done:** in `test_hidden.py`, a `compare` proposal with two visible runs per arm and a hidden third seed reports
  `n=2` per arm; a group whose only run is hidden is `proposed` and its proposal not frozen (`proposal set` without
  `--reason` succeeds); after a `visibility/` file and catch-up the run counts and the version is frozen.
- **Risks:** a `ref` naming a hidden run → the prediction reads the reference as missing (`test_hidden_reference`);
  `plan missing` still lists a grid point whose only run is hidden (`test_hidden_plan_point`); the run's own
  proposal (`.`) of a hidden run: `research_status` of the run itself still answers (`test_hidden_run_own_proposal`).
- **Stop if:** something other than `membership` decides frozen-ness (`ops/record.py:108` uses `members`).

1. `membership`: append `AND runs.hidden = 0` to both returned conditions.
2. `reference`: unchanged code path, since `select_runs` with `m.Selection()` and `ctx.run_id=None` already
   filters; add the test that proves it.

### U44. `run promote`, the card and the status hint (sonnet + review) — code

- **Touches:** `src/beamtime/ops/registry.py` (new `RunPromoteParams` after `NameParams` 235–240, new `Op` after
  `name` 1232–1240), `src/beamtime/ops/record.py` (new `run_promote` after `name` 199–214),
  `src/beamtime/ops/answers.py` (`WRITES` 591–594), `src/beamtime/ops/reading.py` (`card` 851–915, `status`
  1043–1075), `src/beamtime/cli/format.py` (`render_card` 364–400, `render_status` ~610–647),
  `docs/reference/cli.md` (generated), `tests/ops/test_ops.py`, `tests/cli/test_record.py`.
- **Read:** `docs/design/08-cli-mcp.md` § Writing and § Policy; decision 6 and 8.
- **Check:** `uv run python docs/site/reference.py && uv run pytest -q tests/ops tests/cli tests/mcp
  tests/test_docs.py`.
- **Done:** `beamtime run promote <id>` writes `visibility/<id>.yaml` with `hidden: false`, the author and user,
  and the run then shows in `runs`; MCP lists `run_promote`; `card` has `run.hidden`; `status` shows the hint for a
  hidden run whose `created_at` is 8 days old and none for a 1-day-old one.
- **Risks:** a group as argument → `OpError` code 2 (`test_promote_refuses_group`); a visible run → a line "already
  visible", no file (`test_promote_visible_run`); a version edited after the hidden run recorded it → a warning line
  from `Target.hash_problem` (`test_promote_warns_on_edited_proposal`); the op over a remote (`@box/<id>`) routes
  like `name` (`writes=True`; `test_promote_routes` in `tests/remote` if `name` has one).
- **Stop if:** the CLI parser can't take a space-separated op name whose first word is also no op (`run`).

1. `RunPromoteParams(Params)`: `runs: Annotated[list[RunId], msgspec.Meta(description="hidden runs to count from
   now on")]`, `reason: str | None = None`, `author: Author = None`.
2. `Op(name="run promote", kind="run promote", writes=True, params=RunPromoteParams, impl=f"{W}:run_promote",
   positional=("runs",), summary="Count hidden (test) runs like any run from now on.")`; add `"run promote"` to
   `WRITES`.
3. `run_promote(ctx, p)`: for each run, `target_of(ctx, run)`; refuse groups; skip visible ones with a line; else
   `save(target.dir / c.VISIBILITY, ".yaml", dump({"schema": 1, "hidden": False, **reason, "author", "user"}))`;
   then for every proposal key the run recorded, the hash check of decision 5. Return `written(...)` like `name`.
4. `card`: `"hidden": run_hidden(run_dir, info)` in `run`; `render_card` adds `hidden` after the status word.
5. `status`: `hidden = {"count": n, "old": [ids with created_at older than HIDDEN_OLD_S = 7 * 86400, newest
   first, at most 5]}`; `render_status` prints the line of decision 6 only when `count`.

### U45. Hidden runs in the web UI (sonnet) — code

- **Touches:** `web/src/router.ts` (`Route` 6–21, `parse` 29–52, `groupUrl` 54–67), `web/src/shell/calls.ts` (new
  `hiddenRuns`), `web/src/bt/writes.ts` (new `promoteRun` after `renameRun` 62–65), `web/src/shell/header.ts`
  (`GroupHeader` 43–66, `RunHeader` 124–160), the group page that renders the header (`web/src/shell/page.ts`),
  `web/test/` (a router test), `src/beamtime/serve/static/` (rebuilt).
- **Read:** `docs/design/07-web-ui.md` § Writing from the UI as U40 left it; `design/README.md`; decision 9.
- **Check:** `cd web && npm ci && npm test && npm run build`; `uv run pytest -q tests/serve`.
- **Done:** a group with a hidden run shows "1 hidden" in the header facts; `?hidden` lists it with a Promote button;
  promoting refreshes the list, the tree counts and the run table; a hidden run's page shows the Hidden mark and a
  Promote button; `groupUrl(path, {hidden: true})` round-trips through `parse`.
- **Risks:** `ViewPrefs.hidden` (hidden charts) in `web/src/bt/prefs.ts` already uses the word: keep the route field
  named `hiddenRuns` (`router.test.ts`); a remote of 0.2 has no `hidden` column → no fact shown, no error; the shell
  stays under 120 KB compressed.
- **Stop if:** the list needs a new design component beyond `Sym`, `IconButton` and the facts row (design changes
  go through `design/`).

1. Route: `hiddenRuns: boolean` from `q.has("hidden")`; `groupUrl` opt `hidden`.
2. `calls.hiddenRuns(path)`: `runs` with `{from: path, hidden: true, where: {"run.hidden": true}, select:
   ["run.name", "run.status", "run.created_at"], limit: 200}`.
3. `promoteRun(run, scope)`: `post("run_promote", {runs: [run]})`, then `refresh(scope, ["card", "runs",
   "groups", "summary", "series", "keys"])`.
4. Header facts: `row.hidden ? <a href=groupUrl(path, {hidden: true})><b>n</b> hidden</a>`; the list renders under
   the header when the route says so, one row per run (link to the run, status symbol, `ago`, Promote).
5. RunHeader: when `card.run.hidden`, a `Sym` `{icon: "eye-off", tone: "muted", label: "Hidden: left out of
   tables, counts and checks"}` with its word, and a "Promote" item in the details menu plus an `IconButton`.

### U46. The guide and the user docs (haiku) — code

- **Touches:** `src/beamtime/guide/parts/proposals.md` (§ Write one before launching l. 7–26),
  `docs/guides/agents.md`, `docs/quickstart.md` (one line where `init` is shown), `tests/guide/test_guide.py` if it
  pins the part's text.
- **Read:** `docs/design/02-sdk.md` § `init` and `08-cli-mcp.md` § Writing as U40 left them.
- **Check:** `uv run pytest -q tests/guide tests/test_docs.py tests/mcp/test_skills.py`.
- **Done:** `beamtime guide proposals` explains in four to six lines: smoke tests and debugging runs go hidden
  (`BEAMTIME_HIDDEN=1 python train.py`), they never count in checks, `run promote` makes one count, deleting is the
  user's (`beamtime rm`); the agents guide has the same in two lines.
- **Risks:** `src/beamtime/guide/rules/rules.md` must stay untouched (How to execute 3); skills generated from `skills.py` stay
  current (`tests/mcp/test_skills.py`).
- **Stop if:** the text only fits in the rules block.

## N. Detection rules from the audit

### N41. Direction from whole tokens (sonnet) — code

- **Touches:** `src/beamtime/views/defaults.py` (`LOWER_IS_BETTER` 18, `lower_is_better` 309–315),
  `src/beamtime/views/settings.py` (`generated_ts` 107–118), `web/src/bt/chart-defaults.ts` (generated),
  `web/src/bt/fmt.ts` (`LOWER_IS_BETTER`, `lowerIsBetter` 121–128), `web/src/bt/prefs.ts` (`LOWER_IS_BETTER`,
  `higherIsBetter` 32–33), `docs/design/07-web-ui.md` (§ Implementation notes, "starts from the name" l. 482),
  `tests/views/test_views.py`, `web/test/fmt.test.ts`, `src/beamtime/serve/static/`.
- **Read:** audit item 1; decision 10.
- **Check:** `scripts/build-chart-defaults && uv run pytest -q tests/views && cd web && npm test && npm run build`.
- **Done:** one case table in both tests: `val/loss`, `train_loss_ema`, `valLoss`, `rmse`, `error_rate`, `wer` lower;
  `power`, `answer_acc`, `lower_bound`, `tower_score`, `acc` higher; the TS has one word list (generated) and one
  function.
- **Risks:** `metric.val/loss.min` field form in `fmt.ts` keeps its prefix strip (`fmt.test.ts`); camelCase split of
  `NLLLoss` → `nll`, `loss` (case table); a view whose stored pin direction equalled the old guess flips for names
  like `power` (Breaking changes).
- **Stop if:** another copy of the word list turns up (`rg -n 'perplexity' src web/src`).

1. `tokens(leaf) -> list[str]`: `re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", leaf)` plus `([A-Z]+)([A-Z][a-z])`, then
   split on `[_.\-/]+`, lowercase.
2. `lower_is_better`: `any(t in LOWER_IS_BETTER for t in tokens(leaf))` with decision 10's words.
3. `generated_ts` also emits `export const LOWER_IS_BETTER = [...]`; `fmt.ts` imports it and tokenizes the same way;
   `prefs.ts` `higherIsBetter = (y) => !lowerIsBetter(y)` from `fmt.ts`.

### N42. One seed rule on the server (sonnet + review) — code

- **Touches:** `src/beamtime/query/distinguish.py` (`is_seed` 95–101, new `seed_key`), `src/beamtime/query/kinds.py`
  (`keys_kind` 112–170: `config.seed`), `src/beamtime/query/aggregate.py` (`seed_groups` ~20–40: the top-level
  restriction), `src/beamtime/views/defaults.py` (`group_body` 72–100, the best-run query ~177),
  `src/beamtime/views/settings.py` (`settle` 38–70), `src/beamtime/views/prefs.py` (`settle` 125–130 and its callers
  57, 71), `src/beamtime/views/validate.py` (~379), `docs/design/03-index.md` (§ Selecting runs, Seeds l. 297),
  `docs/design/07-web-ui.md` (l. 474), `tests/query/test_distinguish.py`, `tests/views/test_settings.py`.
- **Read:** audit items 5 and 6; decision 11.
- **Check:** `uv run pytest -q tests/query tests/views`.
- **Done:** a group seeded by `trainer.seed` gets `keys.config.seed == "config.trainer.seed"` and the default view
  merges on it above the threshold; `random_seed` and `rng_seed` count as seeds; two seed-like varying keys give
  `None` and the view falls back to no merging; `seeds: config.trainer.seed` aggregates.
- **Risks:** `data_seed` must not count (`test_data_seed_is_no_seed`); a quoted key (`config.["a.b"].seed`) in
  `seed_groups` (`test_nested_seed_field`); a seed that doesn't vary (one seed) → `None`, not merged
  (`test_constant_seed`).
- **Stop if:** the UI plan has already changed `group_body`'s merge condition (item 6): then only replace
  `SEEDS_FIELD` with `seed_key(varying) or SEEDS_FIELD` there and keep its condition.

Overlap: the UI plan's item 6 rewrites when the default view merges (`defaults.py` 87, `SEED_GROUPING_ABOVE`). This
ticket changes only *which key*, not *when*; whichever lands second rebases onto the other.

1. `is_seed`: leaf in `("seed", "random_seed", "rng_seed")`.
2. `seed_key(varying: list[str]) -> str | None` next to it: the single `k` with `is_seed(k.removeprefix("config."))`.
3. `keys_kind`: `"seed": seed_key(distinct.varying)` in `config`.
4. `seed_groups`: accept any `config.` field; compare by the flattened key spelling `flatten` produces.
5. Default view, best-run query and `validate.py`: the group's `keys["config"]["seed"]` instead of `SEEDS_FIELD`
   (fallback `SEEDS_FIELD`). `settings.settle(props, settings, seed=SEEDS_FIELD)`; `prefs.py` callers pass the
   group's seed key.

### N43. One seed rule in the web UI (sonnet) — code

- **Touches:** `web/src/bt/chart-settings.ts` (`seriesCall` 25–40), `web/src/blocks/line.ts` (where it calls
  `seriesCall`), `web/src/blocks/line-settings.ts` (l. 179 filter), `web/test/chart-settings.test.ts`,
  `src/beamtime/serve/static/`.
- **Read:** N42's steps; decision 11.
- **Check:** `cd web && npm ci && npm test && npm run build`.
- **Done:** choosing "mean over seeds" on a `trainer.seed` group sends `seeds: "config.trainer.seed"`; the Color by
  list leaves out the group's seed key, not the literal `config.seed`.
- **Risks:** an exported page (no server) keeps the node's own `seeds` (`chart-settings.test.ts`); the `keys` call
  must be the header's exact call so it is a cache hit (`{method: "keys", params: {from: path}, scope: path}`).
- **Stop if:** the UI plan changed `seriesCall`'s signature; rebase onto it instead.

1. `seriesCall(node, prefs, {zoom, width, seed})`: `params.seeds = base.params.seeds ?? opts.seed ?? SEEDS_FIELD`
   when `prefs.by === "seeds"`.
2. `line.ts` reads the seed from the shared `keys` call; `line-settings.ts` filters `keys.config.seed`.

### N44. A failure signature that ignores paths and quotes (sonnet) — code

- **Touches:** `src/beamtime/query/facts.py` (`failure_key` 107–115, `failure_signature` 118–124),
  `docs/design/03-index.md` (l. 255), `tests/query/test_facts.py` (`test_failure_key` 149–159).
- **Read:** audit item 9; decision 13.
- **Check:** `uv run pytest -q tests/query/test_facts.py tests/ops`.
- **Done:** `FileNotFoundError: [Errno 2] No such file or directory: '/scratch/a/run1.pt'` and `…run2.pt` share one
  signature; `No such file: /scratch/a/run1.pt` and `/scratch/b/run2.pt` too; a traceback ending in `KeyError` after
  `  File "x.py", line 3, in f` reads `KeyError (after: File "x.py", line #, in f)` normalized; the existing
  assertions of `test_failure_key` hold.
- **Risks:** a message with `val/loss` (no leading `/`) stays as is (`test_metric_names_are_no_paths`); an apostrophe
  in prose (`can't find it`) doesn't eat the line (`test_apostrophe`); `failure_key(None, trace)` now joins the whole
  traceback list (`test_failure_key`).
- **Stop if:** a caller stores signatures (they are grouping labels only, 03-index l. 255).

1. `QUOTED = r"'[^'\n]*'|\"[^\"\n]*\""` → `<str>`, only when the quote opens after a non-word character.
2. `PATH = r"(?:[A-Za-z]:\\|~/|\.{1,2}/|/)[^\s'\",;:)]+"` → `<path>`; then numbers and hex → `#`.
3. Bare type rule of decision 13; `failure_key` passes `"\n".join(traceback)`.

### N45. Lost runs show the heartbeat's age (sonnet) — code

- **Touches:** `src/beamtime/format/times.py` (new `age_text`), `src/beamtime/ops/reading.py` (`card` 851–915),
  `src/beamtime/cli/format.py` (`render_card` 364–371), `web/src/shell/header.ts` (`RunHeader` 124–135),
  `web/src/shell/drawer.ts` (`RunContext` status line), `docs/design/01-storage.md` (§ `_run.json`, the lost bullet;
  after U40), `tests/ops/test_ops.py`, new `tests/format/test_times.py`,
  `src/beamtime/serve/static/`.
- **Read:** audit item 10; decision 14.
- **Check:** `uv run pytest -q tests/ops tests/format && cd web && npm test && npm run build`.
- **Done:** a run whose `_run.json` mtime is 7 min old reads `lost (no heartbeat for 7 min)` in `beamtime card`; the
  card answer has `heartbeat_age_s` 420 ± 5; a running run has no such field; the UI's run header tip says "no
  heartbeat for 7m".
- **Risks:** a pulled snapshot judges the age at the snapshot's time (`ctx.now`), not wall time
  (`test_lost_age_in_snapshot`); `age_text` boundaries 89 s, 90 s, 90 min, 36 h (`test_age_text`).
- **Stop if:** the age is wanted in `runs` tables too (a field; ask).

1. `age_text(seconds: float) -> str`: `< 90` → `"N s"`, `< 90 min` → `"N min"`, `< 36 h` → `"N h"`, else `"N d"`.
2. `card`: `"heartbeat_age_s": round(now - heartbeat)` when `status == "lost"`.
3. `render_card` and the UI as in decision 14.

## Close

### U47. Changelog and project notes (haiku) — code

- **Touches:** `CHANGELOG.md` (§ 0.3.0), `CLAUDE.md` (§ Decisions so far: one bullet on hidden runs).
- **Read:** this plan's Goal and Breaking changes.
- **Check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`; the 3.10 command; `git diff
  --stat fb352bd -- tests/golden` empty.
- **Done:** the changelog lists hidden runs, `run promote`, `--hidden`, and every Breaking change below; the Goal's
  checks pass.
- **Risks:** a changelog entry that claims a remote of 0.2 understands `hidden` (it doesn't; Not verified).
- **Stop if:** a Goal check fails; report it instead of patching here.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| Index cache | schema 3 | schema 4 | rebuilds itself on first open |
| `groups` columns | ends with `notes` | adds `hidden` | read columns by name |
| `status` run counts | all runs | visible runs, plus `hidden` | none |
| Metric direction | substring (`power` lower) | whole tokens (`power` higher) | set `metrics: {power: {higher_is_better: false}}` in a view |
| Seed key in default view | `config.seed` only | the one seed key in the group | name `seeds:` in a view to pin it |
| Failure signatures | paths and quotes kept | `<path>`, `<str>` | none; labels only |

## Not verified

- Whether the CLI and the UI send `hidden: false` to remotes (msgspec defaults): a 0.2 remote refuses unknown
  fields (`forbid_unknown_fields`). U42 checks how `remote/route.py` encodes params and sends `hidden` only when true.
- That `decode_cell` turns the `hidden` integer column into a bool for `run.hidden` (U42 step 3).
- That the CLI parser accepts `run promote` with `run` as a new first word (U44 Stop if).
- That `aggregate.seed_groups` works on nested keys once the restriction goes (N42 starts with the failing test).
- The line numbers in `docs/design/` were read from a working tree with the setup session's uncommitted edits; U40
  refreshes them.

## Questions for the user

1. **The name**: `hidden` (recommended: says what it does in every flag and message) or `undercover`?
2. **The status hint**: should `status` list hidden runs older than 7 days with the `beamtime rm` command for you
   (recommended: yes, ids only, at most 5)?
3. **A hide op**: should agents be able to hide a visible run again (`run hide`)? Recommended: no for v0.3; the
   `visibility/` format allows it later.
4. **Hidden runs and their group's proposal**: hidden runs don't freeze a proposal version (recommended), so a
   smoke test before the sweep needs no `--reason` supersede. Agree?
