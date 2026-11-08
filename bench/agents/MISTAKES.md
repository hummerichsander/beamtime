# Mistakes agents made

One entry per failure the harness or a real session showed, with its class (product, validator, error
message, guide, task), what fixed it, and the task that guards it. Newest first. Entries come from
`bench/agents/mine.py` over real sessions until the first harness batches add their own.

| Mistake | Class | Fix | Task |
|---|---|---|---|
| `runs` asked for the field `run.started`; the field is `run.created_at` | error message | open: the message lists the fields, but not the near one | `analysis-start-times` |
| `series` got `band: minmax`, which isn't a value | error message | open: say the valid values | |
| `view_new` on a group of a remote refused ("run it there (ssh)") | product | D2 routes views to the source | `view-remote` |
| `runs` got a `by` argument, which it doesn't take | guide | open: `guide queries` shows grouping | `analysis-mean-per-lr` |
| A group path with a typo (`lr-sweeps`) ends in a dead end | error message | open: suggest the closest group | `analysis-typo-group` |
| `view_new` failed because the draft exists | error message | open: say to continue it or pick another name | |
