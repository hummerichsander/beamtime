# Working with an agent

## Connect

[`beamtime setup`](setup.md) offers this for every agent it finds. By hand:

```sh
beamtime mcp install                     # Claude Code
beamtime mcp install --client cursor     # or codex, vscode, gemini, ...
```

`--skills` writes three skills into `.claude/skills/` (views, the research record, analysis).
`--instructions` writes Beamtime's rules into a marked block in `CLAUDE.md` (or `AGENTS.md`); a
rerun updates it.

## What to ask

- *"How did last night's runs go?"*
- *"Why did run 20261024-101532-k3m9xq2a crash?"*
- *"Build a page that compares the two tokenizers."*

The prompts `/beamtime:proposal`, `/beamtime:verdict` and `/beamtime:memory` walk the agent through
the research loop.

## What agents may do

Agents read everything and **add** notes, proposals, verdicts, memory and pages, each a new file
with the agent as author. Their smoke tests start hidden (`BEAMTIME_HIDDEN=1`) until
`beamtime run promote`.

Agents never **delete, move or set up** anything; they hand you the command (`setup`, `rm`, `mv`,
`gc`, `serve`, `stop`, `ps`, `set`). When `beamtime status` reports an outdated setup, your agent
hands you `beamtime setup`.

## How much agents do

The `agent` setting in `beamtime.yaml` sets launching runs, seeds, significance, proposal length and
more; `beamtime setup` writes a preset (careful, hands-on, analysis only), and
[Settings](settings.md#agent) lists every key.

`beamtime guide <topic>` is the agent's manual (proposals, pages, checklists). It marks the defaults
it takes from `agent`; your own instruction file can override them ("always put the run table
first").
