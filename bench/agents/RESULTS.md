# View tasks: first smoke run (2026-10-31)

| task | model | saved | valid | rounds | metrics | runs | finding | checklist | robust | turns | seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long-context-resume | haiku | True | True | 6 | – | 1/1 | True | 3/5 | True | 44 | 97.3 |
| long-context-resume | sonnet | True | True | 3 | – | 1/1 | True | 2/5 | True | 22 | 58.9 |
| root-overview | haiku | True | True | 6 | – | – | True | 5/5 | – | 33 | 77.6 |
| root-overview | sonnet | True | True | 2 | – | – | False | 3/5 | – | 16 | 35.7 |
| run-diverged | haiku | True | True | 4 | 1/1 | 1/1 | True | 4/5 | True | 24 | 70.2 |
| run-diverged | sonnet | True | True | 3 | 1/1 | 1/1 | True | 4/5 | True | 14 | 41.3 |
| sweep-best | haiku | True | True | 2 | 1/1 | – | True | 7/7 | True | 20 | 49.6 |
| sweep-best | sonnet | True | True | 3 | 1/1 | – | True | 6/7 | True | 15 | 34.5 |
| sweep-divergence | haiku | True | True | 3 | 1/1 | 1/1 | True | 7/7 | True | 30 | 71.3 |
| sweep-divergence | sonnet | True | True | 3 | 1/1 | 1/1 | True | 7/7 | True | 17 | 42.3 |
| sweep-heatmap | haiku | True | True | 4 | 1/1 | – | True | 6/6 | True | 24 | 87.2 |
| sweep-heatmap | sonnet | True | True | 2 | 1/1 | – | True | 5/6 | True | 16 | 36.9 |
| sweep-lr-scatter | haiku | True | True | 2 | 1/1 | – | True | 5/5 | True | 17 | 28.3 |
| sweep-lr-scatter | sonnet | True | True | 1 | 1/1 | – | True | 5/5 | True | 9 | 20.3 |
| sweep-samples | haiku | True | True | 2 | 1/1 | – | True | 5/5 | True | 22 | 54.0 |
| sweep-samples | sonnet | True | True | 2 | 1/1 | – | True | 5/5 | True | 12 | 30.0 |
| sweep-table | haiku | True | True | 2 | 1/1 | – | True | 6/6 | True | 17 | 34.8 |
| sweep-table | sonnet | True | True | 1 | 1/1 | – | True | 6/6 | True | 9 | 23.4 |
| tokenizer-compare | haiku | True | True | 2 | 1/1 | – | True | 6/6 | True | 25 | 43.3 |
| tokenizer-compare | sonnet | True | True | 3 | 1/1 | – | True | 6/6 | True | 14 | 34.0 |

## Per model

| model | runs | saved | valid | finding true | checklist | robust |
| --- | --- | --- | --- | --- | --- | --- |
| haiku | 10 | 10/10 | 10/10 | 10/10 | 94 % | 9/9 |
| sonnet | 10 | 10/10 | 10/10 | 9/10 | 85 % | 9/9 |

## What it showed

- Agents of both sizes saved a valid view in every task, mostly within two or three rounds of
  validation and rendering; Haiku needs about twice the turns and time of Sonnet.
- The weakest task is `long-context-resume`: statuses in the run table and the group list are icons
  without a word, so "lost" and "running" can't be read from a screenshot. A UI question rather than
  a guide question.
- Fixed from this run: validation treated a proposal block on a group without a proposal as an
  error (now a warning; the block says how to write one); the finding judge counted extra true
  details against a finding; robustness is skipped for overviews, which name their groups.
