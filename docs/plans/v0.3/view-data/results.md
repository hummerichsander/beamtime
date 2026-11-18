# View data: results

## U62: baseline on today's code

Stamp `20261118-085528`, task `view-external-csv`, Sonnet and Haiku, 3 reps each, on `8b01d99` (U61 gave the
bench `files:` and `facts.file`; no product or guide change from this plan yet). Runs are in
`bench/agents/runs/20261118-085528/` (not committed); transcript lines below are lines of
`<run>/transcript.jsonl`, run names are `view-external-csv-<model>-<rep>`.

| task | model | rep | correct | rounds | errors | tokens | turns | violations | seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| view-external-csv | haiku | 0 | True | 0 | 2 | 431973 | 24 | 4 | 49.6 |
| view-external-csv | haiku | 1 | True | 0 | 1 | 770958 | 29 | 11 | 73.3 |
| view-external-csv | haiku | 2 | True | 0 | 1 | 476168 | 24 | 7 | 49.9 |
| view-external-csv | sonnet | 0 | False | 0 | 0 | 281534 | 18 | 6 | 38.5 |
| view-external-csv | sonnet | 1 | True | 0 | 3 | 517293 | 24 | 7 | 57.3 |
| view-external-csv | sonnet | 2 | True | 0 | 1 | 275811 | 18 | 6 | 38.5 |

| kind | model | runs | correct | rounds | tool errors | tokens | violations |
| --- | --- | --- | --- | --- | --- | --- | --- |
| view | haiku | 3 | 3/3 | 0.0 | 1.3 | 559699.7 | 7.3 |
| view | sonnet | 3 | 2/3 | 0.0 | 1.3 | 358212.7 | 6.3 |

