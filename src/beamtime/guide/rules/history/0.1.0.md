## Beamtime (experiment log)

This project logs its runs with Beamtime. Rules for agents; these are defaults, edit them here:

- Read `beamtime guide` (MCP: `guide`) before working with runs, proposals, notes or views.
- Ask with the tools (`status`, `runs`, `series`, `check`, `notes`, `memory_show`, ...); don't read
  or parse run files directly.
- Writes are additive: notes, proposals, memory, views and blocks are new versions. Never edit,
  move or delete files in the log dir.
- Never run user commands (serve, init, settings, set, mv, rm, gc, pull, reindex, mcp install,
  note rm, block import and export); hand the user the exact command instead.
- Remote groups are named `@<remote>/<group>`; `status` says which remotes are connected.
- Name yourself as author (your model id) on writes.
- View drafts live in `.beamtime/drafts/`: validate and render before saving, at most two render
  rounds.
