# Audit: what Beamtime detects on its own

Every place where Beamtime decides something from names, shapes, timing or the environment instead of
being told. Written 2026-11-15 at `c092453` (branch `setup`). Evidence is the code, read but not run;
a row marked *verify* needs a test before a fix. The setup scan and the importers are left out: the setup
plan owns them while its tickets run.

Verdicts: **keep** (robust, or it fails safely and visibly), **harden** (the idea is right, the rule is
too loose), **reconsider** (the rule should be replaced).

## Summary

| # | What | Verdict |
|---|---|---|
| 1 | Direction of a metric from its name | harden |
| 2 | Log scale for losses | reconsider |
| 3 | Clocks (`epoch`, `global_step`) | harden |
| 4 | Chart sections by prefix | harden (decided) |
| 5 | The seed key | harden |
| 6 | Merging seeds above 8 runs | reconsider |
| 7 | Markers on sparse curves | harden (decided) |
| 8 | Varying config keys | keep, show why |
| 9 | Failure signature | harden |
| 10 | Lost runs | keep, show the age |
| 11 | Requeue continuation | keep |
| 12 | Time-limit kill reason | keep |
| 13 | Scheduler | keep |
| 14 | Target resolution | keep |
| 15 | Reserved folders, run ids by shape | keep |
| 16 | Index freshness | keep |
| 17 | A running serve | keep |
| 18 | Config readout | keep |
| 19 | Headless render browser | keep |
| 20 | Histograms by column names | keep |

## Harden or reconsider

**1. Direction from the name.** `views/defaults.py:310` `lower_is_better`: lower is better when the
metric's last segment *contains* one of `loss err ppl perplexity nll mse mae wer cer`. Substring matching
misfires: `power`, `answer_acc`, `lower_bound` and `tower_*` contain `wer`. The direction picks the
best run in the header, the Main pins' direction and (through 2) the scale. Fix: match whole tokens
(split on `_ . - /` and camelCase); the view's `metrics:` entry still overrides.

**2. Log scale for losses.** `views/compile.py:303`: a chart is log when its first metric's name holds
`loss` and 1 says lower is better. A name says nothing about the values: negative or zero losses (ELBO
style, contrastive, GAN) are common, and a loss that moves within one decade reads better linear.
Fix: decide from the data, log only when every shown value is positive and they span more than two
decades, else linear; an explicit `scale` still wins. *Verify* how the chart draws non-positive values
on a log axis today (`bt/curves.ts:177` `logRange` assumes `min > 0`).

**3. Clocks.** `views/defaults.py:23`: exactly `epoch`, `global_step` and `trainer/global_step` count
as clocks (no chart, offered as x). `train/epoch` (what the Hugging Face Trainer logs), `step`,
`iteration` and `time` become charts of a straight line. Fix: match the leaf name against a short list
(`epoch`, `step`, `global_step`, `iteration`, `iter`).

**4. Sections by prefix.** `views/defaults.py:234`. Decided: `/`, `.` and `_` after a known prefix,
no more "a prefix with one metric goes to Other", and the guide recommends `/`.

**5. The seed key.** The default view merges seeds only on `config.seed` (`views/settings.py:12`), while
`query/distinguish.py:95` `is_seed` treats any key whose leaf is `seed` as the seed. So `trainer.seed`
counts as a seed when grouping, but the default view doesn't merge on it, and `random_seed` or
`data_seed` count nowhere. Fix: one rule in one place; the default view uses the key `is_seed` finds when
exactly one exists, and the leaf list grows to `seed`, `random_seed`, `rng_seed`.

**6. Merging seeds above 8 runs.** `views/defaults.py:14` and `:87`: the default view shows seeds as a mean
with a band only when the group has more than 8 runs. A sweep that is still coming in changes from
single curves to bands when its 9th run lands, and a 2-arm by 4-seed sweep never merges. Fix: merge
whenever the seed varies and some arm has two or more seeds, whatever the count.

**7. Markers.** `bt/curves.ts:142`: each curve marks every point when it has at most 30 finite values.
Decided: one decision per chart, plus `auto / on / off` in the chart settings.

**9. Failure signature.** `query/facts.py:118`: the last non-empty line of the error or traceback,
numbers and hex replaced by `#`, cut at 120 characters. Paths and names in messages split one failure
into many (`No such file: /scratch/a/run1.pt` and `.../run2.pt`); a wrapper that re-raises a generic
line merges different failures. Fix: also replace paths and quoted strings; when the last line is a bare
exception type, add the line before it.

## Keep

**8. Varying config keys.** `query/distinguish.py`: keys whose values differ; aliases (keys that split
the runs the same way) fold into the shortest; strings unique to every run that look like a path or a
date are noise; a key that a coarser key determines is dropped. Sound. What hurts is that the reasons
are invisible: Color by and the group description silently lack a key. Show them: the `keys` answer
already carries `aliases`; add the dropped keys with "same split as `<key>`", and list both in Color by.

**10. Lost runs.** `format/run.py:105`: a running run whose `_run.json` is older than 300 s (the SDK
beats every 30 s) is lost. A SIGKILL or OOM kill shows as running for up to five minutes; a suspended
job or a sleeping laptop shows lost, then running again. The rule only derives, never writes, so it
heals itself. Show the age ("no heartbeat for 7 min") so lost reads as a fact, not a verdict.

**11. Requeue continuation.** `sdk/run.py:952` `resolve_resume`: an explicit `resume`, else a `key`,
else a SLURM requeue (`SLURM_RESTART_COUNT > 0`) with exactly one unfinished run of the same job in the
folder; several runs ask for `key=` or `name=` with a warning and start a new run. It refuses to guess.
SLURM only; PBS and LSF requeues start new runs, which is safe.

**12. Time-limit kill reason.** `sdk/run.py:815`: SIGTERM within 300 s of `SLURM_JOB_END_TIME` records
`time_limit`. A `scancel` in that window is mislabelled; rare and harmless.

**13. Scheduler.** `sdk/env.py:123`: from the scheduler's own variables. Robust.

**14. Target resolution.** `query/resolve.py`: a group path first, then a moved group, then a unique id
suffix (4 characters or more) or a run name; several matches raise. A run named like a group made later
changes what the word means; acceptable.

**15. Reserved folders, run ids by shape.** `format/tree.py:10`: folders starting `_` or `.` and the
authored names are never groups, and pages tell runs from groups by the id's shape; the SDK refuses
such folder names (`sdk/paths.py:93`), so neither can collide.

**16. Index freshness.** `index/ingest.py:72`: the mtime of `_run.json` and the sizes of the streams. On
NFS attribute caching delays updates (often up to 60 s) but never makes them wrong.

**17. A running serve.** `index/cache.py:255`: `serve.json` counts only while another process holds
`serve.lock`, so a crashed serve leaves no false entry. The basis for `beamtime ps`.

**18. Config readout.** `sdk/run.py:64` `to_config`: by type (dict, dataclass, Pydantic,
`argparse.Namespace`, OmegaConf); anything else raises in `init()`. That breaks the script, but on its
first line, before any work, like a wrong argument. Keep.

**19. Headless render browser.** `views/render.py:108`: Playwright, then an installed Chromium, Chrome or
Edge; without one the render is skipped with the install command.

**20. Histograms by column names.** `blocks/plots.ts:296`: a table with `bin_start`, `bin_end` and
`count` columns is drawn as a histogram. These are names the SDK writes itself.

## Proposed tickets

- **UI plan**: 2, 3, 4, 6, 7, and showing the reasons in 8.
- **Record and tools**: 1, 5, 9, and the age in 10.
- Nothing for 11 to 20.
