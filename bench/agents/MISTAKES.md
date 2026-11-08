# Mistakes agents made

One entry per failure the harness or a real session showed, with its class (product, validator, error
message, guide, task), what fixed it, and the task that guards it. Newest first. Entries come from
`bench/agents/mine.py` over real sessions until the first harness batches add their own.

| Mistake | Class | Fix | Task |
|---|---|---|---|
| `runs` asked for the field `run.started`; the field is `run.created_at` | error message | message names `run.created_at` | `analysis-start-times`; `test_field_errors_suggest_the_right_run_field` |
| `series` got `band: minmax`, which isn't a value | error message | H1: the message lists the bands | `test_an_unknown_band_lists_the_valid_ones` (via the API msgspec's own enum message still shows) |
| `view_new` on a group of a remote refused ("run it there (ssh)") | product | D2 routes views to the source | `view-remote` |
| `runs` got a `by` argument, which it doesn't take | guide | G4: `runs --by` groups | `analysis-mean-per-lr` |
| A group path with a typo (`lr-sweeps`) ends in a dead end | error message | H1: `page_of` suggests the closest group | `analysis-typo-group`; `test_page_of_finds_an_unindexed_copy_and_suggests_a_group` |
| `view_new` failed because the draft exists | error message | H1: the message says to continue it | `test_view_ops_and_the_page` |
