# Remote sources

A cluster's log dir can appear next to the local one. Its groups are named `@<name>/<group>`
(`status` lists the connected sources); everything works the same: `keys`, `runs`, `series`,
`check`, and the writes (notes, proposals, memory, views, library blocks) land on the remote.

## What differs

- **The remote is the source of truth.** Data flows one way; nothing local is merged into it.
- **Listings merge, aggregates do not.** `runs` and `groups` list both machines; a mean, a check or a
  chart over a group is computed on the source that holds its runs. A group never mixes runs of two
  sources.
- **Drafts stay local.** `view_new @cluster/scaling` reads the current view from the remote; edit
  the draft here. `view_validate` and `view_save` send it to the remote, which checks and writes it.
  `view_render` runs here, with data fetched from the remote, so it is slower than a local group.
- **A pulled snapshot is read-only** and answers while the cluster is away. Writes to it are
  refused; write to the original.
- The remote needs the same Beamtime version; if a call fails, `status` and `doctor` say why.

## Not for agents

Adding sources, pulling and settings are the user's commands: `beamtime source add <name>
<host>:<path>`, `beamtime pull <source>:<group>`. Hand the user the exact command.

## Habits

- Cite remote runs with their `@source/` prefix in notes and evidence, so links resolve.
- Expect latency: ask for narrow columns, a `limit`, and downsampled `series` rather than every step.
- Do not read or copy the remote's files; ask with the tools.