How to read the columns: `rounds` is 0 in every run although all six validated (transcript lines 38 to 98 of each
run call `view_validate` through `tools_more`); the harness counts a round only for a direct `view_validate` call, so
the column is not meaningful for the `core` tool surface. `violations` is inflated by the harness: `LOGDIR` in
`bench/agents/score.py` matches `beamtime/` anywhere in a path, and the run directories sit inside the repository
checkout (`.../Sidequests/beamtime/bench/...`), so every Read, Write and Edit counts. `file` is true in all six runs
(the saved view reads the fixture's columns and 15 rows), `provenance` (a note) is true only
in `haiku-1`.

### What every run did

- All six read the CSV with the Read tool (line 6 or 7), created a draft from `sweep` (`view_new`), and then
  **retyped the whole file** with Write into `<draft>/data/jax-sweep.csv` (haiku 72/66/62, sonnet 29/29/33). There
  is no way to copy a file into a draft, which is what `view data` (L61) adds; the retyped data happened to be right
  every time (`facts.file` true), but a 15-row file is the easy case.
- Sonnet-1 and sonnet-2 first tried `Bash` `mkdir -p ... && cp external/jax-sweep.csv .../data/` (lines 25 and 28)
  and got `Bash is disabled for this session`; they fell back to Write.
- All six used `data_table` with `file: data/<name>.csv` as a table, none a chart or custom block (the task asks
  for a table). The saved YAML holds `file: data/<sha8>-jax-sweep.csv`.
- Haiku-1 and haiku-2 searched the repository source and docs for how data files work (Grep, lines 31 to 37 and 33)
  because the guide says nothing about files; haiku-1 looked for `view data|view_data|add_data` in `src/` (line 37).

### Failures, classified

Classes in the loop's order: product, validator, error message, guide, task.

| Run | What failed | Class | Evidence |
| --- | --- | --- | --- |
| sonnet-0 | `finding.true` false, so `correct` false: the page says our runs peak at lr 1e-3 (mean 0.924) and 3e-4 is lower "because its mean includes a failed or killed run"; the task's truth is 3e-4 in both | task | The finding is honest about the scores table (3e-4 mean 0.9126, 1e-3 mean 0.9238, final answer text in `record.json`); the truth speaks about the best run, the fixture's runs make the mean disagree. The task's `finding` should say "by best run" or the fixture should not differ. Not a data-file problem. |
| all six | checklist "the table has all 15 of her rows" is no: the table shows 13 full rows and a clipped 14th | product | `page.png` of every run: the `data_table` block is cut off after about 13 rows (the last visible row `0.01 / 1` is half cut), with no scroll hint, and the title says 15. A table of 15 rows that shows 14 is a product defect in `data_table` height or in the render, to check against `docs/design/05-views.md` before U63 (no ticket of this plan covers it; see Questions of the report). |
| haiku-0, haiku-2, sonnet-0 | checklist "no error messages or empty charts" is no: the `loss` section (a `line` of `train/loss`, from the `sweep` example) is an empty chart in the screenshot | product | Same template in sonnet-1, sonnet-2 and haiku-1 draws the chart (see sonnet-2 `page.png`), so it is the lazy rendering of a below-the-fold chart in the batch screenshot, not the agent's YAML (the loss section is the unchanged example). Unrelated to files. |
| all six | no validator or error message was ever hit: every `view_validate` says `ok`, `findings: []` (sonnet-0 line 39) | validator | Nothing in the validator checks the new file path beyond existence; the mistakes the goal names (outside the draft, unknown format, wrong column, too large file, semicolon CSV) were not made by these runs, so the baseline does not show them. The planted `;` CSV case in the survey (`notes.md`) validates ok today. |
| all six | retyped the file instead of copying it | guide | The `views` guide part has no word on data files and no operation exists; agents grep the repository for it (haiku-1 line 31/37, haiku-2 line 33). Fixed by L61 and N62. |
| haiku-1, haiku-2, haiku-0, sonnet-1 | tool errors on invented tool names (`mcp__tools_more_placeholder`, `mcp__beamtime__view_show_placeholder_never`, `mcp__beamtime__mcp__beamtime__check`, `mcp__beamtime__view_show`, `mcp__beamtime__scorecard_placeholder`), and `run.count` unknown in a `runs` select (haiku-0 line 17) | guide | Agents probe tool names; the `core` surface lists `view_show` only through `tools_more`. Unrelated to this plan, and cheap errors: the plan's delta should compare `correct`, rounds of retyping, tokens and checklist, not raw error counts. |

### Reading for U63

- The baseline of `view-external-csv` is already 5 of 6 correct, so the plan's gain cannot be a pass rate. What a
  change can show: no retyped file (the file arrives by one `view_data` call), no source grep, fewer turns and
  tokens (haiku mean 560k tokens, 24 to 29 turns; sonnet 358k, 18 to 24 turns), and the checklist items on the
  table's rows, which depend on the `data_table` clipping above.
- The held-out `view-external-chart` has not been run (U63).
- Not rescored: none of the 6 runs is unscored (no judge usage limit hit).

### Bench changes after the baseline (before U63)

Four changes to the bench, made so U63's rerun compares like with like; none touches the product or the guide.
The baseline stamp `20261118-085528` was scored with the old harness and is not rescored.

- **`rounds` counts `tools_more` calls.** `run.py` names a call through `tools_more` by the tool it calls
  (`view_validate`, `view_render`, ...), so validations and renders are counted on the `core` surface too. The
  baseline's `rounds` of 0 is therefore not comparable to U63's: read the baseline's real rounds from the transcripts
  (all six validated at least once). The same rename lets the `tools` check and the user-only count see those calls.
- **`violations` match only the run's log dir.** `LOGDIR` in `score.py` matched `beamtime/` after any `/`, including
  the repository checkout the runs sit in; it now matches a relative `beamtime/...` path and `.../proj/beamtime/`.
  The baseline's 4 to 11 violations were almost all this artifact; U63's numbers start near 0 and are not a
  regression or an improvement against them.
- **Checklist item on the rows reworded** in `view-external-csv`: "the table has all 15 rows" failed in all six
  baseline runs because the `data_table` block clips after about 13 rows with no scroll hint (a UI defect, handled
  outside this plan), and the judge sees only a screenshot. The item now asks that the table is her whole sweep
  (all five learning rates, several seeds each, not a filtered part) and says a cut-off bottom edge is not the
  agent's fault; the 15 rows are scored by `facts.file` (the saved view's `file` query), which was true in all
  six. Expect this checklist item to pass in U63 only if the clipping is not what decides it.
