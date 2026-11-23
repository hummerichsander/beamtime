## Experiments: Beamtime is the record

This project's experimental record lives in Beamtime: runs, proposals, notes and memory. Look things
up there, and write findings there. Tools are named as over MCP; the CLI is `beamtime <name>` with
spaces for `_`.

- Start a work session with `status` (it includes the memory).
  `guide` lists its topics; read the one you need before writing proposals, notes or views. For a
  question about data, go straight to the narrowest tool below. A usage error prints the
  operation's help, so no `--help` first.
- Questions about past experiments: answer from `notes`, `status` and `runs`, not from recollection
  or loose files.
- Results, conclusions, dead ends and open questions go into a note on the run or group
  (`note_add`); what should outlive the session goes into the memory (`memory_update`). Not into this
  file, NOTES.md or your own memory; your own memory keeps coding preferences.
- {{record_line}}
- {{launch_line}}
- {{conventions}}
- The operations compute the statistics, intervals and per-run summaries, and every reader of the record
  shares their numbers. Python (`from beamtime import bt`) joins, filters and formats the answers; it
  does not arrive at them: before computing a number yourself, look for the operation or field that
  returns it (`guide analysis`).
- Ask with the tools; never parse run files. Writes add new files; never edit, move or delete in the
  log dir. Name yourself (your model id) as author.
- Never run user commands ({{user_only}}); hand the user the exact command.
- A group on another source is `@<name>/<group>`; `status` lists the sources.

| Question | Tool or field |
|---|---|
| Which runs, how did they end, their settings | `runs` (`where`, `sort`, `limit`) |
| Best, mean or last value per setting | `runs` with `metric.<key>.<stat>` and `by` |
| At which step was the best value | `metric.<key>.min_step`, `max_step` |
| Where did a metric go NaN or infinite | `metric.<key>.nonfinite_step` |
| Where did a metric rise k times above its minimum | `metric.<key>.rise_step:<k>` (`rise_step`: k = 10) |
| One metric at the step of another | `metric.<a>[<b>.min_step]`, e.g. `metric.train/loss[val/loss.min_step]` |
| How did a metric evolve | `series` |
| What differs between runs or groups | `compare` |
| Which runs look wrong | `diagnose` |
| Have the runs finished | `wait` |
| Does the data support the prediction | `check` |
| All of it for my own script | `runs` or `series` with `to: name.csv`, once; the answer lists the columns |
