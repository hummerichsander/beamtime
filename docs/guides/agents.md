# Working with an agent

Beamtime gives your coding agent tools to read your runs and to add to them. The agent sees what
you see in the browser.

## Connect

`beamtime setup` offers this for every agent it finds ([Setting up a project](setup.md)). To connect
one by hand:

```sh
beamtime mcp install                     # Claude Code
beamtime mcp install --client cursor
beamtime mcp install --client codex
```

`--skills` writes three skills into `.claude/skills/` (views, the research record, analysis).
`--instructions` writes Beamtime's rules into a marked block in `CLAUDE.md` (or `AGENTS.md`); a
rerun updates the block.

## What to ask

- *"How did last night's runs go?"*
- *"Which learning rate works best in scaling/lr-sweep?"*
- *"Why did run 20261024-101532-k3m9xq2a crash?"*
- *"Write a proposal for a warmup ablation before I launch it."*
- *"Build a page that compares the two tokenizers."*
- *"Summarize what we learned this week into the memory."*

Three prompts walk the agent through the research loop: `/beamtime:proposal`, `/beamtime:verdict`
and `/beamtime:memory`.

## What agents may do

Agents read everything and **add** notes, proposals, verdicts, memory and pages, each a new file
with the agent as author. Smoke tests start hidden (`BEAMTIME_HIDDEN=1`) and count nowhere until
`beamtime run promote`.

Agents never **delete, move or set up** anything; they hand you the command (`beamtime setup`,
`rm`, `mv`, `gc`, `serve`, `stop`, `ps`, `set`). When your setup is out of date, `beamtime status`
says so and your agent hands you `beamtime setup`.

## How much agents do

The `agent` setting in `beamtime.yaml` says how much agents do on their own: launching runs, seeds,
significance, proposal length and more. `beamtime setup` writes a preset (careful, hands-on or
analysis only); [Settings](settings.md#agent) lists every key. A proposal beyond `proposal_words`
(150) is still written, with a warning, since it freezes once a run records it.

## The agent's manual

`beamtime guide <topic>` is what agents read: proposals, pages, checklists. Its defaults come from
the `agent` setting; your own instruction file can override them ("always put the run table
first").
