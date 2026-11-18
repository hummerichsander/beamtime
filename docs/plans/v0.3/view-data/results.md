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
