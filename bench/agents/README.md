# Agent tasks: how well agents use Beamtime

The harness gives agents tasks in a researcher's words ("show which learning rate works best",
"I want to test whether ..."), lets them work with Beamtime's MCP tools, and scores what they leave in
the log dir. It guards the guide, the tools, the kit and the built-in blocks: run the smoke set after
changing any of them, and the full set before a release. The spec is in `docs/design/05-views.md`,
"Evaluation harness".

## Run it

Needs Claude Code (`claude`, logged in), the `serve` extra and a Chromium for the screenshots.

```sh
uv run python bench/agents/run.py --smoke                      # 15 tasks, Sonnet and Haiku, once each
uv run python bench/agents/run.py --tasks analysis-best-lr     # one task
uv run python bench/agents/run.py --kinds notes verdict --reps 3
uv run python bench/agents/run.py --heldout --reps 3           # the held-out third, once per release
uv run python bench/agents/run.py --guide /tmp/guide           # parts of the guide read from a directory
uv run python bench/agents/score.py bench/agents/runs/<stamp>  # score again (only unscored runs)
uv run python bench/agents/score.py bench/agents/runs/<stamp> --rescore  # also redo errored and stalled scores
uv run python bench/agents/report.py bench/agents/runs/<stamp> # write RESULTS.md again
uv run python bench/agents/report.py --base <stamp> --new <stamp>  # per-task deltas
uv run python bench/agents/mine.py                             # tool counts and errors of real sessions
```

`--guide <dir>` replaces the guide parts that have a file of the same name in `<dir>` (`index.md`,
`views.md`, `notes.md`, ..., and `instructions.md` for the agent rules in CLAUDE.md), so a text can
be tested without a release. The examples and the block catalogue are always the shipped ones.
The MCP setup runs the default `mcp_tools: core` surface: 19 tools are listed and the others are called through `tools_more`, so a record names those calls `mcp__beamtime__tools_more`.

Runs go to `bench/agents/runs/<stamp>/` (not committed): per run the project with its generated log
dir, the agent's transcript (`transcript.jsonl`), `record.json` (tool calls with errors, rounds,
tokens, time), `score.json`, for views the page's screenshot, and the batch's `RESULTS.md`. Agent runs
use your Claude subscription.

**What a run costs.** One run is one agent session; a view run adds two judge calls (finding,
checklist). 29 tasks (19 refinement, 10 held out) × 2 models × 3 reps is 174 agent runs and about 96
judge calls; the smoke set with one rep is 30 agent runs. Start nothing larger than a smoke run
without knowing which of these you are paying for.

## Tasks

`tasks/<id>.yaml`, with a `kind`: `proposal`, `verdict`, `notes`, `view` (the default), `analysis`,
`lifecycle`. Common fields:

```yaml
kind: analysis
smoke: true                      # part of the set run on every change
heldout: true                    # not looked at while refining (see below)
page: scaling/lr-sweep           # the group the work happens in; run:<role> for a generated run
prompt: >                        # in a researcher's words; {run:<role>} becomes that run's id
  Which learning rate in scaling/lr-sweep gives the best final val/acc?
facts: ...                       # the truth, by kind
```

| Kind | Facts | Correct when |
|---|---|---|
| `proposal` | `metrics`, `test`, `plan`, `window` | a new proposal has falsifiable predictions (operator and a value, reference or margin) on the metric, with the test, a plan and a window where asked |
| `verdict` | `verdicts`, `overall`, `overclaims` | a new verdict note matches the planted truth per prediction, cites evidence and matches none of the overclaim patterns |
| `notes` | `type`, `supersedes` | exactly one new note of the type; a correction supersedes the note it names |
| `view` | `metrics`, `runs`, `finding`, `overclaims`, `checklist` | saved, valid, its queries ask for the metrics and select the runs, and the finding is judged true |
| `analysis` | `answer`, `overclaims`, `tools` | the answer matches every pattern and no overclaim, a listed tool was used, no raw file was read |
| `lifecycle` | `tool`, `run`, `dest` | the tool succeeded on the run (and the copy exists; for `resume`, the answer names the run) |

