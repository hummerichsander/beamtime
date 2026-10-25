# The research record: proposals, notes and memory

Status: **draft, under discussion**

Beamtime records not only what runs did but why they were run and what was learned. This document
specifies that record: proposals with checkable predictions, the automatic check, notes, and a
compressed project memory. It replaces the provisional sections of [layer 1](01-storage.md) and is
the spec the other layers refer to.

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

Every step is a file in a folder. The index derives the rest: checks, folder status, the timeline,
backlinks.

## Proposals

A proposal states what a folder's runs are expected to show and why. It can sit on a group or on a
run.

### Versions

Proposals are versioned like views: each save is a new file in `proposal/`, and the newest version
is the current one.

```yaml
# beamtime/scaling/warmup/proposal/20261025-091200-x8k2.yaml
statement: Warmup removes the loss spike and improves peak accuracy at learning rates above 1e-4.
rationale: The spike at step 120 matches the Adam second-moment estimate still warming up.
confidence: 0.7                       # optional: the author's belief before the runs
supersedes: null                      # or a version id, see below
plan:
  grid: {config.lr: [3e-4, 1e-3, 3e-3], config.warmup: [0, 500], config.seed: [0, 1, 2]}
predictions:
  - name: no-spike
    select: {config.warmup: 500}
    reduce: {metric: train/loss, stat: max, steps: [100, 300]}
    op: "<"
    value: 2.5
  - name: warmup-helps
    reduce: {metric: val/acc, stat: max}
    seeds: config.seed
    test: compare
    a: {config.warmup: 500}
    b: {config.warmup: 0}
    op: ">"
    margin: 0.005
  - name: sharper-samples
    kind: manual
    description: Generated samples at the end of training look sharper with warmup.
author: claude-opus-5-5
user: ada
```

- **Freezing.** A group's proposal version freezes when the next run below the folder starts after the
  version was saved; a run's proposal freezes at its first logged metric. The freezing run's SDK
  records time and hash in `_frozen/<version>.json` (exclusive create). Frozen versions never change.
- **Before freezing**, a version can be replaced freely by saving a new one; drafting leaves no
  trace beyond the version history.
- **After freezing**, a new version must say what it **supersedes** and why:

  ```yaml
  supersedes: {version: 20261025-091200-x8k2, reason: "train/loss is logged as train/loss_step; prediction no-spike referred to the wrong key"}
  ```

  The superseded version stays frozen and is still evaluated, against the runs that started while it
  was current. Readers see what was predicted before and after the amendment.
- **A version saved after runs exist** is evaluated only against runs that started after it froze.
  Claims about data that was already visible are not predictions.
- **`confidence`** is optional. Recorded before any data, it allows checking later how well-calibrated
  a project's expectations were.

### Plans

A plan says which runs complete the experiment, so a check cannot pass on the first two runs of
fifteen. It is optional and takes one of three forms:

| Form | Meaning | For |
|---|---|---|
| `plan: {runs: 15}` | complete when 15 runs below the folder have ended | a sweep of known size |
| `plan: {grid: {config.lr: [...], config.seed: [...]}}` | complete when every grid point has an ended run | a sweep defined by its grid |
| `plan: children` | complete when the plans of all subfolders are complete | a group of sweeps |
| no plan | open-ended; complete once a decision note declares it (`completes: [[scaling/warmup]]`) | exploratory work |

Progress is shown everywhere the check is ("9 of 15 runs"). Runs that failed, were killed or are lost
don't count towards a plan; they are listed next to it.

### Predictions

Each prediction has a `name`, unique within the proposal, so notes and links can refer to it.

**Automatic predictions** are evaluated in four steps ([layer 3](03-index.md) implements them):

1. **Select** the runs: all runs below the folder that belong to this proposal version, optionally
   narrowed by `select` (status, tags, config values). On a run, the run itself.
2. **Reduce** each run to one number: `reduce: {metric, stat, steps}`, with `stat` one of `last`,
   `min`, `max`, `mean`, and an optional step window.
3. **Merge seeds** (groups): with `seeds: config.seed`, runs whose configs are identical except for
   that key form one point.
4. **Test** the points:

| `test` | Claim | Fields |
|---|---|---|
| `each` (default) | every point satisfies the comparison | `op`, and `value` or `ref` + optional `margin` |
| `trend` | the points rise or fall when ordered by a config key | `over`, `direction`, optional `tolerance` |
| `best` | the best point has a given config | `best: max \| min`, `where` |
| `compare` | subset `a` beats subset `b` | `a`, `b`, `op`, optional `margin` |

