# Benchmark: agents with Beamtime against plain files and TensorBoard

Base commit `fb352bd`, branch `setup`. Proposed 2026-11-15, based on the v0.3 benchmark brief (four setups,
about eight researcher tasks, tokens and speed as one or two README figures), a reading of
`bench/agents/` (README, `run.py`, `score.py`, `report.py`, `mine.py`, 35 tasks, `RESULTS.md`,
`MISTAKES.md`, the batch `runs/20261108-213034`), `src/beamtime/synth/generate.py`, the guide's rules
block and the docs build. Planned in the background without an interview; the assumed decisions are
marked "assumed". No breaking changes: everything new lives in `bench/agents/compare/`, tests and docs.
Notes and the cost estimate: [notes.md](notes.md).

Run a ticket with `/run-ticket docs/plans/v0.3/benchmark/benchmark-plan.md <ID>` in a fresh session;
review tickets marked `+ review` with `/review-ticket docs/plans/v0.3/benchmark/benchmark-plan.md <ID>`
on a stronger model. `ticket.py status <this file>` shows what's done and what's next.

## Goal

- **Done means:** one command runs the same eight researcher tasks over the same synthetic numbers in
  four setups (Beamtime over MCP, Beamtime over the CLI, plain files, TensorBoard event files), three
  data seeds each, on one recorded model; every session is graded automatically against truth computed
  from the data; a report writes a table of every measure and two figures (tokens vs score; wall time
  per task), and the README and a docs guide show them with the method and the published tasks.
- **Confirmed by:** `uv run pytest -q tests/bench` (exporters, truth, grader, setups, report on fixture
  records, no agents); `uv run python bench/agents/compare/sessions.py --dry-run` lists 96 sessions with
  their commands; after the user starts the real run, `tables.py <batch>` writes
  `docs/guides/benchmark/` (table, `.pdf` and `.svg` figures) and `cd web && npm run docs` builds the
  guide without broken links.
- **Out of scope:** W&B (no fully offline read path; see Decision 3); Beamtime-only tasks (views,
  waiting for runs, lost runs; they stay in the existing harness); more than one model; tuning the guide
  to the benchmark's tasks; running any agent inside a ticket (only L72, started by the user).

## Findings

