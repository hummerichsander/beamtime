# Benchmark, wide: tasks at scale, on long series and on the research record

Base commit `7677788`, branch `v0.3-benchmark`. Proposed 2026-11-17, based on the L72 full run of the comparison
benchmark (`docs/plans/v0.3/benchmark/benchmark-plan.md`; batches `compare-20261117-122237` sonnet,
`compare-20261117-134256` haiku, `compare-20261117-140234` lean check) and the interview after it. No breaking
change; the benchmark gains a second data set and six tasks.

Run a ticket with `/run-ticket <this file> <ID>` in a fresh session; review tickets marked `+ review` with
`/review-ticket <this file> <ID>` on a stronger model. `ticket.py status <this file>` shows what's done and what's
next.

## Goal

The outcome this plan commits to, checked against at the end and in every review:

- **Done means:** the comparison benchmark has six new tasks on a second data set, `wide`: two at scale (about 300
  runs in 20 groups), two on long series (100k steps), two on the research record (a proposal with predictions,
  an earlier verdict, memory, runs added since). Every task has one answer computed from the data, and every
  setup gets the same information (the record as plain files where Beamtime isn't there). A full run of all 14
  tasks on sonnet and on haiku exists, graded and without leaks, and its numbers are summarized for the user.
- **Confirmed by:** `uv run pytest -q -n 2 tests/bench`; `uv run python bench/agents/compare/sessions.py --dry-run`
  lists 168 sessions; two batch folders with 168 graded records each; the run summary in [Findings](#findings).
- **Out of scope:** results pages, figures and the README (U71, U72 of the benchmark plan, after the user has
  discussed the numbers); changes to Beamtime itself (a ticket that finds a Beamtime bug reports it); new setups.

## Findings

Evidence: **real data** (L72 records), **code** (read, not run).

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | Sonnet scores 0.99 to 0.995 on every setup; the benchmark can't tell setups apart by accuracy | the 8 tasks are small: one log dir at synth scale `s`, about 60 runs, 2k steps | real data | Y82–Y85 |
| 2 | Plain files and TensorBoard are cheapest (45k, 58k tokens per session against 90k for Beamtime) | at this size reading every file is cheap; nothing needs aggregation, downsampling or the record | real data | Y82–Y85 |
| 3 | The record can't be tested today | `data.strip_record` deletes proposals, notes and memory, since they could state answers | code | Y83 |
| 4 | One data set per batch, hard-wired | `sessions.py` makes `root/data/<seed>` (610), `prepare` reads it (401), `truth_for` (448) | code | Y81 |

### Run summary (Y86)

Evidence: **real data**. Per session means over 42 sessions per setup (14 tasks x 3 seeds); tokens are all tokens
including cache reads; cost is at list price; no session leaked and none has `other_model` (`other_model` is false
in all 336 records). Pilots (seed 7, 24 sessions each, all 1.00 on sonnet, 0.944 to 1.00 on haiku):
`compare-20261117-160637` (sonnet), `compare-20261117-161717` (haiku).

| Batch | Model | Setup | Score | Tokens | Cost | Turns | Tool errors | drivers | leaderboard | divergence | best-checkpoint | check-all | stale-verdicts |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `compare-20261117-162537` | sonnet | cli | 0.997 | 95k | $0.066 | 7.6 | 0.55 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| | | files | 0.992 | 51k | $0.042 | 5.1 | 0.55 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| | | mcp | 0.997 | 84k | $0.053 | 7.8 | 0.31 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| | | tensorboard | 0.988 | 45k | $0.042 | 4.2 | 0.19 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `compare-20261117-171307` | haiku | cli | 0.976 | 208k | $0.009 | 12.1 | 0.31 | 0.67 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| | | files | 0.976 | 85k | $0.005 | 5.8 | 0.07 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | 1.00 |
| | | mcp | 0.976 | 162k | $0.007 | 12.2 | 1.05 | 0.67 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| | | tensorboard | 0.952 | 119k | $0.007 | 6.7 | 0.31 | 1.00 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 |

Both batches have 168 graded records. The sonnet batch was interrupted at 81 records and finished by running only
the 87 missing sessions into the same folder (same data, environments and pinned model). Notes for the discussion:

- **Sonnet scores 1.00 on all six new tasks in all four setups**; the batch's only misses are two old tasks
  (`chart` 0.88 on four sessions, `table` 0.80 on three). The new tasks do not separate setups by accuracy on
  sonnet; they separate them by cost: files and TensorBoard use 17k to 24k tokens on `divergence` and
  `best-checkpoint`, the CLI and MCP 100k to 155k.
- **Haiku's six misses on the new tasks** are three format effects and one timeout. `drivers` on cli and mcp (all
  three seeds each, score 0.67): the key is answered as `config.weight_decay`, the truth is `weight_decay`; value
  and mean are right. `leaderboard` files seed 8 (0.00): the right five runs and values, but the ids are the
  8-character suffix (`znsqh92c`), the truth the full id (`20261020-183700-yfh0pweh`). `divergence` TensorBoard
  seed 9 (0.00): timeout at 600 s after 6 turns; no cost is recorded for it, so haiku's TensorBoard cost is a
  little low. One old-task miss on haiku: `find-runs` TensorBoard seed 9 (0.00).
- **Long series** (`divergence`, `best-checkpoint`; sonnet 12/12 each): the TensorBoard CLAUDE.md section tells the
  agent to read with `size_guidance={"scalars": 0}` (all points), so TensorBoard agents saw all 100k steps and the
  sampling concern did not arise there; haiku TensorBoard 3/3 on `best-checkpoint`, 2/3 on `divergence` (the
  timeout). Beamtime setups (cli, mcp) scored 1.00 in both models on both tasks, three seeds each; how each
  session read the series (`points: all` or the export) was not checked.
- **Time limit:** the slowest new-task sessions took 154 s (sonnet, `stale-verdicts`) and 600 s (the haiku timeout);
  no other session of either batch ran past 175 s, so the files export of the long series is not slow to read.

## Brief

- **Data sets** (Y81): a task names its data set, `data: s` (default, the existing log dir) or `data: wide`.
  `sessions.py` builds each data set a batch needs once per seed, in `root/data/<seed>` (`s`, unchanged) and
  `root/data-<name>/<seed>`; truth is computed per (data set, seed). `DATASETS` and `TRUTHS` map a name to its
  builder and its truth function.
- **The wide log dir** (Y82, Y83): `bench/agents/compare/wide.py`, `make_wide_logdir(dest, *, seed, now) ->
  Manifest`, a `WideGenerator(Generator)` from the synth whose `run()` writes only these groups, all two levels
  deep: `sweeps/s01`…`sweeps/s20`, `long/stability`, `long/schedules`, `study/optimizer`. The record of
  `study/optimizer` and the project memory stay; `_synth.json` is removed.
- **The record as files** (Y83): the files and TensorBoard exports copy every `proposal/`, `notes/` and `memory/`
  folder to `record/<group>/…` (the project memory to `record/memory/`), byte for byte; their CLAUDE.md
  sections name `record/`. The `s` data set has no record, so nothing changes there.
- **Truth** (Y84, Y85): `bench/agents/compare/wide_truth.py`, `compute(files_root, logdir) -> dict[str, dict]`,
  from the plain-files export plus `record/`, reusing `truth.load_runs`. It is independent of Beamtime; the record
  tasks are cross-checked against `beamtime check` in a test.
- **Grading** (Y81): one new check kind, `keyed`: the answer and the truth are lists of objects with a key field;
  per key it compares one field (`equal`, or `close` with `abs`/`rel`). Score = correct keys ÷ max(given keys,
  expected keys).
- **Tasks** (Y84, Y85): `drivers`, `leaderboard`, `divergence`, `best-checkpoint`, `check-all`, `stale-verdicts`
  in `bench/agents/compare/tasks/`, `data: wide`, `time_limit_s: 600`. Each prompt states every rule it needs
  (final means last logged; the divergence bar; the check's method), so all setups answer the same question.

Done, for every ticket: its Done line holds; its Check passes; the benchmark's method notes say what the code does;
its heading is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q -n 2 tests/bench`; the full suite
   `uv run pytest -q -n 2` (4 workers ran out of memory here). `uv` is `~/.local/bin/uv`; unset `VIRTUAL_ENV`. A
   no-cost listing: `uv run python bench/agents/compare/sessions.py --dry-run`.
2. Generated files: none. Tickets run one at a time in this checkout.
3. Rules: CLAUDE.md's Python style. Never edit `src/beamtime/synth/`: the test fixtures depend on its bytes;
   subclass it in `bench/`. Never touch `tests/golden/`. Generation must be deterministic per seed (one
   `random.Random` per generator, no wall clock except `now`).
4. Spec: the benchmark plan's Decisions (`docs/plans/v0.3/benchmark/benchmark-plan.md` § Decisions, l. 101) still
   hold: same tools per setup (1), truth from data (6), answers as JSON (7), no leaks (10).
5. Ticket budget: 140k tokens per ticket session; split a ticket that would exceed it.
6. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading.

## Order

What's left runs in this order: Y81 Y82 Y83 Y84 Y85 Y86

```
Y81 ─ Y82 ─ Y83 ─ Y84 ─ Y85 ─ Y86      in this order (shared modules)
```

## Decisions taken; say if you want otherwise

1. **A second data set** (your decision): the new tasks run on `wide`; the 8 tasks stay on `s`, so their numbers stay
   comparable with L72. Rejected: growing the one log dir, which makes every old task slower and pricier.
2. **The record as plain files** (your decision): files and TensorBoard get the same proposal, notes and memory under
   `record/`, so only the tools differ. Rejected: the record for Beamtime only, no fair comparison.
3. **Two tasks per family** (your decision): 6 new tasks, 14 in all, 168 sessions per model.
4. **Groups two levels deep**, so `truth.load_runs` (`runs/*/*/*/config.json`) reads the wide export unchanged.
5. **One new check kind, `keyed`**, for per-run and per-prediction answers. Rejected: one kind per task, more
   grader code to review.
6. **Truth independent of Beamtime**: computed in plain Python and scipy from the export. The record tasks also
   compare it against `beamtime check` in a test; a mismatch stops the ticket.
7. **Planted answers are asserted for seeds 7, 8 and 9**: unique leaders, margins and flips hold for every seed,
   tested, or the ticket stops; a task whose answer depends on noise at the fourth decimal is no task.
8. **Prompts state every rule**: definitions that an agent would otherwise have to guess are in the prompt, as in the
   existing `check-prediction` task.
9. **The full run covers all 14 tasks at the final commit** (your decision that I run it): the error fixes after L72
   changed Beamtime, so the old tasks are rerun too. Pilot first on seed 7, both models; the run stops before any
   results page.
10. **Long series at 100k steps**: `train/loss` every step, `val/loss` every 500 steps and at the last step, and
    nothing else, so the export stays about 3 MB per run.

## Y. Wide benchmark

### Y81. Data sets per task and the `keyed` check (sonnet + review) — code — **done**

- **Touches:** `bench/agents/compare/grade.py` (`KINDS` 23, `Task` 46–72 gets `data: str = "s"`, `run_check`
  214, new `keyed`), `bench/agents/compare/sessions.py` (`run_job` 401–402, `truth_for` 448–459,
  `grade_batch` 461–540 at 502, `run_batch` 609–610), `bench/agents/compare/data.py` (new `DATASETS`),
  `bench/agents/compare/truth.py` (new `TRUTHS`); `tests/bench/test_compare_grade.py`,
  `tests/bench/test_compare_sessions.py`.
- **Read:** the benchmark plan § Decisions 6, 7, 10 (l. 124–141).
- **Check:** `uv run pytest -q -n 2 tests/bench`; `uv run python bench/agents/compare/sessions.py --dry-run | tail -1`
  still says 96 sessions.
- **Done:** a task without `data` runs on `s` exactly as before (the dry run lists the same 96 sessions); a test
  task with `data: other`, whose builder and truth function a test registers, gets its project from
  `root/data-other/<seed>` and its truth from that function; `keyed` scores the cases below.
- **Risks:** a batch of only `s` tasks builds no other data set (`test_only_needed_datasets_built`); truths of two
  data sets with the same seed don't overwrite each other (`test_truth_per_dataset`); `keyed` with a duplicate
  key in the answer counts it once and with a missing field scores that key wrong (`test_keyed_duplicates`).
- **Stop if:** `prepare` needs to know the data set beyond its `data_dir` argument.

1. `data.DATASETS: dict[str, Callable[..., Manifest]] = {"s": make_logdir}`; `truth.TRUTHS = {"s": compute}`.
   `wide` is added in Y82.
2. `sessions.data_dir(root, data, seed) -> Path`: `root/data/<seed>` for `s`, else `root/data-<data>/<seed>`.
   `run_batch` builds each data set used by the chosen tasks once per seed; `run_job` passes
   `data_dir(root, task.data, job.seed)` to `prepare`; `truth_for(root, data, seed)` exports into
   `root/truth[-<data>]/<seed>`; `grade_batch` caches truths by `(task.data, seed)`.
3. `grade.keyed(given, expected, *, key, field, abs=None, rel=None) -> float`: `given` is a list of objects (or a
   dict key → object); per expected key, correct if the field is `same` (no tolerance) or `close`; score =
   correct ÷ max(len(given keys), len(expected keys)), 0 when either is empty and the other is not, 1 when both
   are empty. The task YAML: `{kind: keyed, truth: <name>, key: id, field: step, abs: 0}`. Run ids go through
   `trail` like `ids` does.

### Y82. The wide log dir: sweeps and long series (sonnet + review) — code — **done**

- **Touches:** new `bench/agents/compare/wide.py`, `bench/agents/compare/data.py` (`DATASETS`); new
  `tests/bench/test_compare_wide.py`.
- **Read:** `src/beamtime/synth/generate.py` (`Generator` 104–137, `curves` 439–466, `spec` 566, `write_run` 722,
  `diverging` 534–551); `bench/agents/compare/data.py` (`BenchGenerator`, `own_stream`) as the model to follow.
- **Check:** `uv run pytest -q -n 2 tests/bench/test_compare_wide.py`; time `make_wide_logdir` for one seed (report
  it; under 2 minutes).
- **Done:** for seeds 7, 8, 9: 300 runs in `sweeps/s01`…`s20`, 8 in `long/stability`, 8 in `long/schedules`; the
  planted properties below hold, each asserted; equal seeds give byte-identical metric files.
- **Risks:** the 5th and 6th best finished final `val/loss` closer than 1e-3 (`test_leaderboard_gap`); the spike
  run crossing the 10× bar (`test_spike_stays_below_bar`); two schedules runs with the minimum `val/loss` at the
  same evaluation step (`test_checkpoint_unique`).
- **Stop if:** generating one seed takes over 5 minutes, or the logdir exceeds 300 MB.

1. `WideGenerator(Generator)` with `Scale(name="wide", seeds=…, steps=1000, val_every=50)`; `run()` calls
   `sweeps()`, `long_series()`, then (Y83) `study()`. `make_wide_logdir` removes `_synth.json` and returns the
   manifest; manifest roles carry the planted ids.
2. `sweeps()`: 20 groups × 15 runs. Config drawn per run from `lr ∈ {1e-4, 3e-4, 1e-3, 3e-3}`, `batch_size ∈ {64,
   128, 256}`, `weight_decay ∈ {0, 1e-4, 1e-3, 1e-2}`, `dropout ∈ {0, 0.1, 0.3}`, `model ∈ {resnet18, resnet34}`,
   `seed`. Final `val/loss` = 0.5 + wd effect `{0: 0.30, 1e-4: 0.15, 1e-3: 0, 1e-2: 0.10}` + lr effect `{1e-4:
   0.06, 3e-4: 0, 1e-3: 0.02, 3e-3: 0.08}` + at most 0.02 from each other key + noise sd 0.02. `train/loss` every
   10 steps, `val/loss` every 50 and at the last step. About 8 % `failed` (stops at 30–90 %, an error line) and 2
   % `killed`; three of them (manifest role `traps`) have a last `val/loss` below the 5th best finished run.
3. `long_series()`: 100k steps, Decision 10. `long/stability`: 8 runs (`optimizer: adamw`, `lr` from {1e-3, 2e-3,
   3e-3, 5e-3}, `seed` 0/1); three diverge at distinct steps between 20k and 80k (loss grows ×e every 500 steps, then
   NaN, then inf; status `failed`, the run stops 300 steps later); one spikes to about 6× its running minimum for
   200 steps and recovers; four are clean. `long/schedules`: `schedule ∈ {cosine, linear, step, constant}` ×
   `seed` 0/1; `val/loss` falls, then rises (overfit), its minimum at a distinct evaluation step per run.
4. `data.DATASETS["wide"] = wide.make_wide_logdir`.

### Y83. The study group and the record as files (sonnet + review) — code — **done**

- **Touches:** `bench/agents/compare/wide.py` (new `study`), `bench/agents/compare/formats.py` (new `export_record`,
  called from `export_files` 44 and `export_tensorboard` 76), `bench/agents/compare/setups.py` (`FILES` 29,
  `TENSORBOARD` 37); `tests/bench/test_compare_wide.py`, `tests/bench/test_compare_formats.py`.
- **Read:** `docs/design/09-research-record.md` § Predictions (l. 106), § Statistics (l. 133), § The check (l. 155),
  § Notes (l. 178–262), § Memory (l. 279–333); `src/beamtime/synth/generate.py` `record` (194–272) for how notes are
  written.
- **Check:** `uv run pytest -q -n 2 tests/bench`; in a scratch folder, build seed 7, then `uv run beamtime --root
  <scratch> check study/optimizer` shows the four predictions.
- **Done:** `study/optimizer` holds proposal v1 with four predictions, 18 runs that record it (3 optimizers × seeds
  0–5), a verdict note written after seeds 0–2 that states each prediction's verdict as of then, and project memory
  that repeats them; for seeds 7, 8, 9 exactly two predictions change verdict once seeds 3–5 count (asserted); the
  files and TensorBoard exports have `record/study/optimizer/{proposal,notes}/…` and `record/memory/…` equal to the
  log dir's files.
- **Risks:** a later run's start time before the verdict note's (`test_note_before_second_batch`); the export
  copying a run's own folders as record (`test_record_export_skips_runs`); the `s` export gaining a `record/`
  folder (`test_s_has_no_record`).
- **Stop if:** `beamtime check` and the generator's own verdicts disagree on seeds 0–2.

1. `study()`: optimizers `sgd`, `adamw`, `lion`; final `val/loss` per optimizer planted so that, with
   `config.seed` as repetitions, the four predictions are: `adamw-converges` (each, `adamw` last `val/loss` `<`
   0.40), `adamw-beats-sgd` (compare `adamw` `<` `sgd`), `lion-beats-adamw` (compare `lion` `<` `adamw`, margin 0),
   `sgd-under` (each, `sgd` `<` 0.55). Seeds 3–5 flip `lion-beats-adamw` and `sgd-under` (from confirmed to
   inconclusive, or the reverse; the executor picks the values, the test pins the result).
2. Runs record `proposals: {"study/optimizer": <version>}`; the verdict note (type `verdict`, `verdicts`, `check`
   as the synth writes them) is dated after seed 2's last run and before seed 3's first; the project memory under
   `memory/` says the four verdicts in one line each.
3. `formats.export_record(logdir, dest)`: copy each `proposal/`, `notes/`, `memory/` folder outside runs to
   `<dest>/record/<group>/<folder>`, the project memory to `<dest>/record/memory`. `FILES` and `TENSORBOARD` gain one line:
   "`record/<group>/`: the researchers' proposals (with predictions), notes and memory, where there are any."

### Y84. Truth and tasks at scale and on long series (sonnet + review) — code — **done**

- **Touches:** new `bench/agents/compare/wide_truth.py`, `bench/agents/compare/truth.py` (`TRUTHS`), new
  `bench/agents/compare/tasks/{drivers,leaderboard,divergence,best-checkpoint}.yaml`; new
  `tests/bench/test_compare_wide_truth.py`.
- **Read:** `bench/agents/compare/truth.py` (`load_runs` 65–90, `best_config` 153) and
  `bench/agents/compare/tasks/check-prediction.yaml` as the style for prompts and checks.
- **Check:** `uv run pytest -q -n 2 tests/bench`; `uv run python bench/agents/compare/sessions.py --dry-run --tasks
  drivers leaderboard divergence best-checkpoint | tail -1` lists 48 sessions.
- **Done:** truth for seeds 7, 8, 9 matches the manifest's planted roles: the driver is `weight_decay` with best value
  `1e-3`, the leaderboard excludes every trap, the divergence set is the three planted runs with their steps, the
  spike run is absent; every task's checks score a hand-written perfect answer 1.0 and a trap answer below 1.
- **Risks:** a NaN `val/loss` entering a mean or a minimum (`test_nan_ignored`); `0` and `1e-4` weight decay read as
  the same value from CSV (`test_config_values_exact`); the running minimum taken over NaN (`test_running_min`).
- **Stop if:** a planted answer doesn't come out of the truth; fix the data in a follow-up, not the truth.

1. `drivers`: over every finished run under `sweeps/`, final = last logged `val/loss`; per config key except
   `seed`, η² = between-value sum of squares ÷ total; answer `{"key", "best_value", "mean_at_best"}` (the value
   with the lowest mean). Checks: `key` equal, `best_value` equal, `mean_at_best` close abs 0.002.
2. `leaderboard`: the 5 finished runs with the lowest final `val/loss`, answer `{"runs": [{"id", "group",
   "val_loss"}]}`; checks: `ids` as `f1`, `val_loss` as `keyed` close abs 1e-4.
3. `divergence`: in `long/stability`, a run diverges at the first step where `train/loss` is NaN or infinite or
   above 10× the lowest `train/loss` logged up to that step; answer `{"runs": [{"id", "step"}]}`; checks: `f1` on
   ids, `keyed` on `step` (abs 0).
4. `best-checkpoint`: per run of `long/schedules`, the step of the lowest `val/loss` and `train/loss` at that step;
   answer `{"runs": [{"id", "step", "train_loss"}]}`; checks: `keyed` on `step` (abs 0) and on `train_loss` (abs
   1e-6).

### Y85. Truth and tasks on the research record (sonnet + review) — code — **done**

- **Touches:** `bench/agents/compare/wide_truth.py` (new `check_all`, `stale_verdicts`), new
  `bench/agents/compare/tasks/{check-all,stale-verdicts}.yaml`; `tests/bench/test_compare_wide_truth.py`.
- **Read:** `docs/design/09-research-record.md` § Statistics (l. 133–154); `bench/agents/compare/truth.py`
  `check_prediction` (244–275).
- **Check:** `uv run pytest -q -n 2 tests/bench`; the cross-check test runs `beamtime check study/optimizer` on seeds 7,
  8, 9.
- **Done:** for every seed and prediction, the truth's verdict, effect and interval equal `beamtime check`'s (effect
  and ends abs 1e-9); `stale-verdicts` names exactly the two planted flips with their new verdicts.
- **Risks:** Welch's degrees of freedom computed per the textbook while Beamtime uses another form
  (`test_matches_beamtime_check`); `pass`/`fail` mapped the wrong way for `<` predictions (`test_less_than_verdicts`);
  the old verdict read from memory instead of the note (`test_old_from_note`).
- **Stop if:** truth and `beamtime check` disagree and Beamtime looks wrong: report the case, don't change Beamtime.

1. `check-all`: the prompt says how each test is decided, in the words of § Statistics: `each` with seeds, a
   t-interval of the mean over seeds; `compare`, a Welch t-interval for the difference of the means; 95 %;
   confirmed when the whole interval satisfies the claim, refuted when the whole interval violates it, else
   inconclusive. Answer `{"predictions": [{"name", "verdict", "effect", "ci"}]}`; checks: `keyed` on `verdict`,
   `keyed` on `effect` (abs 0.002).
2. `stale-verdicts`: "The group's verdict note recorded verdicts; runs were added since. Which predictions' verdicts
   no longer hold, and what are they now?" Answer `{"changed": [{"name", "old", "new"}]}`; checks: `f1` on names,
   `keyed` on `new`.

### Y86. Pilot and full runs (sonnet) — real data — **done**

- **Touches:** this plan's [Findings](#findings) (the run summary); `bench/agents/compare/tasks/*.yaml` and the wide
  data only if the pilot shows a broken task.
- **Read:** the benchmark plan § L72 (l. 444–460).
- **Check:** pilot `uv run python bench/agents/compare/sessions.py --seeds 7 --tasks drivers leaderboard divergence
  best-checkpoint check-all stale-verdicts` and the same with `--model haiku`; then the full runs `sessions.py` and
  `sessions.py --model haiku` (all 14 tasks, 168 sessions each).
- **Done:** two full batches with 168 graded records each, no leak, no `other_model`; the Findings table gains one
  row per batch: per setup and model the mean score, tokens per session, cost, turns and tool errors, and the
  six new tasks' scores per setup; the batch folders are named.
- **Risks:** a session timing out because the files export of the long series is slow to read (look at timeouts per
  setup in the pilot); the judge isn't needed for the new tasks (no chart), so `grade_batch` must not wait on it.
- **Stop if:** a pilot task scores 0 on every setup of both models (the task or its truth is wrong), or a careful
  human would answer it differently from the truth. Don't write results pages: the user discusses the numbers first.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| Batch size | 96 sessions per model | 168 (14 tasks) | `--tasks` selects a subset |

## Not verified

- How long `make_wide_logdir` takes and how big it gets (Y82 measures it); each session copies or exports it.
- Whether `beamtime check` handles `compare` with seeds the way § Statistics reads (Y85's cross-check settles it).
- That the files export of 16 runs × 100k rows stays readable within 600 s by every setup (Y86's pilot).
