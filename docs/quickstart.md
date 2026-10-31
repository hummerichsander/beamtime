# Quickstart

## 1. Install

```sh
pip install 'beamtime[serve]'
```

Beamtime needs Python 3.11 or newer. Your training code only needs `pip install beamtime`, which
also works on Python 3.10.

Then, in your project folder:

```sh
beamtime init
```

This creates `beamtime.yaml` and a `beamtime/` folder for your runs (and keeps that folder out of
git).

## 2. Log a run

Add two lines to your training script:

```python
import beamtime

run = beamtime.init(dir="lr-sweep", config={"lr": 3e-4})

for step in range(1000):
    loss = train_step()
    run.log({"train/loss": loss})
```

Run your script as usual. Each run becomes a folder in `beamtime/lr-sweep/`. Beamtime also records
what your script prints, errors, and whether the run finished, crashed or was stopped. You don't
need to call anything else.

## 3. Look at it

```sh
beamtime serve --open
```

Your browser opens with your experiments on the left. Click one to see its curves and runs. Pages
update while runs are still training.

No runs yet? `beamtime demo --open` opens a sample project to look around in.

## 4. Ask your agent

```sh
beamtime mcp install
```

Now ask Claude Code something like *"How did last night's runs go?"* or *"Build a page that shows
which learning rate works best."* For Cursor and Codex, and for what agents may and may not do,
see [Working with an agent](guides/agents.md).

## Next

- Say what you expect before you run, and record what you found: [Proposals and verdicts](guides/research-record.md).
- Training on a cluster? See [Runs on a cluster](guides/cluster.md).
- Using PyTorch Lightning? See [PyTorch Lightning](guides/lightning.md).
