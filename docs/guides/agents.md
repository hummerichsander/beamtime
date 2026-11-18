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

Add `--skills` to write three Beamtime skills into `.claude/skills/`, one per task (views, the
research record, analysis).

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

A smoke test or debugging run should start hidden (`BEAMTIME_HIDDEN=1`): it counts nowhere until someone
promotes it with `beamtime run promote`.

Agents never **delete, move or set up** anything. For those, they tell you the command to run
yourself: `beamtime setup`, `beamtime rm`, `beamtime mv`, `beamtime gc`, `beamtime serve`,
`beamtime stop`, `beamtime ps`, `beamtime set`. When your setup is out of date, `beamtime status` and `beamtime setup --check` say so,
and your agent hands you `beamtime setup`.

## How much agents do

The `agent` setting in `beamtime.yaml` says how much agents do on their own: whether they may
launch runs, how many seeds and what significance a proposal asks for, how long a proposal may be,
and more. `beamtime setup` asks for a preset (careful, hands-on or analysis only) and writes it;
[Settings](settings.md#agent) lists every key.

One of them is `proposal_words` (150 by default): agents keep a proposal's statement, rationale and
prediction descriptions to about that many words, since a proposal is frozen once a run records it.
`beamtime proposal set` still writes a longer one, and adds a line to its answer:
`warning: 212 words, beyond this project's limit of 150 (agent.proposal_words); a proposal is frozen
once a run records it, so shorten it now`.

## The agent's manual

`beamtime guide` lists the topics agents read about Beamtime (`beamtime guide <topic>`): how to
write proposals, how to build pages, and checklists. Its defaults come from the `agent` setting and
say where each value comes from; your own instruction file can change them ("always put the run table first").
