# How it works

## Runs are folders

Every call to `beamtime.init()` creates a **run**: one folder with a few plain files, such as the
metrics you logged, the config, and what the script printed. Nothing is uploaded anywhere. You can
copy, move or delete runs like any other folder.

## Groups are folders too

`dir="scaling/lr-sweep"` puts the run into the folder `beamtime/scaling/lr-sweep/`. Such a folder is
a **group**. Groups can hold runs and other groups. Use them the way you'd organize experiments
anyway: one group per question.

## A proposal says what you expect

Before running a group, you can write down what you expect, for example *"lr 3e-4 converges
fastest."* That is the group's **proposal**. Runs started afterwards remember it, so later you know
what they were for. Beamtime can also check the expectation against the numbers.

## A verdict says what you found

When you're done, you (or your agent) add a **verdict**: confirmed, refuted or inconclusive, with a
sentence about why. Groups then show their status at a glance: open, being tested, concluded.

More in [Proposals and verdicts](guides/research-record.md).

## Pages show it

Each group and run has a page in the browser. By default it shows the most important curves, the
runs in a table, and the notes. An agent can build a better page for a particular question, a
**view**; see [Pages and views](guides/views.md).

## Notes and memory

Anyone can add **notes** to a group: an observation, a question, a decision. A group's **memory**
is a short summary agents read first, so they don't start from scratch each time.

## Agents use the same things

Your coding agent reads runs, notes and pages through Beamtime's tools, the same as you do in the
browser or on the command line. Agents can add notes and pages, but they never delete or move
anything. See [Working with an agent](guides/agents.md).