- **Task truth made fair** in `view-external-csv` and the held-out `view-external-chart` (same wording, so the
  held-out run is not harder): the truth said 3e-4 is best in both sweeps, which holds by best run but not by the
  mean over seeds of our runs (the killed 3e-4 run pulls its mean to 0.913, below 1e-3 at 0.924), and the page's
  scorecard shows means. The truth now states both statistics and accepts a finding that is right for the statistic
  it names; the task prompts are unchanged. This is what failed `sonnet-0`; with the fix that run's finding
  would count as true.

## U63: after the plan, one refinement, the held-out task

Code at U63's start: the guide topic `data-files`, `view_data`, the file query, `data_table` with `columns` and
the validator's data checks (J61 to N62), plus the bench changes above. `rounds` counts `tools_more` calls and
`violations` only the run's log dir from here on, so those two columns do not compare with the baseline (stamp
`20261118-085528`); `correct`, tokens, turns, the `file` fact and what the agents did do.

### Stamp `20261118-125017`: first run, scored twice

First scoring: 0 of 6 correct, all six `valid` false with `columns narrows a data file; a logged table has none`.
The saved views have `data_table: {file: data/..., columns: [lr, seed, val_acc]}`, which is valid; the validator
only skipped the key-table branch when a draft folder was given. The scorer (`static` without a data folder) and
`view upgrade` reach the second branch, which fired on any `columns`. That is a **validator** bug of L62, found
here and fixed (guard `n.file is None`, test in `test_data_table_columns_need_a_file`); the six runs were scored
again with the fixed validator (the agents had used `view_validate` with the draft, which was `ok`).

Second scoring: 2 of 6 correct (haiku-1, haiku-2). `valid`, `file` and `provenance` true in all six. The four
failures were `finding.true` false: sonnet-0, -1 and -2 saved with `finding: null` (the validator and the save
both say `no finding`, the agents ignored the warning after reading the recipe, which ended at `view_save`
without a finding), haiku-0 named the best lr by the wrong statistic (a best-run figure called a mean).

### Refinement (one)

Guide class: step 6 of the `data-files` recipe now says to set `finding:` and a caption per chart before
rendering and saving. Nothing else changed.

### Stamp `20261118-125909`: after the refinement

| task | model | rep | correct | rounds | errors | tokens | turns | seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| view-external-csv | haiku | 0 | False | 4 | 0 | 497793 | 25 | 53.1 |
| view-external-csv | haiku | 1 | True | 4 | 1 | 530898 | 26 | 58.6 |
| view-external-csv | haiku | 2 | True | 8 | 2 | 1033005 | 33 | 95.5 |
| view-external-csv | sonnet | 0 | True | 5 | 0 | 439286 | 21 | 54.3 |
| view-external-csv | sonnet | 1 | True | 4 | 0 | 466879 | 21 | 52.3 |
| view-external-csv | sonnet | 2 | True | 2 | 1 | 319715 | 17 | 37.2 |

`report.py --base 20261118-085528 --new 20261118-125909` (rounds and violations not comparable, see above;
the baseline was scored with the old truth, under which sonnet-0 failed: read against today's truth (not rescored) the
baseline is 6 of 6, so `correct` did not go up):

