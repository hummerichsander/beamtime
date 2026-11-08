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
| `lifecycle` | `tool`, `run`, `dest` | the tool succeeded on the run (and the copy exists) |

A view task with `remote: box` also generates a second log dir that the project reaches as the remote
`box` over the command transport; the agent works on `@box/<group>`, and the saved view is scored on
the remote's log dir.

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
