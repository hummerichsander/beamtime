# The research record: proposals, notes and memory

Status: **reviewed; v1 scope per the [overview](00-overview.md#scope)**

Beamtime records not only what runs did but why they were run and what was learned. This document
specifies that record: proposals with checkable predictions, the automatic check, notes, and a
compressed memory.

The design borrows from three practices:

- **Preregistration** (OSF, AsPredicted): hypothesis, measures, analysis and sample size are fixed
  before data exists; amendments are documented, never silent.
- **Architecture decision records**: decisions are immutable records that are superseded, not
  edited.
- **Electronic lab notebooks**: timestamped entries linked to the data they discuss.

## The cycle

```
proposal ──► plan ──► runs ──► check ──► verdict note ──► decision note ──► memory ──► next proposal
 (frozen)            (logged)  (automatic) (human/agent)    (what next)      (compressed)
```

Every step is a file in a group. The index derives the rest: checks, group status, the timeline,
backlinks.

## Proposals

A proposal states what a group's runs are expected to show and why. It can sit on a group or on a
run.

### Versions

Each save is a new file in `proposal/`; the newest version is the current one.

```yaml
# beamtime/scaling/warmup/proposal/20261025-091200-x8k2.yaml
schema: 1
statement: Warmup removes the loss spike and improves peak accuracy at learning rates above 1e-4.
rationale: The spike at step 120 matches the Adam second-moment estimate still warming up.
confidence: 0.7
plan:
  grid: {config.lr: [3e-4, 1e-3, 3e-3], config.warmup: [0, 500], config.seed: [0, 1, 2]}
predictions:
  - name: no-spike
    where: {config.warmup: 500}
    reduce: {metric: train/loss, stat: max, steps: [100, 300]}
    seeds: config.seed
    op: "<"
    value: 2.5
  - name: warmup-helps
    reduce: {metric: val/acc, stat: max}
    seeds: config.seed
    test: compare
    a: {config.warmup: 500}
    b: {config.warmup: 0}
    pair_by: [config.lr]
    op: ">"
    margin: 0.005
  - name: sharper-samples
    kind: manual
    description: Generated samples at the end of training look sharper with warmup.
author: claude-opus-5-5
user: ada
```

- **Membership.** At `init`, every run records in its own `_run.json` the current proposal version of
  each ancestor group and its own ([layer 1](01-storage.md#_runjson)). A proposal version is evaluated
  against exactly the runs that recorded it. This is explicit, needs no clock, and survives moving a
  run: a moved run keeps its membership, and the UI notes that it was recorded under another group.
- **Freezing.** A version is frozen once any run has recorded it. A run's own proposal is frozen from
  the run's start. Frozen versions never change; the index refuses to treat an edited frozen file as
  valid and shows the hash mismatch.
- **Before freezing**, a version can be replaced freely by saving a new one.
- **After freezing**, a new version must say what it supersedes and why:

  ```yaml
  supersedes: {version: 20261025-091200-x8k2, reason: "train/loss is logged as train/loss_step"}
  ```

  The superseded version stays frozen and is still evaluated against its runs. Runs started after the
  new version was saved record the new one. Readers see what was predicted before and after the
  amendment.
- **`confidence`** is optional: the author's belief before any data, for checking calibration later.

### Plans

A plan says which runs complete the experiment, so a check cannot be final after the first two runs
of fifteen. It is optional:

| Form | Complete when | For |
|---|---|---|
| `plan: {runs: 15}` | 15 runs of this version have ended | a sweep of known size |
| `plan: {grid: {config.lr: [...], config.seed: [...]}}` | every grid point has an ended run | a sweep defined by its grid |
| `plan: children` | the plans of all subgroups are complete | a group of sweeps |
| no plan | a decision note declares it (`completes: [scaling/warmup]`) | exploratory work |

Progress is shown wherever the check is ("9 of 15 runs"). Runs that failed, were killed or are lost
don't count; they are listed next to the plan.

### Predictions

Each prediction has a `name`, unique within the proposal, so notes and links can refer to it.

**Automatic predictions** are evaluated in four steps:

1. **Select** the runs of this proposal version, optionally narrowed by `where`, in the condition
   syntax of queries ([layer 3](03-index.md#selecting-runs)). On a run, the run itself.
2. **Reduce** each run to one number: `reduce: {metric, stat, steps}`, with `stat` one of `first`,
   `last`, `min`, `max`, `mean`, and an optional step window, the same reduction as the query
   language's windowed statistics.
3. **Merge seeds**: with `seeds: config.seed`, runs whose configs are identical except for that key
   form one point, with their values as its repetitions. Without `seeds`, each run is a point without
   repetitions.
4. **Test** the points:

| `test` | Claim | Fields | Version |
|---|---|---|---|
| `each` (default) | every point satisfies the comparison | `op` (`<`, `<=`, `>`, `>=`), and `value` or `ref: {run: <id>}`, optional `margin` | v1 |
| `compare` | the points of `a` beat those of `b` | `a`, `b` (conditions), `op`, optional `margin`, optional `pair_by` | v1 |
| `trend` | the points rise or fall along a config key | `over`, `direction`, optional `tolerance` | v1.1 |
| `best` | the best point has a given config | `best: max \| min`, `where` | v1.1 |

**Manual predictions** (`kind: manual`) state a claim that cannot be computed. They are frozen with the
proposal and stay `pending` until a verdict note decides them.

### Statistics

Small samples are the norm (two to five seeds), so the check uses intervals that are honest at that
size:

- **`each`** with `seeds`: a t-interval for each point's mean. The point passes if the whole interval
  satisfies the comparison, fails if the whole interval violates it, and is `inconclusive` otherwise.
  The prediction passes if every point passes and fails if any point fails.
- **`compare`**: a Welch t-interval for the difference between the mean of `a` and the mean of `b`,
  over their points. With `pair_by`, points of `a` and `b` that agree on those keys are paired, and a
  paired t-interval is used on the differences. For `a > b + margin`, the prediction passes if the
  interval's lower end exceeds the margin, fails if its upper end is below it, and is `inconclusive`
  in between.
- **The level** is 95 % by default; `significance: 0.99` raises it.
- **Too few repetitions** (fewer than two per point for `each`, or per side for `compare`) give
  **`insufficient`**: "add seeds, or set `significance: none`".
- **`significance: none`**, and predictions without repetitions (run-level proposals, `each` without
  `seeds`), decide on the values directly; the result says that no uncertainty was taken into account.
- Every result reports the effect, its interval and the number of points behind it. With three seeds
  the t-interval is wide (its multiplier is 4.3), so a claim passes only if the effect is clear; that
  is intended.

### The check

The index evaluates every frozen proposal version against its runs and keeps the result current. It
is never stored, because it follows from the files.

| Per prediction | Meaning |
|---|---|
| `pass`, `fail` | decided at the significance level |
| `inconclusive` | the interval straddles the claim |
| `insufficient` | too few repetitions for an interval |
| `pending` | data missing: runs still going, a metric not logged yet, a manual prediction without verdict |

The proposal's check combines them: `fail` if any prediction fails, `pass` if all pass, otherwise the
most informative of `inconclusive`, `insufficient` and `pending`. **Until the plan is complete, every
result is marked provisional**, and the check shows the plan's progress.

The check is a proposal of its own. The verdict of record is written by a person or agent, who can
disagree with the check and say why.

## Notes

Notes are the running record of a group: what was seen, decided, wondered and concluded. Each note is
a Markdown file with YAML frontmatter in `notes/`, named by its version id (`20261025-170200-m4p7.md`),
and never edited; a correction is a new note. The web UI makes this invisible: a note's title or
body is edited in place, and saving writes a new note that supersedes the old one, with its typed
fields carried over ([layer 7](07-web-ui.md#writing-from-the-ui)). The memory and a proposal that no
run has recorded yet are edited the same way, as new versions; a frozen proposal is not.

### Types

| `type` | For |
|---|---|
| `observation` | something seen in the data or the runs |
| `decision` | a choice about how to continue: a convention, a change of plan, declaring an experiment complete |
| `idea` | something to try |
| `question` | something open that needs an answer |
| `verdict` | a judgement of a proposal version |

### Fields

```markdown
---
schema: 1
description: Warmup helps above lr 1e-4; no spike in any seed; samples not visibly sharper.
type: verdict
proposal: 20261025-091200-x8k2
verdicts:
  no-spike: confirmed
  warmup-helps: confirmed
  sharper-samples: refuted
overall: confirmed
check:
  no-spike: {result: pass, effect: -0.41, ci: [-0.52, -0.33], points: 3}
  warmup-helps: {result: pass, effect: 0.011, ci: [0.004, 0.018], points: 9}
evidence:
  - {run: 20261025-101532-k3m9xq2a}
  - {metric: val/acc, stat: max, run: 20261025-101532-k3m9xq2a, value: 0.931}
  - {view: "scaling/warmup@20261025-161004-q2m1"}
  - {prediction: "scaling/warmup#warmup-helps"}
resolves: [20261020-110000-ab12]
author: claude-opus-5-5
user: ada
---

The spike at step 120 is gone in all nine warmup runs. The accuracy gain is small but consistent
across learning rates; see the view for the curves.
```

| Field | Meaning |
|---|---|
| `description` | one line, required; what listings, the timeline and agents read first |
| `type` | one of the types above |
| `author`, `user` | who wrote it (a person or model id), and the account it was written for |
| `resolves` | ids of notes this one answers or implements (a question, an idea) |
| `supersedes` | the id of a note this one corrects |
| `completes` | (decisions) groups whose open-ended experiment is declared complete |
| `proposal`, `verdicts`, `overall`, `check` | (verdicts) the version judged, a verdict per prediction (`confirmed`, `refuted`, `inconclusive`), an overall verdict, and the check at the time of writing, added automatically, so the verdict stays traceable after more runs arrive |
| `evidence` | what the note rests on, as typed entries: `run`, `metric` (with `stat`, `run`, `value`), `view`, `prediction`, `note` |

- Fields hold plain ids and paths; `[[...]]` links are for the body.
- A question is **open** until a note `resolves` it; a note is **superseded** once another note
  `supersedes` it. Both states are derived and shown in listings.
- The newest verdict on the current proposal version is the group's verdict.

### Links

`[[...]]` in note and memory bodies points to:

| Target | Syntax |
|---|---|
| a run | `[[20261025-101532-k3m9xq2a]]` |
| a group | `[[scaling/warmup]]`, `[[@cluster/scaling]]` |
| a note | `[[20261020-110000-ab12]]` |
| a prediction | `[[scaling/warmup#warmup-helps]]` |
| a view version | `[[scaling/warmup@20261025-161004-q2m1]]` |

The index resolves links and keeps backlinks, so a run, prediction or view shows the notes that cite
it. The UI shows a note's description instead of its id.

## Group status

Every group has a research status, derived from its files and shown in the frame, the `groups` block
and the sidebar ([layer 7](07-web-ui.md#shell)):

| Status | When |
|---|---|
| `open` | no proposal |
| `proposed` | a proposal, but no run has recorded its current version |
| `running` | runs of the current version exist; the plan is not complete |
| `evaluable` | the plan is complete; the check is final |
| `concluded` | a verdict exists for the current version |

In queries, the status, check, plan progress and verdict are the fields `proposal.status`,
`proposal.check`, `proposal.progress` and `proposal.verdict` ([layer 3](03-index.md#fields)).

## Memory

Notes are the complete record; **memory** is its compressed summary, for people catching up and for
agents designing the next experiment without reading dozens of notes.

### Files

Each update is a new file in `memory/`; the newest version is current. The log dir holds the project's
memory; any group can have one for its direction.

```markdown
---
schema: 1
covers_until: 2026-10-25T14:00:00Z
author: claude-opus-5-5
user: ada
---

## Current understanding
- Warmup ≥ 500 steps removes the loss spike above lr 1e-4 [[20261025-170200-m4p7]]

## Decisions and conventions
- Scaling runs use a cosine schedule from now on [[20261023-093000-c2d9]]

## Dead ends
- Label smoothing had no effect on calibration [[20261019-150000-k8s1]]

## Open questions
- Does the warmup effect hold beyond 1B parameters? [[20261025-171000-r5t3]]

## Active
- scaling/width-sweep: running, 9 of 15 runs
```

- **Every line links to its evidence**, so the summary can be compressed hard without losing the way
  back to the record.
- **The five sections** are a convention the guide recommends, not a schema.
- **A size budget** of about 1.5k tokens per memory file; `memory update` warns beyond it, which forces
  real compression.
- `covers_until` is the time of the newest note incorporated.

### Compaction

Updating memory means rewriting it: incorporating new notes, folding concluded experiments into one
line, dropping what no longer matters. Nothing is lost: notes stay, and older memory versions are
kept.

### Reading and staleness

- `beamtime memory show <group>` (MCP: `memory_show`) returns the memory of the group and of every
  group above it, root first.
- `status`, `guide` and `memory_show` say when notes have been added since `covers_until` ("7 notes
  since the last update").
- `/beamtime:memory` (an MCP prompt) updates and compacts a group's memory.

## Agent defaults

The guide ([layer 5](05-views.md#defaults)) states these as defaults:

- **Before designing an experiment**, read `memory_show` for the target group, then the open
  questions and recent decisions it points to.
- **Before a launch**, write the proposal with a plan and named predictions, so its runs record it
  from the start (`/beamtime:proposal`).
- **Verdicts** judge each prediction, cite evidence, and carry the check snapshot; disagreeing with the
  check is allowed and must be explained (`/beamtime:verdict`).
- **After a verdict or decision**, update the group's memory.
- **Never overclaim**: a finding or verdict says what the check says, including `insufficient`,
  `inconclusive` and provisional results.

## Implementation notes

Decided while building the research record (milestone M4):

- **Edits of frozen versions** are detected with `proposal_hashes` in `_run.json`
  ([layer 1](01-storage.md#_runjson)): the SDK records the hash of every proposal file it records.
  A version whose file no longer matches, or is gone, checks as `invalid` with the mismatch, and no
  prediction is evaluated. A run's own proposal counts as frozen from its start.
- **t quantiles** are computed in pure Python (Newton steps on the upper tail via the regularized
  incomplete beta function); they match SciPy to 1e-9, also for the fractional degrees of freedom of
  Welch's interval.
- **Margins and direction**: the `op` gives the direction. For `>` the claim is
  `estimate > threshold + margin`, for `<` it is `estimate < threshold - margin`; `each` compares the
  point means with `value` (or the `ref` run's reduced value), `compare` the difference `a - b` with
  0. Effects are reported as `mean - value` and `a - b`.
- **`each`** reports the worst point (closest to failing) as the effect and lists every point,
  labelled by the config keys that differ between points.
- **`compare`** without `pair_by` uses the runs of each side as the repetitions of a Welch interval;
  with `pair_by`, points that agree on those fields are paired, each the mean of its runs, and the
  paired interval runs over the pairs. `compare` always takes uncertainty into account unless
  `significance: none`.
- **Only finished runs** enter the check; with none yet, a prediction is `pending` (and says how many
  are running). A metric no run has logged is `pending` too.
- **Manual predictions** take the judgement of the newest verdict on the version: `confirmed` counts
  as `pass`, `refuted` as `fail`.
- **Verdicts must judge every prediction** of the version they name; evidence ids must exist.
- **A run's own proposal** is complete once the run has finished, whatever its plan; a blank one (no
  statement, plan or predictions) leaves the run `open`.
- **Backlinks** come from the index's links table: `card` lists the notes citing a run
  (`cited_by`), and `check` the notes citing each prediction.
- **Memory**: the size budget is measured in characters, 6000 (about 1.5k tokens); `covers_until`
  defaults to the time of the newest note at or below the group.

## Decisions

- Proposals are versioned; runs record their membership in `_run.json`; a version is frozen once a run
  records it; frozen versions are superseded with a reason, never edited.
- Plans are optional (`runs`, `grid`, `children`); without one, checks stay provisional until a
  decision note completes the group.
- Predictions are named, automatic or manual; v1 has `each` and `compare`, with `trend` and `best` in
  v1.1. Selection uses the query language's `where`.
- Intervals are t-intervals (Welch, or paired with `pair_by`) at 95 % by default; `inconclusive` and
  `insufficient` are honest outcomes; every result reports the effect, interval and number of points.
- Verdicts judge each prediction, name the proposal version, and snapshot the check.
- Notes are named by version id, have five types, and link with plain ids in fields and `[[...]]` in
  bodies.
- Groups have a derived research status: `open`, `proposed`, `running`, `evaluable`, `concluded`.
- Memory is a versioned, compressed summary per group with links to evidence and a size budget.
