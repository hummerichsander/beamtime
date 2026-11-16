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

`--guide <dir>` replaces the guide parts that have a file of the same name in `<dir>` (`overview.md`,
`notes.md`, ..., and `instructions.md` for the agent rules in CLAUDE.md), so a text can be tested
without a release. The examples and the block catalogue are always the shipped ones.

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
  the last logged value of a metric; the intervals are Beamtime's own `welch_interval` at 95 %. Truth
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
  holds the true effect), `cause` (each stopped run's cause matches the wording of its true cause:
  diverged is `diverg`, `nan`, `inf`, `FloatingPoint`; killed is `kill`, `SIGTERM`, `cancel`; `failed`
  alone is no cause), `file` (a PNG or a table, inside `project`), and for the table task
  `table_ids` (17 rows), `table_values` (lr, seed, val/acc within 1e-6; the prompt asks for full precision) and `table_finished`
  (yes/no for finished or not; running, lost and killed are not told apart). `find-runs` compares at
  exactly 0.922 without tolerance.
  The `chart` task's `judge` list holds five statements (scatter of val/acc against lr, log x, about 15
  points with the failed and killed runs left out, the peak at 3e-4 readable, labelled axes); each
  becomes a check `judge1`..`judge5` next to `file`, answered by `score.ask` with the pinned model
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
  `uv pip install` (`base`: numpy, pandas, scipy, matplotlib, tensorboard; `beamtime`: the same plus this
  checkout's `beamtime[serve]`) and keeps venvs whose install finished (marked by `.installed`).
