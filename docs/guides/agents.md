# Working with an agent

Beamtime gives your coding agent tools to read your runs and to add to them. The agent sees what
you see in the browser.

## Connect

```sh
beamtime mcp install                     # Claude Code
beamtime mcp install --client cursor
beamtime mcp install --client codex
```

Add `--instructions` to also write Beamtime's working rules into `CLAUDE.md` (or `AGENTS.md`), in
a marked block you can edit around. Running it again updates the block.

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

Agents read everything and **add**: notes, proposals, verdicts, memory and pages. Every addition is
a new file with the agent as its author; nothing is overwritten.

Agents never **delete, move or set up** anything. For those, they tell you the command to run
yourself: `beamtime rm`, `beamtime mv`, `beamtime gc`, `beamtime serve`, `beamtime set`.

## The agent's manual

`beamtime guide` prints what agents read about Beamtime: how to write proposals, how to build
pages, and checklists. Its defaults are marked as defaults; your own instruction file can change
them ("always put the run table first").