Evidence: **reproduced** (run), **real data** (seen in the user's data), **code** (read, not run).

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | `bench/agents/run.py` cannot set up any project: `ImportError: cannot import name 'END' from 'beamtime.ops.admin'` | A12 (`c6e7b67`) moved the rules block to `beamtime.guide.rules` (`START`, `END` l. 11, `render` 31, `write_block` 163) and removed `admin.instructions`; `run.py` `project` still imports it (l. 113) and calls it (l. 128, 130) | reproduced | N71 |
| 2 | Every synth log dir carries its answers: `_synth.json` (planted effects), proposals stating "lr 3e-4 gives the best final val/acc", verdict notes and a memory saying the same | `generate` writes the manifest (`generate.py` 873) and `record()`/`run()` write the record (124–136, 194–272) | code | M71 |
| 3 | Whether lr 3e-4's lead over the runner-up (1e-3) is significant depends on the seed: Welch 95 % CI excludes 0 for seeds 9, 10, 11, not for 7, 8 | noise 0.003 on the final value and on the last eval vs a planted gap of about 0.009 | reproduced | M74, J71 |
| 4 | Counting the killed lr-3e-4 run flips the winner (3e-4 mean 0.910 < 1e-3 mean 0.920 on seeds 7–11) | the killed run stops at 40 % (`killed`, `generate.py` 553) | reproduced | M74, J71 |
| 5 | Existing analysis facts are regexes fixed to seed 7 (`0\.9[23]`, `0\.[345]`), so they cannot grade other seeds | facts are literals in `tasks/*.yaml` | code | M74 |
| 6 | Session projects live inside the repo (`bench/agents/runs/`), where an agent with Bash can read `src/beamtime/synth/generate.py` (`BEST_LR` l. 24) | `RUNS = HERE / "runs"` (`run.py` 24) | code | J73 |
| 7 | Today's harness gives no Bash (`TOOLS` `run.py` 27), records tokens as one dict without the model id, and reads the model only implicitly; the init event has `model`, the result `usage` and `modelUsage` | `summary` (`run.py` 209–255) | real data (`runs/20261108-213034/*/transcript.jsonl`) | J74 |
| 8 | Beamtime over MCP on sonnet, analysis tasks: mean 68k tokens (55k cache read, 13k cache write, 0.7k out), 12 s, $0.063 per session | baseline batch | real data | notes |

## Brief

- **Home** (all): `bench/agents/compare/`, scripts run as `uv run python bench/agents/compare/<x>.py`;
  they `sys.path.append` `bench/agents` to reuse `run.summary` and `score.ask`. Tests in `tests/bench/`
  (new package, `__init__.py`) put both folders on `sys.path`.
- **Data** (M71): `data.make_logdir(dest, seed=, now=) -> Manifest` generates scale `s` (47 runs, five
  groups) and strips `_synth.json`, every `proposal/`, `notes/`, `memory/`, and `proposals`/
  `proposal_hashes` in `_run.json`. Seeds 7, 8, 9.
- **Formats** (M72, M73): `formats.export_files(logdir, dest)` → `runs/<group>/<run id>/{config.json,
  metrics.csv, output.log}`; `formats.export_tensorboard(logdir, dest)` → `tb/<group>/<run id>/{events…,
  hparams.yaml, output.log}`. Both read the effective metrics (`read_effective_metrics`), so a resumed
  run has one series. Run ids are folder names everywhere, so answers compare across setups.
- **Truth** (M74): `truth.compute(files_root, logdir) -> dict[task_id, dict]`, pure Python over the
  plain-files export (status from `_run.json`); computed at grading time only, never written into a
  session's reach.
- **Tasks and grading** (J71, J72): `tasks/<id>.yaml` (prompt, answer schema, checks, time limit,
  setups); every prompt ends with "End your reply with a fenced json block: {…}". `grade.grade(task,
  answer_text, truth, project) -> Grade(score: float, correct: bool, checks: dict)`.
- **Setups and sessions** (J73, J74): `setups.SETUPS` = `mcp`, `cli`, `files`, `tensorboard`;
  `setups.prepare(setup, session_dir, data_dir) -> Project`; `sessions.py` runs `claude -p` per (task,
  setup, seed) and writes `record.json` + `grade.json`. Projects live outside the repo.
- **Report** (L71): `tables.py <batch>` → `docs/guides/benchmark/results.md` fragment and figures
  `tokens-vs-score.{pdf,svg}`, `time-per-task.{pdf,svg}`.

Done, for every ticket: its Done line holds; its Check passes; `bench/agents/README.md` and the docs say
what the code does; its heading is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check .` (bench and tests are excluded from ruff
   but keep their style); `uv run pytest -q tests/bench` while working; the full suite
   `uv run pytest -q` before committing. TensorBoard tests need
   `uv run --with tensorboard pytest -q tests/bench` and `pytest.importorskip("tensorboard")` elsewhere.
2. Never start `claude`, an agent, a judge or a paid API call in a ticket, except L72 when the user says
   so. Tests stub `subprocess.run` for `claude`.
3. Rules: CLAUDE.md style (docstrings, `str | None`, keyword-only constructors, `match` with a
   `case _: raise ValueError`). No new project dependencies: tensorboard, pandas and scipy live only in
   the benchmark's own environments (J73). Figures follow CLAUDE.md § Visualization exactly.
4. Don't touch `docs/design/`, `docs/plans/setup/` or `src/beamtime/` (another session has uncommitted
   work there; the plan needs no product change).
5. Ticket budget: 140k tokens (assumed default); split a ticket that would exceed it.
6. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to
   the ticket's heading.

## Order

```
N71                       independent (harness repair)
M71 ─┬─ M72 ─ M74 ─ J71 ─ J72
    └─ M73 ───────────────┐
                    J73 ─ J74 ─ L71 ─ L72 (user starts) ─ U71 ─ U72
```

What's left runs in this order: N71 M71 M72 M73 M74 J71 J72 J73 J74 L71 L72 U71 U72

## Decisions taken; say if you want otherwise

1. **Four setups, same tools** (assumed): every session gets `Bash,Read,Write,Edit,Glob,Grep`; `mcp`
   adds Beamtime's MCP server; `cli` has `beamtime` on the PATH and no MCP server. Rejected: MCP without
   Bash, because a real agent has Bash and the figure would then compare tool sets, not data access.
2. **One CLAUDE.md shape** (assumed): an identical preamble, then one setup section (the tool
   description): for `mcp`/`cli` the rules block as shipped (`guide.rules.render` with the project's
   default agent settings, 217 words), for `files`/`tensorboard` a short description of the files. The
   same line names the Python libraries in all four. Rejected: trimming Beamtime's rules to analysis,
   because the benchmark measures the product as shipped.
3. **W&B is out**: offline mode only writes `.wandb` files for a later `wandb sync`; reading runs back
   needs the W&B server (cloud, or the `wandb/local` container, which needs a license key from an
   account). There is no offline query path, so the setup would not be "fully offline" (not run; see
   Not verified).
4. **Data: synth scale `s`, seeds 7, 8, 9, record stripped** (assumed): seed 7 and 8 make "is it
   significant" a no, 9 a yes (Finding 3). No setup sees proposals, notes, memory or `_synth.json`,
   since they state the answers (Finding 2). Rejected: scale `m` (500 runs), because event-file export
   and copies per session grow 100× for little extra signal.
5. **Baseline files** (assumed): `config.json` (nested as logged), `metrics.csv` (`step`, `time`, then
   sorted metric keys; empty cell where not logged; `nan`/`inf` as written by Python), `output.log`. No
   status file: hand-rolled logging rarely has one, and the output's last line tells (`done`, a
   traceback, `JOB CANCELLED`). TensorBoard gets the Lightning layout: event files with one scalar per
   metric (step, wall time), the hparams plugin summary, `hparams.yaml`, and `output.log`.
6. **Truth from data, not literals** (assumed): computed per seed from the plain-files export, with
   status from `_run.json`; "completed" means status `finished`. A test checks it against Beamtime's
   own query path for seed 7. Truth and tasks tell only finished from not finished: no truth value
   and no graded check distinguishes running, lost and killed (Beamtime calls a run lost after 300 s,
   so setups would disagree on the synthetic "lost" and "running" runs).
7. **Answers as JSON** (assumed): every prompt ends with the same kind of answer line; grading parses
   the last fenced `json` block. A missing or malformed block scores 0 on its checks. Rejected: regexes
   over prose, which fail across seeds (Finding 5) and across setups' wording.
8. **One model, recorded** (assumed): `--model sonnet`, resolved at batch start from the first init
   event and then pinned as the full id (`claude-sonnet-5-5` in the last batch) for every session and
   the chart judge; `modelUsage` keys are stored and a session using another model is flagged.
9. **96 sessions per run** (assumed): 8 tasks × 4 setups × 3 seeds, one session each; `--reps` exists
   but defaults to 1; parallel 3 with the job order shuffled by a fixed seed, so contention hits all
   setups alike.
10. **No leaks** (assumed): projects live under `$BT_COMPARE_ROOT` (default
    `$TMPDIR/bt-compare/<stamp>/`), outside the repo; truth is computed after the sessions; a session
    whose tool inputs name the repo path, `synth/` or `generate.py` is flagged `leak` and left out of
    the figures (kept in the table).
11. **Measures** (from the brief): input, cache-write, cache-read and output tokens; total; cost (USD,
    from the result); wall seconds (harness) and API ms; turns; tool calls by name and errors; score in
    [0, 1] and `correct`; timeouts score 0 and keep the tokens summed from the assistant messages.
12. **Figures** (assumed shape): (a) single column 3.3 × 2.5 in: x total tokens per session (log;
    geometric mean over tasks), y mean score, one point per setup, error bars min–max over the three
    seeds; (b) double column 6.9 × 2.5 in: per task, one point per setup (median over seeds, min–max
    bars), log seconds. `.pdf` for docs and papers, `.svg` for the README and the site (GitHub cannot
    show a PDF). Only tasks run in every setup enter the figures; all eight are.
13. **Docs** (from the brief): `docs/guides/benchmark.md` (method, fairness rules, tasks, table,
    figures) in `docs/nav.json` under Guides; the README gets a short section with figure (a) and a link.
14. **`find-runs` threshold 0.922** (review of M74): at 0.925 seed 8 has a run at 0.92489, which
    `beamtime runs` prints as `0.925` (three digits), so the CLI setup would be graded wrong for
    reading its own table. At 0.922 every seed's nearest run is at least 9.7e-4 away (0.926: 6.3e-4).
15. **`table` values at full precision** (review of J71): the prompt asks for every number at full
    precision, as logged, and the check keeps 1e-6; printed tables round to three digits, and the
    same stated requirement then holds for every setup.

## N. Harness repair

### N71. Restore the rules block in run.py (sonnet) — reproduced — **done**

- **Touches:** `bench/agents/run.py` (`project` 106–139: the import 113, `instructions(...)` 128, the
  `--guide` override 129–130), new `tests/bench/__init__.py`, new `tests/bench/test_harness.py`.
- **Read:** `src/beamtime/guide/rules.py` (`START`, `END` 11, `render` 31–49, `write_block` 163–182);
  `src/beamtime/ops/admin.py` `write_rules` 694–714.
- **Check:** `uv run python -c "import sys; sys.path.insert(0,'bench/agents'); import run, tempfile,
  pathlib; t=run.Task.load(pathlib.Path('bench/agents/tasks/analysis-best-lr.yaml')); f=pathlib.Path(tempfile.mkdtemp());
  root,_=run.project(t,f,None); print('beamtime:start' in (root/'CLAUDE.md').read_text())"` prints
  `True` (today: the ImportError of Finding 1); `uv run pytest -q tests/bench/test_harness.py` (new).
- **Done:** `project` writes CLAUDE.md with the marked block from `render(ctx.settings.agent,
  user_only)`; `--guide` with `instructions.md` still replaces the block's text.
- **Risks:** settings not found because `beamtime.yaml` is written after the context is made → write it
  first (`test_project_writes_rules`); the user-only list drifting from `admin.write_rules` → build it
  the same way (`sorted(o.name for o in OPS if o.user_only)`).
- **Stop if:** the rules need a client (`setup.agents.client_named`) to render; then call
  `rules_change(client_named("claude"), ...)` instead and say so.

1. Replace the import with `from beamtime.guide.rules import END, START, render, write_block`,
   `from beamtime.ops.context import Context`, `from beamtime.ops.registry import OPS`.
2. After `beamtime.yaml` is written: `ctx = Context.make(root=root)`;
   `write_block(root / "CLAUDE.md", render(ctx.settings.agent, sorted(o.name for o in OPS if o.user_only)))`.
3. New `tests/bench/__init__.py`, `tests/bench/test_harness.py` (new): `test_project_writes_rules` (tmp
   folder, no agent) and `test_guide_override_replaces_block`.

## M. Data and exporters

### M71. Bench log dirs without answers (sonnet + review) — code — **done**

- **Touches:** new `bench/agents/compare/data.py`, new `tests/bench/test_compare_data.py`.
- **Read:** `src/beamtime/synth/generate.py` (`generate` 839–877, `record` 194–272, `write_run`
  722–810); `src/beamtime/format/io.py` `write_replaced` 50; `src/beamtime/format/tree.py` `iter_runs` 32.
- **Check:** `uv run pytest -q tests/bench/test_compare_data.py`.
- **Done:** for seeds 7, 8, 9 the log dir has 47 runs in five groups, no `_synth.json`, no `proposal/`,
  `notes/` or `memory/` anywhere, every `_run.json` has `proposals == {}`; `beamtime runs` and the
  index read it without errors; a second call with the same seed is byte-identical in metrics.
- **Risks:** `os.utime` heartbeats lost by the rewrite of `_run.json` → the lost run reads as running
  forever; restore the mtime after rewriting (`test_heartbeats_survive`); a reader that needs the
  proposal hashes (`test_index_reads_stripped_logdir` through `beamtime.query.run`).
- **Stop if:** stripping needs a change in `src/beamtime/` (Decision: no product change).

1. `make_logdir(dest: Path, *, seed: int, now: datetime) -> Manifest`: `generate(dest / "beamtime",
   seed=seed, now=now)`, then `strip_record(dest / "beamtime")`; returns the manifest (roles are kept in
   memory for grading, never written into `dest`).
2. `strip_record(logdir: Path) -> None`: delete `_synth.json`; `shutil.rmtree` every directory named
   `proposal`, `notes`, `memory` that is not inside a run; for each run rewrite `_run.json` with
   `proposals={}`, `proposal_hashes={}` by `write_replaced`, keeping its `st_mtime` (`os.utime`).
3. Tests above plus `test_no_answers_left`: grep the tree for `3e-4 gives`, `verdict`, `unigram beats`.

### M72. The plain-files export (sonnet) — code — **done**

- **Touches:** new `bench/agents/compare/formats.py` (`ExportRun`, `export_runs`, `export_files`), new
  `tests/bench/test_compare_formats.py`.
- **Read:** `src/beamtime/format/run.py` (`read_run_info` 52, `read_config` 117, `read_output` 371,
  `read_effective_metrics` 405); Decision 5.
- **Check:** `uv run pytest -q tests/bench/test_compare_formats.py -k files`.
- **Done:** `runs/<group>/<run id>/` per run with the three files; the CSV round-trips every logged
  value of seed 7 (NaN and inf included); the resumed run has one row per step; `config.json` equals
  `_config.json` without `schema`.
- **Risks:** NaN/inf as strings in `_metrics.jsonl` turned into text → parse back with `float`
  (`test_nonfinite_roundtrip`); sparse egnn keys (`validation/*` every 50 steps) shifted to the wrong
  rows (`test_sparse_columns`); the reserved `_step`/`_t` keys leaking as columns (`test_csv_header`).

1. `@dataclass(kw_only=True) ExportRun`: `group: str`, `id: str`, `config: dict`, `rows: list[dict]`,
   `output: str`, `status: str`.
2. `export_runs(logdir) -> Iterator[ExportRun]` over `iter_runs(logdir)`, rows from
   `read_effective_metrics`, the shared reader of M72 and M73.
3. `export_files(logdir: Path, dest: Path) -> int` writes `dest/runs/...`; header `step,time,<sorted
   keys>`; returns the number of runs.

### M73. The TensorBoard export (sonnet + review) — code — **done**

- **Touches:** `bench/agents/compare/formats.py` (new `export_tensorboard`),
  `tests/bench/test_compare_formats.py` (TensorBoard tests, `importorskip`).
- **Read:** Decision 5; the M72 code; "Not verified" (TensorBoard API).
- **Check:** `uv run --with tensorboard pytest -q tests/bench/test_compare_formats.py -k tensorboard`.
- **Done:** `tb/<group>/<run id>/` per run; `EventAccumulator` reads back every scalar of seed 7 with
  its step and wall time (NaN stays NaN); the hparams plugin lists the flattened config;
  `hparams.yaml` holds the nested config; `output.log` beside.
- **Risks:** `hparams_pb` needing TensorFlow (`test_hparams_without_tf`); nested config values (dicts)
  rejected by hparams → flatten with `.` (`test_nested_hparams`); float32 rounding of `simple_value`
  making truth differ by setup → truth tolerances (M74) cover 1e-6 relative (`test_float32_close`).
- **Stop if:** event files cannot be written without TensorFlow or PyTorch (it worked with
  tensorboard 2.21.0; see Not verified); report which package works.

1. `export_tensorboard(logdir: Path, dest: Path) -> int`, imports tensorboard inside the function:
   `EventFileWriter` from `tensorboard.summary.writer.event_file_writer`, `Event`/`Summary` protos from
   `tensorboard.compat.proto`, `hparams_pb` from `tensorboard.plugins.hparams.summary_v2`.
2. One event per (row, metric) with `step=_step`, `wall_time=_t`; one hparams event at the first time.

### M74. Truth from the exported numbers (sonnet + review) — reproduced — **done**

- **Touches:** new `bench/agents/compare/truth.py`, new `tests/bench/test_compare_truth.py`.
- **Read:** J71's task table (below) for what each task needs; `src/beamtime/record/stats.py`
  (`welch_interval` 161, `mean_interval` 147); Findings 3, 4.
- **Check:** `uv run pytest -q tests/bench/test_compare_truth.py`.
- **Done:** `compute(files_root: Path, logdir: Path) -> dict[str, dict]` gives every task's expected
  values; seed 7: best 3e-4, runner-up 1e-3, not significant; seed 9 significant; best arm `large`;
  `fastest-to-threshold` 3e-3; the failing runs are the `diverging` and `killed` roles.
- **Risks:** counting unfinished runs (`test_completed_only`: 3e-4 stays best); the last eval vs the last
  row (`test_final_is_last_logged_value`); disagreement with Beamtime's own numbers
  (`test_matches_beamtime_query`: `beamtime.query.run` means per lr equal to 1e-9).

One function per task id (names in J71), each pure Python over `runs/*/*/metrics.csv` and
`config.json`; status comes from `_run.json` of the same run id. Significance uses `welch_interval` at
0.95 (Beamtime's own t-interval, pure Python); the test pins seed 7's interval
(difference 0.0079, CI [-0.0002, 0.0160]) and seed 9's (0.0066, [0.0011, 0.0122]).

## J. Tasks, setups and sessions

### J71. Eight tasks and the grader (sonnet + review) — code — **done**

- **Touches:** new `bench/agents/compare/tasks/*.yaml` (8), new `bench/agents/compare/grade.py`
  (`Task`, `load_tasks`, `answer_json`, `grade`), new `tests/bench/test_compare_grade.py`.
- **Read:** `bench/agents/score.py` `score_analysis` 210–229 (what it does today); Decisions 6, 7, 10.
- **Check:** `uv run pytest -q tests/bench/test_compare_grade.py`.
- **Done:** each task grades a hand-written correct answer 1.0, a typical wrong one (killed run counted,
  wrong lr, missing block) below 1; no prompt names Beamtime, TensorBoard, CSV or a file layout.
- **Risks:** lr written as `0.0003` vs `3e-4` → compare as floats with 1e-9 relative
  (`test_lr_forms`); run ids with a group prefix → match the trailing id (`test_id_forms`); several json
  blocks → the last wins (`test_last_block`).

| id | prompt (gist) | answer keys | checks | limit |
|---|---|---|---|---|
| `best-config` | best lr in scaling/lr-sweep by final val/acc over the seeds of completed runs; is the lead over the runner-up significant (95 %)? | `best_lr`, `runner_up_lr`, `difference`, `significant` | equal, equal, close 20 %, equal | 300 s |
| `failures` | which runs in scaling/lr-sweep did not complete, and why each stopped | `runs: [{id, cause}]` | id set equal; cause matches `diverg\|nan\|inf\|FloatingPoint` or `kill\|SIGTERM\|cancel` | 300 s |
| `sweep-summary` | summarize realistic/egnn-bench: mean final validation/w1_energy per arm over completed runs, the best arm, runs to leave out | `per_arm`, `best_arm`, `exclude` | close 1 % each, equal, set equal | 400 s |
| `check-prediction` | "unigram lowers final val/ppl vs BPE by more than 0.1" in tokenizer/bpe-vs-unigram: supported at 95 %? | `verdict`, `effect`, `ci` | equal (`confirmed`), close 0.05 abs, contains truth effect | 300 s |
| `chart` | figure of final val/acc vs lr for scaling/lr-sweep, one point per completed run, log x, as a PNG | `file` | exists and is PNG; judged (J72) | 600 s |
| `find-runs` | every run in the project whose last val/acc is at least 0.922 | `runs: [id]` | F1 = 1 for correct; score F1 | 400 s |
| `fastest` | which lr in scaling/lr-sweep first reaches val/acc 0.85 (mean step over seeds of completed runs) | `lr`, `step` | equal, close 10 % | 400 s |
| `table` | CSV of every run of scaling/lr-sweep: run id, lr, seed, status, final val/acc; say where | `file` | file in the project; 17 rows; values close 1e-6; status words map to finished/failed/killed | 300 s |

1. `Task` (keyword-only dataclass): `id`, `prompt`, `answer` (the json shape shown to the agent),
   `checks: dict[str, dict]` (`kind`: `equal | close | set | f1 | contains | file`), `time_limit_s`,
   `setups: list[str]` (default all four), `judge: list[str]` (J72).
2. `answer_json(text) -> dict | None`; `grade(task, text, truth, project) -> Grade` with `score` the
   share of checks passed and `correct = score == 1`.

### J72. Chart grading with the judge (sonnet) — code — **done**

- **Touches:** `bench/agents/compare/grade.py` (`judge_chart`), `bench/agents/compare/tasks/chart.yaml` (`judge` list),
  `tests/bench/test_compare_grade.py` (stubbed `ask`).
- **Read:** `bench/agents/score.py` `judge_checklist` 446–481, `ask` 483–530.
- **Check:** `uv run pytest -q tests/bench/test_compare_grade.py -k chart`.
- **Done:** a PNG is judged on five items (scatter of val/acc vs lr; log x; about 15 points with the
  failed and killed runs left out; peak at 3e-4 readable; labelled axes) through `score.ask` with the
  pinned model; items count as checks; a usage-limit answer leaves the session ungraded.
- **Risks:** a PDF or SVG instead of a PNG → convert nothing, score `file` 0 (`test_not_png`); the judge
  seeing the project → run it in a copy holding only the image (`test_judge_sees_only_image`).

### J73. Setups: projects, instructions, tools, environments (sonnet + review) — code — **done**

- **Touches:** new `bench/agents/compare/setups.py`, new `tests/bench/test_compare_setups.py`.
- **Read:** `bench/agents/run.py` `project` 106–139 (after N71); Decisions 1, 2, 5, 10.
- **Check:** `uv run pytest -q tests/bench/test_compare_setups.py`.
- **Done:** `prepare(setup, session_dir, data_dir, env) -> Project` gives for each setup a project with
  its data, CLAUDE.md (same preamble byte for byte; only the `## Data` section differs), the tool list,
  the MCP config (`mcp` only) and a PATH; `make_envs(root)` builds two venvs with `uv venv` +
  `uv pip install`: `base` (numpy, pandas, scipy, matplotlib, tensorboard) and `beamtime` (the same plus
  this checkout's `beamtime[serve]`); the index of a Beamtime project is warmed before the session.
- **Risks:** `beamtime` reachable from the `files` setup through the PATH (`test_files_path_has_no_beamtime`);
  the user's skills or settings leaking in → `--setting-sources project --disable-slash-commands`
  (`test_command_flags`); `BEAMTIME_CACHE` shared between sessions (`test_cache_per_session`).

1. `SETUPS: dict[str, Setup]`; `Setup` has `name`, `data` (`beamtime | files | tensorboard`),
   `mcp: bool`, `env` (`base | beamtime`), `section: str` (the CLAUDE.md text).
2. Preamble (identical): the project holds results of numerical experiments; answer from the data; work
   on your own, don't ask back; Python with numpy, pandas, scipy and matplotlib is on the PATH.
3. Sections: `mcp`/`cli` the rendered rules block (N71's way); `files`/`tensorboard` the layout of
   Decision 5 in four lines each.

### J74. The session runner and its records (sonnet + review) — code

- **Touches:** new `bench/agents/compare/sessions.py`, `bench/agents/README.md` (a "Comparison"
  section), new `tests/bench/test_compare_sessions.py`.
- **Read:** `bench/agents/run.py` `run_one` 142–206 and `summary` 209–255; Decisions 8–11.
- **Check:** `uv run pytest -q tests/bench/test_compare_sessions.py`;
  `uv run python bench/agents/compare/sessions.py --dry-run` prints 96 sessions.
- **Done:** `sessions.py [--setups ...] [--tasks ...] [--seeds 7 8 9] [--reps 1] [--parallel 3]
  [--dry-run] [--grade-only <batch>]` builds data once per seed, runs every session with its time
  limit, grades, and writes `bench/agents/runs/compare-<stamp>/<task>-<setup>-<seed>-<rep>/` with
  `record.json`, `grade.json`, `transcript.jsonl`, the answer file (chart, table); projects are deleted
  after grading unless `--keep`.
- **Risks:** a timeout without a result event → tokens from the assistant messages, deduplicated by
  message id (`test_timeout_tokens`); a second model in `modelUsage` (`test_flags_other_model`); leak
  detection on tool inputs (`test_leak_flag`).

Record fields: `task`, `setup`, `seed`, `rep`, `model` (init event), `models` (`modelUsage` keys),
`claude_version`, `status` (`ok | timeout | error`), `seconds`, `api_ms`, `turns`, `tokens`
(`input`, `cache_write`, `cache_read`, `output`, `total`), `cost_usd`, `tools` (counts by name),
`tool_errors`, `beamtime_calls` (MCP tools or `beamtime` in Bash), `leak`, `answer` (last 4000 chars).

## L. Results

### L71. Report table and figures (sonnet) — code

- **Touches:** new `bench/agents/compare/tables.py`, new `bench/agents/compare/figures.py`, new
  `tests/bench/test_compare_report.py` (fixture records, no agents).
- **Read:** CLAUDE.md § Visualization; Decisions 10–12.
- **Check:** `uv run pytest -q tests/bench/test_compare_report.py`.
- **Done:** `tables.py <batch> [--out docs/guides/benchmark]` writes `results.md` (per task × setup:
  n, score mean, correct k/n, median and min–max of total tokens, uncached tokens, cost, seconds,
  turns, tool calls; then per setup over all tasks; model id, Claude Code version, date, seeds) and the
  four figure files; leaked sessions are listed and left out of the figures.
- **Risks:** a setup with a missing task in the figures → refuse and say which (`test_incomplete_batch`);
  LaTeX missing → `["science", "nature", "no-latex"]` (`test_no_latex_fallback`); rc overrides creeping
  in (`test_no_rc_overrides`: the module never touches `rcParams` or `fontsize`/`linewidth` keywords).

### L72. Pilot and full run (sonnet) — user starts

- **Touches:** new `docs/guides/benchmark/results.md` and the four figure files (from L71), `bench/agents/compare/tasks/*.yaml` only
  if the pilot shows a broken task.
- **Check:** `uv run python bench/agents/compare/sessions.py --seeds 7` (pilot, 32 sessions), then the
  full command; `uv run python bench/agents/compare/tables.py bench/agents/runs/compare-<stamp>`.
- **Done:** 96 graded sessions on one model; no leaked session; the figures and table are committed.
- **Stop if:** the user hasn't said to start it (it costs about $30 at list price, notes.md), or the
  pilot shows a task that a careful human would answer differently from the truth; fix the task first.

## U. Docs

### U71. The method page (sonnet) — code

- **Touches:** new `docs/guides/benchmark.md`, `docs/nav.json` (Guides, last), the figure files in
  new `docs/guides/benchmark/` (from L71).
- **Read:** `web/docs.mjs` `figure` 100–118 (images, light/dark variants, broken links);
  `docs/guides/agents.md` for tone; Decisions 1–13.
- **Check:** `cd web && npm run docs`; `uv run pytest -q tests/test_docs.py`.
- **Done:** the page states the question, the four setups, the data and its planted effects, the eight
  tasks (linking `bench/agents/compare/tasks/` on GitHub), the fairness rules, the measures, the model
  and date, the table and both figures, how to rerun, and the limits (one model, synthetic data, one
  author's tasks); the site builds without broken links.
- **Risks:** a link to the `.pdf` counted as broken by `docs.mjs` → link it by GitHub URL; the table
  pasted by hand drifting from `results.md` → include it verbatim from L71's output.

### U72. The README section (haiku) — code

- **Touches:** `README.md` (a "Benchmark" section after the quickstart block, before Documentation).
- **Read:** `README.md` 1–45; `docs/guides/benchmark.md`.
- **Check:** `uv run pytest -q tests/test_docs.py`; the image URL answers in a browser after push.
- **Done:** three to five lines: what was measured, the one-line result in numbers from `results.md`,
  figure (a) as `<img>` from the raw.githubusercontent.com URL of the guide's `tokens-vs-score.svg`
  (the README's existing pattern), and a link to the guide.

## Breaking changes

None: new files in `bench/agents/compare/`, `tests/bench/`, `docs/guides/`; `run.py` gets its rules
block back.

## Not verified

- Checked (reproduced, tensorboard 2.21.0 in a scratch env without TensorFlow): `EventFileWriter`
  writes scalars, `summary_v2.hparams_pb` builds the hparams summary, and `EventAccumulator` reads back
  `[(0, 1.0), (1, 0.5), (2, nan)]`. Not checked: that the hparams plugin lists nested keys as flattened.
- W&B has no offline read path (Decision 3) is from knowledge of its offline mode and server, not run.
- `--disable-slash-commands` with `--setting-sources project` keeps the user's skills and plugins out of
  the sessions; J73 checks the init event's tool and skill lists.
- Token and time estimates for the baselines (notes.md) are guesses from the Beamtime batch; the pilot
  in L72 replaces them.
- The `cli` setup's agent finds the CLI from the rules block alone (`beamtime guide`, `--help`); the
  pilot shows it.
