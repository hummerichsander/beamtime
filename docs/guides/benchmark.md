# Benchmark: Beamtime and plain files

Does an agent answer questions about experiments faster and more correctly with Beamtime than
with the files a researcher would otherwise have? This page describes a benchmark that measures it:
what is compared, the data and the tasks, the rules that keep the comparison fair, and what it
cannot tell you. The scripts live in
[`bench/agents/compare/`](https://github.com/hummerichsander/beamtime/tree/main/bench/agents/compare).

## The question

The same eight questions, asked of the same numbers, in four setups. A headless Claude Code session
answers each question; a script grades the answer against values computed from the data. The report
shows how many tokens and how much time a session needed and how many answers were right.

## The four setups

Every session gets the same tools (`Bash`, `Read`, `Write`, `Edit`, `Glob`, `Grep`) and Python with
numpy, pandas, scipy and matplotlib. What differs is how the data reaches the agent:

| Setup | The agent reads the runs through |
| --- | --- |
| `mcp` | Beamtime's MCP server, which adds its tools |
| `cli` | the `beamtime` command in Bash, with no MCP server |
| `files` | plain files per run: `config.json`, `metrics.csv`, `output.log` |
| `tensorboard` | TensorBoard event files per run, `hparams.yaml` and `output.log` |

`mcp` and `cli` are two interfaces of one product, so they are compared as separate setups: the `mcp`
session has no `beamtime` command on its PATH, and the `cli` session has no MCP server. Both
get Beamtime's working rules as shipped (the block `beamtime setup` writes into `CLAUDE.md`). The
`files` and `tensorboard` sessions get a few lines that describe their files. Everything else in
`CLAUDE.md` is identical byte for byte, including the line that names the Python libraries.

TensorBoard is the usual tool for a quick look at a training run, and its event files are what
PyTorch Lightning writes by default. Weights & Biases is not part of the comparison: its offline mode
only writes files for a later upload, and reading runs back needs a W&B server, so there is no
fully offline path to give an agent.

## The data

The runs are synthetic, from Beamtime's seeded generator (scale `s`) with messier data planted on
top, as real projects have it: 61 runs in six groups, with learning curves, configs and captured
output.

| Group | Runs | What it holds |
| --- | --- | --- |
| `scaling/lr-sweep` | 18 | five learning rates times three seeds that finished (peak at 3e-4), one run that diverged, one killed, and an earlier run of one setting that a later run supersedes |
| `scaling/lr-sweep-2` | 11 | the sweep's second batch: two more seeds per learning rate, validation accuracy renamed (`val/accuracy`) and logged half as often, one run out of GPU memory and rerun |
| `tokenizer/bpe-vs-unigram` | 8 | BPE against unigram, where unigram lowers the final validation perplexity; seed 3's unigram run was killed |
| `realistic/egnn-bench` | 9 | three arms (small, medium, large) with three seeds each, one killed; the large arm overfits late, and one run has a NaN validation loss |
| `realistic/lr-scan` | 12 | a scan with its own metric names |
| `scaling/long-context` | 3 | a resumed run, one still running and one lost |

Three data seeds (7, 8 and 9) give three different sets of numbers with the same planted structure.
With both batches, the best learning rate leads significantly in seeds 7 and 9 and not in seed 8,
and the tokenizer prediction is confirmed in seeds 7 and 9 and inconclusive in seed 8, so these
answers are not the same in every session.

Beamtime's research record is removed before any session: no proposals, notes or memory and no
generator manifest, since they state the answers. A session sees the runs and nothing else. Each
session gets its own copy in a folder outside the repository.

## The eight tasks

Each task is a question in plain words that names no product and no file layout, and ends with the
shape of the answer: a fenced `json` block. The full prompts, answer shapes, checks and time limits
are in
[`tasks/`](https://github.com/hummerichsander/beamtime/tree/main/bench/agents/compare/tasks).

| Task | The question | Time limit |
| --- | --- | --- |
| `best-config` | Over both batches of the sweep, counting the most recent finished run of each learning rate and seed: which learning rate gives the best final validation accuracy, and is the lead significant? | 400 s |
| `failures` | Which runs of both batches did not complete, why did each stop, and which completed later run redid it? | 400 s |
| `sweep-summary` | Per arm of the egnn benchmark, the mean energy metric at each run's best-validation-loss checkpoint, the best arm, and the runs to leave out. | 400 s |
| `check-prediction` | Is "unigram lowers `val/ppl` by more than 0.2" supported at 95 %, compared seed by seed? Verdict, effect, interval. | 300 s |
| `chart` | A figure of the final validation accuracy against the learning rate over both batches, with a line through the means, saved as a PNG. | 600 s |
| `find-runs` | Which runs of the project have a last validation accuracy of at least 0.922, whatever their status? | 400 s |
| `fastest` | Which learning rate reaches a validation accuracy of 0.9 in the fewest steps, over both batches? | 400 s |
| `table` | A table of every run of both batches with its learning rate, seed, whether it finished or was superseded, and its final accuracy. | 400 s |

## Grading

Truth is computed from the data after the sessions, with plain Python, and never written into a
session's folder. A mean over runs uses only runs that finished (status `finished` in the run's
`_run.json`); the final value is the last logged value; intervals are 95 % t-intervals (Welch, or paired by seed
where the task says so).

The grader reads the last fenced `json` block of the reply. Each task has a few checks (an exact
value, a number within a tolerance, a set of run ids, an interval whose bounds lie near the true ones, a
file of the right kind). The score is the share of checks passed, a session is `correct` when all
pass, and a missing or malformed block scores 0. For the `chart` task, the model that ran the
sessions also judges seven statements about the PNG, seeing only the image. Running, lost and killed
runs are not told apart anywhere: Beamtime calls a run lost only after 300 seconds without a
heartbeat, which a snapshot of files cannot show, so tasks and truth distinguish finished from
not finished.

## Fairness rules

- One model for every session and for the chart judge, resolved at the start of a batch and pinned as
  a full model id. A session that used another model for more than 5 % of its output is flagged.
- The same tools, the same libraries, the same preamble and the same prompts in every setup.
- Eight tasks times four setups times three seeds is 96 sessions, one session each, three at a time
  in an order shuffled with a fixed seed, so slow moments in the machine hit every setup alike.
- A session whose tool calls name the repository, `synth/` or `generate.py` has looked for the
  answers where it should not; it is flagged, listed in the table and left out of the figures.
- Only a failure of the agent scores 0: a timeout, or running out of turns. A crash of `claude`, an
  API error or a hit usage limit leaves the session ungraded, and the report counts them.
- Prompts and checks were fixed before the first batch. Where a check tests a printed value, the same
  rule holds in every setup: the `table` task and the tasks that compute a statistic ask for the values
  at full precision, and `find-runs`
  compares at a threshold (0.922) that no run's rounded value sits on.

## Measures

Per session: input, cache-write, cache-read and output tokens and their total, the cost in US dollars
as `claude` reports it, wall seconds, API milliseconds, turns, tool calls by name and tool errors,
and the score. A timed-out session keeps the tokens of its messages and scores 0. The tables give
the median with the range over the three seeds for every measure, per task and setup and per setup
over all tasks.

## Rerun it

```sh
uv run python bench/agents/compare/sessions.py --dry-run     # lists the 96 sessions and their commands
uv run python bench/agents/compare/sessions.py               # runs them: needs claude, and costs money
uv run python bench/agents/compare/tables.py bench/agents/runs/compare-<stamp>
```

The first command builds nothing and calls nothing. The second starts real Claude Code sessions with
your account; `--setups`, `--tasks`, `--seeds` and `--model` run a part of it, and
`--grade-only <batch>` grades a batch whose sessions ended on a usage limit. Projects and venvs are
built under `$BT_COMPARE_ROOT` (default `$TMPDIR/bt-compare/`) and deleted after grading unless
`--keep`. The third command writes the table and the figures into `docs/guides/benchmark/`.
[`bench/agents/README.md`](https://github.com/hummerichsander/beamtime/blob/main/bench/agents/README.md)
documents every file and flag.

## Limits

- **One model.** The numbers hold for the model and the Claude Code version of the batch; another
  model may rank the setups differently.
- **Synthetic data.** The runs are small, with planted effects and a few planted difficulties (a second
  batch, a renamed metric, superseded runs, a NaN, overfitting). Real projects are messier in other
  ways, and a different layout of files could suit an agent better than this one.
- **One author's tasks.** The tasks are the questions a researcher asks of a sweep. They were written
  by Beamtime's author and favour no setup on purpose, but they are not neutral.
- **Three seeds and one session each.** Language models vary from session to session. The ranges in
  the table show how far three seeds spread; they are not confidence intervals.
- **Setups as shipped.** `files` and `tensorboard` get a description of the files, not a tuned
  helper library; Beamtime gets its rules as shipped, not tuned to these tasks.

<!-- Results (model, Claude Code version, date, the table from results.md and the figures
tokens-vs-score and time-per-task) are added after the first full batch. -->