`ref` compares against another run (`ref: {run: <id>}`) or the view's baseline concept
(`ref: baseline`, [layer 5](05-views.md#baselines)).

**Manual predictions** (`kind: manual`) state a claim that cannot be computed. They are frozen with
the proposal like the others and stay `pending` until a verdict note decides them.

### Significance

Group predictions account for noise by default:

- Each point keeps its individual runs (seeds). A **bootstrap over these runs** (10,000 resamples,
  with a fixed seed so results are reproducible) gives a 95 % confidence interval for the tested
  quantity: the difference of means for `compare`, the point values for `each`, the probability of
  the claimed order for `trend` and of the claimed winner for `best`.
- A prediction **passes** only if the claim holds across the interval (for `compare`: the whole
  interval of the difference lies beyond the margin) and **fails** only if the opposite holds across
  it. In between, it is `inconclusive`.
- With fewer than two runs per point, there is no noise estimate. The prediction is
  **`insufficient`**: "add seeds, or set `significance: none`".
- `significance: none` decides on the means alone; `significance: 0.99` raises the level.
- Run-level predictions (one run, no repetitions) are decided directly; their result says so.

The effect size and its interval are always reported, whatever the outcome.

### The check

The index evaluates every frozen proposal version against its runs and keeps the result current. It
is never stored, because it follows deterministically from the files.

| Per prediction | Meaning |
|---|---|
| `pass`, `fail` | decided at the significance level |
| `inconclusive` | the interval straddles the claim |
| `insufficient` | too few repetitions for a noise estimate |
| `pending` | data missing: runs still going, a metric not logged yet, a manual prediction without verdict |

The proposal's check combines them: `fail` if any prediction fails, `pass` if all pass, otherwise
the most informative of `inconclusive`, `insufficient` and `pending`. **Until the plan is complete,
every result is marked provisional**, and the check shows the plan's progress.

The check is a proposal of its own. The verdict of record is written by a person or agent, who can
disagree with the check and say why.

## Notes

Notes are the running record of a folder: what was seen, decided, wondered and concluded. They are
Markdown with YAML frontmatter, one note per file in `notes/`, and never edited or deleted; a
correction is a new note.

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
description: Warmup helps above lr 1e-4; no spike in any seed; samples not visibly sharper.
type: verdict
proposal: 20261025-091200-x8k2           # the version judged
verdicts:
  no-spike: confirmed
  warmup-helps: confirmed
  sharper-samples: refuted
overall: confirmed
check:                                    # the check at the time of writing
  no-spike: {result: pass, effect: -0.41, ci: [-0.52, -0.33], runs: 9}
  warmup-helps: {result: pass, effect: 0.011, ci: [0.007, 0.016], runs: 18}
evidence:
  - {run: 20261025-101532-k3m9xq2a}
  - {view: scaling/warmup@20261025-161004-q2m1}
  - {prediction: scaling/warmup#warmup-helps}
resolves: [[20261020-110000-question-warmup]]
author: claude-opus-5-5
user: ada
---

The spike at step 120 is gone in all nine warmup runs. The accuracy gain is small but consistent
across learning rates; see the frozen view for the curves.
```

| Field | Meaning |
|---|---|
| `description` | one line, required; what listings, the timeline and agents read first |
| `type` | one of the types above |
| `author`, `user` | who wrote it (a person or model id), and the account it was written for |
| `resolves` | notes this one answers or implements: a question, an idea |
| `supersedes` | a note this one corrects |
| `completes` | (decisions) folders whose open-ended experiment is declared complete |
| `proposal`, `verdicts`, `overall`, `check` | (verdicts) the version judged, a verdict per prediction (`confirmed`, `refuted`, `inconclusive`), an overall verdict, and a snapshot of the check when the verdict was written, so it stays traceable after more runs arrive |
| `evidence` | what the note rests on: metric values, runs, view versions, predictions, other notes |

- The body is optional and short.
- A question is **open** until a note `resolves` it; a note is **superseded** once another note
  `supersedes` it. Both states are derived and shown in listings.
- The newest verdict on the current proposal version is the folder's verdict.

### Links

`[[...]]` links in note bodies and fields point to:

| Target | Syntax |
|---|---|
| a run | `[[20261025-101532-k3m9xq2a]]` |
| a folder | `[[scaling/warmup]]`, `[[@cluster/scaling]]` |
| a note | `[[20261020-110000-question-warmup]]` (its file name) |
| a prediction | `[[scaling/warmup#warmup-helps]]` |
| a view version | `[[scaling/warmup@20261025-161004-q2m1]]` |

The index resolves links and keeps backlinks, so a run, prediction or view shows the notes that cite
it.

## Folder status

Every group has a research status, derived from its files and shown in the frame, the `folders`
block and the sidebar:

| Status | When |
|---|---|
| `open` | no proposal |
| `proposed` | a proposal, no runs yet |
| `running` | runs exist; the plan is not complete |
| `evaluable` | the plan is complete; the check is final |
| `concluded` | a verdict exists for the current proposal version |

## Memory

Notes are the complete record; **memory** is its compressed summary, for people catching up and for
agents designing the next experiment without reading dozens of notes.

### Files

Memory is versioned like views: each update is a new file in `memory/`, and the newest version is
current. The log dir root holds the project's memory; any group can have one for its direction.

```markdown
---
covers_until: 2026-10-25T14:00:00Z       # the newest note incorporated
author: claude-opus-5-5
user: ada
---

## Current understanding
- Warmup ≥ 500 steps removes the loss spike above lr 1e-4 [[20261025-170200-verdict-warmup]]

## Decisions and conventions
- Scaling runs use a cosine schedule from now on [[20261023-093000-decision-cosine]]

## Dead ends
- Label smoothing had no effect on calibration [[20261019-150000-verdict-ls]]

## Open questions
- Does the warmup effect hold beyond 1B parameters? [[20261025-171000-question-scale]]

## Active
- scaling/width-sweep: running, 9 of 15 runs
```

- **Every line links to its evidence**, so the summary can be compressed hard without losing the
  way back to the record.
- **The five sections** are a convention the guide recommends, not a schema.
- **A size budget** of about 1.5k tokens per memory file; `validate` warns beyond it, which forces
  real compression.

### Compaction

Updating memory means rewriting it: incorporating new notes, folding concluded experiments into one
line, dropping what no longer matters. Nothing is lost: notes stay, and older memory versions are
kept. Compaction is therefore safe to do often.

### Reading and staleness

- `beamtime memory <folder>` and the MCP tool `memory` return the memory of the folder and of every
  folder above it, root first: the context for working in that folder, in a few thousand tokens.
- `covers_until` tells how current a memory is. `status`, `guide` and the `memory` tool say when notes
  have been added since ("7 notes since the last update").
- `/beamtime:memory` (an MCP prompt) updates and compacts a folder's memory.

## Agent defaults

The guide ([layer 5](05-views.md#the-agent-guide)) states these as defaults:

- **Before designing an experiment**, read `memory` for the target folder, then the open questions
  and recent decisions it points to.
- **Before a launch**, write the proposal, with a plan and named predictions, so it freezes before
  any data exists (`/beamtime:proposal`).
- **Verdicts** judge each prediction, cite evidence, and include the check snapshot; disagreeing with
  the check is allowed and must be explained (`/beamtime:verdict`).
- **After a verdict or decision**, update the folder's memory.
- **Never overclaim**: a finding or verdict says what the check says, including `insufficient` and
  `provisional`.

## Changes to other layers

- **Layer 1:** `proposal/` (versions) replaces `proposal.yaml`; `memory/` is a new authored folder;
  `proposal`, `memory` and `_frozen` are reserved names.
- **Layer 2:** `init(proposal=...)` writes a run's first proposal version; freezing writes
  `_frozen/<version>.json`.
- **Layer 3:** the check computes significance by bootstrap and plan progress; the index derives
  folder status, open questions and superseded notes.
- **Layer 5:** the `proposal` block shows each prediction with result, effect and interval, the plan's
  progress and the folder status; the frame shows the status.
- **Layer 8:** new commands and tools `memory` and `memory_update`; `note` gains `--resolves`,
  `--supersedes`, `--completes`; a new prompt `/beamtime:memory`.

## Decisions

- Proposals are versioned; frozen versions are superseded with a reason, never edited.
- Plans are optional (`runs`, `grid`, `children`); without one, checks stay provisional until a
  decision note completes the folder.
- Predictions are named, automatic or manual; group predictions use a 95 % bootstrap over seeds by
  default, with `inconclusive` and `insufficient` as honest outcomes.
- Verdicts judge each prediction, name the proposal version, and snapshot the check.
- Notes gain the `question` type and `resolves`, `supersedes`, `completes`; links reach runs, folders,
  notes, predictions and view versions.
- Folders have a derived research status: `open`, `proposed`, `running`, `evaluable`, `concluded`.
- Memory is a versioned, compressed summary per folder with links to evidence and a size budget;
  compaction never deletes notes.
