# Notes

Notes are the running record of a group. They are immutable: a correction is a new note with
`supersedes`. Add one with `note_add` (`beamtime note add`); give `group`, `type`, a one-line
`description` (what listings show), and a Markdown `body`.

## Types

| Type | Use it for |
|---|---|
| `observation` | something seen in data or runs: "the spike at step 120 is gone in all nine runs" |
| `decision` | a choice about how to continue: a convention, a change of plan; `completes: [<group>]` declares an open-ended experiment finished |
| `idea` | something to try |
| `question` | something open; it stays open until a later note `resolves` it |
| `theory` | an explanation not yet checked against data |
| `verdict` | a judgement of a proposal version (`guide verdicts`) |

An explanation you have not measured is a `theory`, not an `observation`. Once a theory is tested,
write an observation that cites it.

## Evidence and links

- `evidence` lists what the note rests on: run ids, note ids, `group#prediction`,
  `group@view-version`, or `{metric: val/acc, stat: max, run: <id>, value: 0.931}`.
- In the body, `[[run-id]]`, `[[group]]`, `[[note-id]]` and `[[group#prediction]]` become links, and
  the cited run, prediction or view shows the note as a backlink.
- `resolves: [<id>]` answers a question or implements an idea; `supersedes: <id>` corrects a note.

## Habits

- One thing per note, with a description that stands alone in the timeline.
- Quote numbers from queries and the check, not from memory; cite the run.
- A note records what you saw. Do not rewrite or delete old notes; add a new one.
- `notes --open` lists open questions: read them before designing the next experiment.
