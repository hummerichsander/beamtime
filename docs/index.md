# Beamtime

Beamtime keeps track of your machine-learning experiments. Your training script logs metrics with
two lines of code; Beamtime stores them as plain files in your project and shows them in your
browser, from your laptop or a cluster.

Every experiment starts with a sentence saying what you expect, and ends with what you found. Your
coding agent (Claude Code, Cursor, Codex) reads the same runs, answers questions about them and
builds pages for you.

## Start here

1. **[Quickstart](quickstart.md)**: install Beamtime, log a run, and look at it. Five minutes.
2. **[How it works](how-it-works.md)**: runs, groups, proposals and verdicts, in plain words.

## Go further

- [Working with an agent](guides/agents.md): connect Claude Code, Cursor or Codex.
- [Proposals and verdicts](guides/research-record.md): write down what you expect, check it, conclude.
- [Pages and views](guides/views.md): have an agent build a page for an experiment.
- [Runs on a cluster](guides/cluster.md): SLURM jobs, preemption and resuming.
- [Remote machines](guides/remotes.md): see a cluster's runs next to your laptop's.
- [PyTorch Lightning](guides/lightning.md): one logger for the `Trainer`.
- [Sharing and figures](guides/export.md): a page as a file, charts for a paper.
- [Settings](guides/settings.md): themes, figure styles and where settings live.
- [Command reference](reference/cli.md): every command and its options.
