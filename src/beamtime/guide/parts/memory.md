# Memory

Notes are the complete record; memory is its compressed summary, for the next person or agent who
designs an experiment. Read `memory_show <group>` first: it returns the memory of the group and of
every group above it, root first. `status`, `guide <group>` and `memory_show` say when notes were
added since the last update.

## Write it

`memory_update` (`beamtime memory update <group> --file m.md`) saves a new version; older ones stay.
Rewrite the whole memory, do not append:

```
## Current understanding
- Warmup of 500 steps or more removes the loss spike above lr 1e-4 [[20261025-170200-m4p7]]

## Decisions and conventions
- Scaling runs use a cosine schedule from now on [[20261023-093000-c2d9]]

## Dead ends
- Label smoothing had no effect on calibration [[20261019-150000-k8s1]]

## Open questions
- Does the warmup effect hold beyond 1B parameters? [[20261025-171000-r5t3]]

## Active
- scaling/width-sweep: running, 9 of 15 runs
```

- **Every line links its evidence** with `[[note-id]]`, so the summary can be short and the record
  stays one click away.
- The five sections are a convention, not a schema. Keep to about 1.5k tokens; the tool warns
  beyond it, which forces real compression.
- Fold a concluded experiment into one line; drop what no longer matters. Nothing is lost, the
  notes remain.
- `covers_until` defaults to the time of the newest note in scope; set it when you summarized less.

## When

After a verdict or a decision, and before a long break. Not after every observation.
