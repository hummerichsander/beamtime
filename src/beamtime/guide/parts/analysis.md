# Analysis: which tool for which question

Ask with the tools; never parse run files. Start with `keys` (what exists), then the narrowest tool.

| Question | Tool |
|---|---|
| What metrics, config keys and data does the group have? | `keys` |
| Which runs, how did they end, what were their settings? | `runs` (`where`, columns, `sort`, `limit`) |
| What differs between these runs or groups, and did the metrics move? | `compare` |
| Where does a group stand: statuses, check, best per setting, failures, notes? | `digest` (first, then the narrower tools) |
| Have the runs finished (or reached a value) yet? | `wait` (never a sleep loop or `squeue`; over MCP it returns after 45 s, call it again) |
| Which runs look wrong (non-finite, diverging, stalled, restarted, short, missing a metric)? | `diagnose`, before any mean |
| What happened in one run? | `card`, then `output` (tail, grep) |
| What did the runs print, or why did they fail? | `logs` (one run or a group; `grep`, `context`; tracebacks grouped by signature) |
| How did a metric evolve? | `series` (downsampled; aggregated with `by` or `seeds`) |
| What is the best, mean or last value, per setting? | `runs` or `query` with `metric.<key>.<stat>` columns and `by` |
| What did the runs log besides metrics? | `data` (tables, images, text) |
| Does the data support the prediction? | `check` (never re-derive it by hand) |
| What was decided, seen, left open? | `timeline`, `notes --open`, `memory_show` |
| How does the research stand? | `groups`, `proposal_show` |
| Anything else in the query language | `query` with the object form (`guide queries`) |

## Habits

- Look before you compute: a table of the runs usually shows a failed or unfinished run that
  would have spoiled a mean.
- Compare runs of the same length and the same code: `run.code` and the step window say which.
- Aggregate by the varying config keys plus seeds; runs that differ in more than noise must not
  be averaged (`keys` lists what varies).
- Put a number into a note only with its source: the query, the run, the window.
- When the tools cannot express an analysis, run your own script, save its table as a data file
  in the view draft (`data/<name>.csv`, shown by `data_table`), and record the script in a note.