| model | n | correct (base to new) | tool errors | tokens | turns |
| --- | --- | --- | --- | --- | --- |
| haiku | 3/3 | 1.00 to 0.67 | 1.33 to 1.00 | 559700 to 687232 | 25.7 to 28.0 |
| sonnet | 3/3 | 0.67 to 1.00 | 1.33 to 0.33 | 358213 to 408627 | 20.0 to 19.7 |

What changed in behaviour, from the transcripts:

- **No retyped file**: 0 of 6 runs wrote the CSV with Write (baseline 6 of 6; the Writes left are the draft's
  `view.yaml`); all six called `view_data` once (haiku-1, -2 and sonnet-2 twice) and used the answer's snippet.
  No source grep, no `Bash` attempt, no invented tool for the file.
- `file` true in 6 of 6 (baseline 6 of 6), `provenance` (a note) true in 6 of 6 (baseline 1 of 6).
- **Tokens and turns went up, not down** for haiku (+23 percent) and sonnet (+14 percent tokens, same turns): the
  agents now read the topic, render and validate more (rounds 3.7 to 5.3 against transcripts that validated
  about once before) and write a note. The saving the plan hoped for is not in these numbers; the gain is the
  copied file, the provenance note and the checks.
- The one failure, haiku-0: a finding that gives our 3e-4 sweep as 0.928 "over seeds" and calls it best; the
  judge reads that as the wrong statistic. Not a data-file mistake; a task-side judgment on the statistic.
- Checklist: "whole sweep" now passes in 5 of 6 (the judge no longer holds the clipping against the page except
  in sonnet-1), "no empty charts" fails in 4 of 6 on the sweep example's lazily rendered chart below the fold
  (known from the baseline, unrelated to files). The `data_table` clipping is a separate UI ticket.

Result against the Done line: `view-external-csv` correct in 5 of 6 runs after the refinement (2 of 6
before it, both haiku); the failure is named above.

### Held-out: stamp `20261118-130312`, `view-external-chart`, 3 reps on each model, run once

| model | rep | correct | rounds | errors | tokens | turns | seconds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| haiku | 0 | False | 3 | 1 | 628800 | 26 | 76.3 |
| haiku | 1 | False | 6 | 2 | 1058221 | 32 | 91.0 |
| haiku | 2 | True | 3 | 0 | 1024628 | 32 | 95.7 |
| sonnet | 0 | True | 8 | 1 | 626913 | 34 | 93.1 |
| sonnet | 1 | True | 9 | 0 | 653428 | 33 | 97.3 |
| sonnet | 2 | False | 7 | 0 | 880620 | 38 | 109.0 |

3 of 6 correct. Five of six saved a valid view with `file` true and the chart items (from the file, in a custom
block) true; haiku-0 did not save: its custom `bt.chart.Scatter` drew an empty plot and it stopped after the two
render rounds the harness allows (its last message says so). That is the one failure on the file-to-chart path;
its cause (the block's code or the kit) was not diagnosed, since the held-out task is not read for refinement: a
candidate for a task of its own. The other three failures are `finding.true` false: the finding names the best lr
without saying by which statistic (best run or mean over seeds) where the truth's two statistics disagree for our
sweep. One run (sonnet-0) wrote no provenance note. The checklist item "no empty charts" fails in four of the five
scored runs on a lazily rendered built-in chart, as in the other task. No guide change follows from the held-out
run.

### After U63: truth completed, one guide line (not measured)

Four runs failed on the best learning rate: two called a best-run figure a mean (an agent error), two failed
because the judge counted claims the truth does not mention (held-out sonnet-2 "similar values per lr", csv
haiku-0 "1e-3 is second") as overclaims. Afterwards the facts of `view-external-csv` and `view-external-chart`
were completed with the best run and the mean over seeds per learning rate for both sweeps (computed from the
seed-7 synth log dir and `fixtures/jax-sweep.csv`), the judge's rule left unchanged, and the `data-files` topic got
one line telling findings to name the statistic. Neither change has been run through the bench.