A view task with `remote: box` also generates a second log dir that the project reaches as the remote
`box` over the command transport; the agent works on `@box/<group>`, and the saved view is scored on
the remote's log dir. `run.py` writes the project's `beamtime.yaml` with `yaml.safe_dump`, which the
settings reader must parse for `@box` to resolve (a JSON line appended to a YAML mapping did not, and
every first-baseline `view-remote` run failed on it).

The log dirs come from `beamtime.synth` (seed 7), whose planted effects are the truth: lr 3e-4 is
best in the sweep, unigram beats BPE by about 0.4 val/ppl, one run diverges at lr 1e-2, one is
killed, one resumed, one lost and one still running.

## Scores

Deterministic first; a model judges prose only (a view's finding and checklist).

| Score | How |
|---|---|
| correct | per kind, above |
| rounds | `view_validate` and `view_render` calls |
| tool errors | tool calls that failed |
| tokens, turns | from the transcript's result |
| violations | raw reads (Read, Grep or Glob of the log dir, `_*` files included), edits of the log dir, calls of user-only commands |
| views | also hand-drawn charts, live-capable blocks, axis labels and caption length (the validator's lints), the queries' coverage, the checklist and robustness on a single run, a subgroup and an empty group |

A judge that hits its usage limit leaves the run unscored (no `score.json`, the batch stops, a later
pass retries it); a malformed answer is still an `error` in the score. `--rescore` redoes the scores
whose finding or checklist is an error or whose checklist is all bare `no` with no reason, never a clean
one. The `tools` list of an analysis task credits any tool that can give the answer, `digest` included.

`report.py --base --new` compares two batches task by task and model by model. A delta from fewer
than three reps is marked; compare on Haiku and Sonnet.

## The loop

1. Run the tasks (`--reps 3` on both models) and keep the stamp.
2. Read each failure's transcript and classify it, in this order: **product** (a tool or field that
   should have worked), **validator** (a check that missed or misled), **error message** (it didn't
   say what to do), **guide** (the text didn't say it), **task** (the task was unfair or wrong).
3. Fix the earliest class that applies: a product bug is no guide paragraph, a better message beats a
   rule in the guide.
4. Add the failure to `MISTAKES.md` with its class and its fix.
5. Rerun (`--guide <dir>` while the text is a draft) and compare with `report.py --base --new`.

The held-out tasks (`heldout: true`, a third of them) are not read during refinement and run only
with `--heldout`; that keeps the guide from fitting the tasks. `mine.py` seeds new tasks from real
sessions: the most common errors and raw reads there become tasks before they become rules.

## The comparison benchmark

`compare/` runs the same researcher tasks over the same synthetic numbers in several setups (Beamtime
over MCP and the CLI, plain files, TensorBoard event files); see the plan in
`docs/plans/v0.3/benchmark/benchmark-plan.md`. Built so far:

- `compare/data.py`: `make_logdir(dest, seed=, now=)` writes a scale `s` log dir (47 runs, five groups)
  at `dest/beamtime` and strips what states the answers: `_synth.json`, every `proposal/`, `notes/` and
  `memory/` folder outside runs, and `proposals`/`proposal_hashes` in each `_run.json` (its mtime, the
  heartbeat, is kept). The manifest's roles are returned, never written. Seeds 7, 8 and 9.
- `compare/data.py`: `make_logdir(dest, seed=, now=)` writes the synth's scale `s` through
  `BenchGenerator` (a subclass of the synth's `Generator`) with the messier data of Decision 17 planted
  on top, each planted run from a random stream of its own: an early run of lr 1e-3 seed 1 in
  `scaling/lr-sweep` that a later run supersedes (final accuracy 0.975); a second batch
  `scaling/lr-sweep-2` (seeds 3 and 4 per lr) that logs `val/accuracy` every 100 steps instead of
  `val/acc` every 50, and reruns the killed lr 3e-4 seed 3; an out-of-memory crash in it (lr 3e-3 seed 4)
  rerun to completion; a tokenizer seed 3 whose unigram run was killed (no pair); an egnn `large` arm
  whose validation/loss rises late (overfitting) and a NaN validation/loss at step 300 of one `small`
  run. Then `strip_record` deletes the manifest and the research record. 61 runs in six groups; the
  manifest's roles (`superseded`, `killed_rerun`, `oom`, `oom_rerun`, `unpaired`, `unpaired_killed`,
  `nan_loss`, the synth's own) stay in memory for tests.
- `compare/formats.py`: `export_runs(logdir)` reads every run once (group, run id = folder name, config,
  effective metrics with resumed attempts resolved, output, status); `export_files(logdir, dest)` writes
  the plain-files baseline `dest/runs/<group>/<run id>/{config.json, metrics.csv, output.log}`. The CSV
  has `step`, `time` and the sorted metric keys; a metric not logged at a step is an empty cell, `nan`
  and `inf` are written as Python writes them, and there is no status file.
  `export_tensorboard(logdir, dest)` writes the TensorBoard baseline `dest/tb/<group>/<run id>/{events,
  hparams.yaml, output.log}`: one scalar event per logged value (step and wall time as logged; the
  value is float32, within 1e-6 relative) and an hparams event with the config flattened by `.` (lists
  and `None` as JSON text), while `hparams.yaml` keeps it nested. It needs `tensorboard` only, no
  TensorFlow or PyTorch, so tests run under `uv run --with tensorboard` and skip without it.
- `compare/truth.py`: `compute(files_root, logdir)` gives every task's expected values (`best-config`,
  `failures`, `sweep-summary`, `check-prediction`, `chart`, `find-runs`, `fastest`, `table`) in pure
  Python from the plain-files export, so it is computed per seed at grading time and never written into
  a session's reach. Only finished runs enter a mean (`_run.json` status `finished`); the final value is
  the last logged value of a metric, and validation accuracy is `val/acc` or `val/accuracy`. The sweep
  tasks read both batches and count the most recent run of each lr and seed (run ids start with the
  start time), if it finished. `sweep-summary` reads validation/w1_energy at each run's lowest finite
  validation/loss; `check-prediction` pairs the tokenizers by seed (`paired_interval`, threshold 0.2);
  `fastest` asks for 0.9, where an lr qualifies only if all its counted runs reach it. The intervals
  are Beamtime's own `welch_interval` and `paired_interval` at 95 %. Truth
  and graded checks tell finished from not finished only: running, lost and killed runs are alike.
- `compare/tasks/<id>.yaml` and `compare/grade.py`: the eight tasks (`best-config`, `failures`,
  `sweep-summary`, `check-prediction`, `chart`, `find-runs`, `fastest`, `table`). A file holds the
  question (`prompt`), the answer shape shown to the agent (`answer`), the `checks` and `time_limit_s`;
  `setups` (default all four) and `judge` (J72) are optional. `load_tasks()` appends "End your reply
  with a fenced json block: {answer}" to every prompt, and no prompt names a product or a file layout.
  `grade(task, text, truth[task.id], project)` takes the last fenced json block (none or a malformed
  last one scores 0), runs each check and returns `Grade(score, correct, checks)`: the score is the
  mean of the checks, `correct` means all passed. Check kinds: `equal` (numbers as floats, 1e-9
  relative, so `0.0003` is `3e-4`), `close` (`rel`, `abs`; a dict key by key), `set` and `f1` (run ids,
  also `{id: ...}`, matched on the trailing path part, so `group/id` is `id`), `contains` (the interval
  holds the true effect; no shipped task uses it now), `interval` (both bounds within `abs`, in either
  order), `cause` (each stopped run's cause matches the wording of its true cause:
  diverged is `diverg`, `nan`, `inf`, `FloatingPoint`; oom is `memory`, `oom`; killed is `kill`,
  `SIGTERM`, `cancel`; `failed` alone is no cause), `rerun` (each stopped run names its completed rerun
  in any id form, or null, `""` or `none` when there is none), `file` (a PNG or a table, inside
  `project`), `keyed` (a list of objects, or a dict of key to object, scored per key: `key` names the
  object, `field` the compared value, `answer` the answer key to read when it is not the check's name
  (several keyed checks on one list), with `abs`/`rel` as `close` and without as `equal`; the score is
  the keys right over the larger of the given and the expected keys, a key given twice counts once and
  a key without the field is wrong), and for the table task `table_ids` (29 rows), `table_values` (lr, seed, val_acc within
  1e-6; the prompt asks for full precision) and `table_flag` (yes/no in the `finished` and the
  `superseded` column; running, lost and killed are not told apart). Tolerances (Decision 17):
  `difference` 5 %, `per_arm` 0.2 %, `effect` 0.002 and the interval's bounds 0.005 absolute, `fastest`'s
  step 1 %; the prompts that compute ask for the values at full precision. `find-runs` compares at
  exactly 0.922 without tolerance.
  The `chart` task's `judge` list holds seven statements (points of the final accuracy against lr, a
  line through the means, log x, no points for the failed and killed runs, every point below about 0.95
  (the superseded run left out), the peak at 3e-4 readable, labelled axes; no count, since overlapping
  points can't be counted); each becomes a check `judge1`..`judge7` next to `file`, answered by `score.ask` with the pinned model
  (`grade(..., model=)`) from the PNG alone, run in a fresh folder holding only a copy of the image
  (`Grade.notes` keeps the judge's reasons). A file that is not a PNG (PDF, SVG) scores 0 on `file` and
  all items without a judge call; a usage-limit answer raises `score.JudgeStalled`, so the session
  stays ungraded.
- `compare/setups.py`: `SETUPS` (`mcp`, `cli`, `files`, `tensorboard`) and `prepare(setup, session_dir,
  data_dir, envs)`, which builds a session's project in `session_dir/proj` and returns a `Project`: the
  data (a copy of the log dir plus `beamtime.yaml` for `mcp` and `cli`, `runs/` for `files`, `tb/` for
  `tensorboard`, exported by the `beamtime` environment since it has tensorboard), a CLAUDE.md that is
  the same preamble byte for byte plus a `## Data` section (Beamtime's rules block as shipped, with
  default agent settings, or four lines on the files), the tool list (`Bash,Read,Write,Edit,Glob,Grep`
  everywhere, plus `mcp__beamtime__*` allowed for `mcp`), the MCP config (`mcp` only), and the session's
  environment: a PATH that starts with the setup's venv and drops every host folder holding a `beamtime`,
  its own `BEAMTIME_CACHE` and `XDG_CONFIG_HOME` inside the session folder. `Project.flags` are the
  `claude` flags (`--tools`, `--allowedTools`, `--strict-mcp-config`, `--mcp-config` for `mcp`,
  `--setting-sources project`, `--disable-slash-commands`, `--no-session-persistence`); the session
  adds the prompt, model and output format. Only `cli` has `beamtime` on the PATH; `mcp` reaches the
  server through the absolute command in its MCP config. A Beamtime project's index is warmed with
  `beamtime runs` before the session. `make_envs(root)` builds the two venvs with `uv venv` and
  `uv pip install` (`base`: numpy, pandas, scipy, matplotlib, tensorboard, pyyaml; `beamtime`: the same plus this
  checkout's `beamtime[serve]`) and keeps venvs whose install finished (marked by `.installed`).
- Data sets: a task names its `data` (default `s`); `data.DATASETS` maps a name to its builder and
  `truth.TRUTHS` to its truth function. `sessions.py` builds only the data sets the chosen tasks use, once
  per seed, in `root/data/<seed>` for `s` and `root/data-<name>/<seed>` otherwise, and computes the truth
  per (data set, seed) from an export in `root/truth[-<name>]/<seed>`.
- The `wide` data set (`compare/wide.py`, `make_wide_logdir`; about 4 s and 100 MB per seed): `sweeps/s01` to
  `s20` hold 300 runs (15 each) whose config is drawn from a grid and whose final `val/loss` is 0.5 plus
  an effect per key (weight decay and lr large, batch size, dropout and model at most 0.02) plus noise of
  sd 0.02; 24 runs fail and 6 are killed at 30 to 90 % of the steps, and three of them last logged a
  `val/loss` below the fifth best finished run (role `traps`). The five best finished runs are at least
  0.002 apart (role `leaders`). `long/stability` has eight 100k-step runs: three diverge at distinct steps
  (loss grows by e every 500 steps, then NaN, then inf, `failed`; role `diverged`), one spikes to about 6
  times its running minimum for 200 steps (role `spike`), four are clean. `long/schedules` has four
  schedules x two seeds whose `val/loss` falls and then rises, with its minimum at a distinct evaluation
  step per run. Long runs log `train/loss` every step and `val/loss` every 500 steps and at the last step.
  `study/optimizer` has a proposal with four predictions on the last `val/loss` per optimizer (`sgd`, `adamw`,
  `lion`; `config.seed` 0 to 5; `adamw-converges`, `adamw-beats-sgd`, `lion-beats-adamw`, `sgd-under`), all
  18 runs recording it. The final losses are planted exactly (a mean per optimizer and half, plus offsets of
  -0.02, 0 and 0.02 over three seeds), so the check does not depend on the data seed. A verdict note
  (`overall: inconclusive`; its `check` field holds the check's numbers) and the project memory (one line per
  verdict) are written after the runs of seeds 0 to 2 and before those of seeds 3 to 5. With seeds 3 to 5
  counted, `lion-beats-adamw` goes from inconclusive to confirmed and `sgd-under` from confirmed to
  inconclusive; the other two stay confirmed. `formats.export_record` copies every `proposal/`, `notes/` and
  `memory/` folder outside runs to `record/<group>/…` (the project memory to `record/memory/`) in the files and
  TensorBoard exports, and only then do their CLAUDE.md sections name `record/`; the `s` data set has no
  record, so its exports and texts are as before.
- `compare/sessions.py`: `uv run python bench/agents/compare/sessions.py [--setups ...] [--tasks ...]
  [--seeds 7 8 9] [--reps 1] [--parallel 3] [--model sonnet] [--keep] [--dry-run] [--grade-only BATCH]`.
  `--dry-run` lists the 96 sessions (8 tasks x 4 setups x 3 seeds, in a fixed shuffled order) with their
  commands and builds nothing. A real run resolves the model alias to its full id with one probe
  session (the init event's `model`) and pins that id for every session and the chart judge, reads
  `claude --version`, builds the venvs (`make_envs`, per batch) and one log dir per seed, then runs the
  sessions (`claude -p ... --output-format stream-json --verbose`, cwd the project, its time limit, the
  `claude` found on the host PATH before a session's PATH drops folders; `claude` starts its own process
  group, killed when it exits or times out, so nothing it started outlives the session). The result
  event ends a session: the runner checks the transcript every 0.5 s and kills the group once the
  result is there, since `claude` otherwise waits on a Bash command the agent left in the background;
  `status` comes from the result (`ok`, or `error` for `is_error`) and `seconds` is the harness's wall
  time up to it. Only a session without a result by its limit is a `timeout`. Projects, data, venvs and the
  truth export live in `$BT_COMPARE_ROOT/<stamp>/` (default `$TMPDIR/bt-compare/<stamp>/`), outside the
  repo; a batch's records go to `bench/agents/runs/compare-<stamp>/<task>-<setup>-<seed>-<rep>/` with
  `record.json`, `grade.json`, `transcript.jsonl` and the file the answer names (`answer.png`,
  `answer.csv`), and `batch.json` (model, version, root, seeds). Grading runs after all sessions: truth
  per seed from the plain-files export, `grade.grade(...)` with the pinned model; a timeout, or an error with a result event (max turns),
  scores 0 (a timeout's tokens come from the assistant messages, each message once); the chart judge
  is asked a second time when its answer lacks a usable mark (`yes` as a bool, or yes/no/true/false)
  for an item, and when the second lacks one too the session stays ungraded with its project kept,
  marked `ungraded: judge failed` with the `judge_error`, counted in `batch.json`, and `--grade-only`
  tries again (never scored 0); a session that
  never started or crashed (an error without a result event) stays ungraded for good, marked
  `ungraded` in its record and counted in `batch.json`; one that ended on a usage limit, or whose
  judge stalls, stays ungraded with its project kept, and `--grade-only <batch>` grades
  it later. Sessions and the root are deleted after grading unless `--keep`.
  `record.json` holds `task`, `setup`, `seed`, `rep`, `model` (init event), `models` (`modelUsage` keys),
  `model_usage` (per model: tokens and cost), `other_model` (the init event names another model,
  or another model wrote more than 5 % of the output tokens), `claude_version`, `status` (`ok`, `timeout`, `error`),
  `seconds`, `api_ms`, `turns`, `tokens` (`input`, `cache_write`, `cache_read`, `output`, `total`),
  `cost_usd`, `tools` (counts by name), `tool_errors`, `beamtime_calls` (MCP tools or `beamtime` in
  Bash), `leak` (a tool input names the repo path, `synth/` or `generate.py`), `answer` (last 4000
  characters) and `stderr`; `grade.json` holds `score`, `correct`, `checks` and the judge's `notes`.
  The sessions' environment (setups.py) drops every `BEAMTIME_*` variable but `BEAMTIME_CACHE` and sets
  `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- `compare/tables.py` and `compare/figures.py`: `uv run python bench/agents/compare/tables.py
  bench/agents/runs/compare-<sonnet stamp> bench/agents/runs/compare-<haiku stamp>
  [--out docs/guides/benchmark]` takes one batch per model (Decision 18) and writes each into
  `<out>/<alias>/` (`sonnet/`, `haiku/`; the model id for a batch without an alias): `results.md`
  (model id, Claude Code version, date, seeds; per task and setup, then per setup over all tasks: n,
  then the cost (median with min-max of total tokens, uncached tokens (input, cache-write and output),
  cost, seconds, turns and tool calls), then mean score and correct k/n) and the figures `tokens-vs-score` (single column: geometric mean
  of tokens per session over tasks against mean score, one point per setup, bars over the seeds) and
  `time-per-task` (double column: median seconds per task, bars over the seeds) as `.pdf` and `.svg`.
  With two or more batches it also writes `<out>/models.md`, the per-setup table with one row per
  setup and model. Ungraded sessions (`crashed`, `not started`, `usage limit`, `judge failed`, not
  graded yet) are left out of every mean and counted; a session with `leak` is listed and left out of the figures only; one with `other_model` is
  listed. When a setup has no graded session without a leak for a task, nothing is written and the
  command names the missing `setup/task`. The figures use scienceplots as it is, with `no-latex` added
  when `latex` is not on the PATH. Tests: `tests/bench/test_compare_report.py`.
- `compare/wide_truth.py`: `compute(files_root, logdir)` for the `wide` data set (`truth.TRUTHS["wide"]`),
  from the plain-files export with `truth.load_runs`, in pure Python and without Beamtime. `drivers`:
  the finished runs under `sweeps/`, final = last logged `val/loss`; per config key except `seed` eta squared
  (between-value sum of squares over the total), the key with the largest, its value with the lowest mean and
  that mean (config values are read from `config.json`, so `0` and `1e-4` stay two values). `leaderboard`: the
  five finished runs with the lowest final `val/loss` (the failed and killed traps are left out). `divergence`:
  in `long/stability` the first step where `train/loss` is NaN or infinite or above 10 times the lowest finite
  `train/loss` logged before that step; the spike (about 6 times) does not count. `best-checkpoint`: per run of
  `long/schedules` the first step of the lowest finite `val/loss` and the `train/loss` at that step. The tasks
  `drivers`, `leaderboard`, `divergence` and `best-checkpoint` (`data: wide`, 600 s) state these rules in
  their prompts; their checks are `equal`/`close` (`drivers`), `f1` on the ids and `keyed` on `val_loss`,
  `step` (abs 0) and `train_loss` (abs 1e-6). Numbers in a task file are written `0.0001`, not `1e-4`, which
  YAML reads as text.
