## Experiments: Beamtime is the record

This project's experimental record lives in Beamtime: runs, proposals, notes and memory. Look things
up there, and write findings there. Tools are named as over MCP; the CLI is `beamtime <name>` with
spaces for `_`.

- Start each session with `memory_show`, then `status`. `guide` lists its topics; read the one you
  need before working with runs, proposals, notes or views.
- Questions about past experiments: answer from `notes`, `memory_show` and `runs`, not from
  recollection or loose files.
- Results, conclusions, dead ends and open questions go into a note on the run or group
  (`note_add`); what should outlive the session goes into the memory (`memory_update`). Not into this
  file, NOTES.md or your own memory; your own memory keeps coding preferences.
- {{record_line}}
- {{launch_line}}
- {{conventions}}
- Ask with the tools; don't parse run files. Writes add new files; never edit, move or delete in the
  log dir. Name yourself (your model id) as author.
- Never run user commands ({{user_only}}); hand the user the exact command.
- A group on another source is `@<name>/<group>`; `status` lists the sources.
