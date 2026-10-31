# View tasks: how well agents build views

The harness gives agents tasks in a researcher's words ("show which learning rate works best"),
lets them build and save a view with Beamtime's MCP tools, and scores the result. It guards the
guide, the kit and the built-in blocks: run the smoke set after changing any of them, and the full
set before a release. The spec is in `docs/design/05-views.md`, "Evaluation harness".

## Run it

Needs Claude Code (`claude`, logged in), the `serve` extra and a Chromium for the screenshots.

```sh
uv run python bench/views/run.py --smoke                     # 10 tasks, Sonnet and Haiku, once each
uv run python bench/views/run.py --models opus --reps 3      # all tasks, one model, three times
uv run python bench/views/run.py --tasks sweep-best          # one task
uv run python bench/views/score.py bench/views/runs/<stamp>  # score again (only unscored runs)
uv run python bench/views/report.py bench/views/runs/<stamp> # write RESULTS.md again
```

Runs go to `bench/views/runs/<stamp>/` (not committed): per run the project with its generated log
dir, the agent's transcript (`transcript.jsonl`), `record.json` (tool calls, rounds, tokens, time),
`score.json`, the page's screenshot, and the batch's `RESULTS.md`. Agent runs use your Claude
subscription; the smoke set is 20 agent runs and 40 judge calls.

## Tasks

`tasks/<id>.yaml`:

```yaml
category: sweep
smoke: true                      # part of the set run on every change
page: scaling/lr-sweep           # where the view is saved; run:<role> for a generated run's page
prompt: >                        # in a researcher's words; {run:<role>} becomes that run's id
  I ran a learning-rate sweep in scaling/lr-sweep. ...
facts:
  metrics: [val/acc]             # the view's queries must ask for these
  runs: [diverging]              # and select these runs (generator roles)
  finding: "lr 3e-4 gives ..."   # the truth the view's finding is judged against
  overclaims: ["lr 0.01 is best"]
checklist:                       # yes/no items, judged from a screenshot
  - The page shows validation accuracy against the learning rate.
```

The log dirs come from `beamtime.synth` (seed 7), whose planted effects are the truth: lr 3e-4 is
best in the sweep, unigram beats BPE by about 0.4 val/ppl, one run diverges at lr 1e-2, one is
killed, one resumed, one lost and one still running.

## Scores

| Score | How |
|---|---|
| saved, valid | a view version was saved, and it validates statically on its page |
| rounds | `view_validate` and `view_render` calls the agent made |
| metrics, runs | the compiled view's queries ask for the task's metrics and select its runs |
| finding | a model judges the finding against the truth and the known overclaims |
| checklist | a model answers each item from a screenshot of the saved page |
| robust | the view also validates on a single run, a subgroup and an empty group |
