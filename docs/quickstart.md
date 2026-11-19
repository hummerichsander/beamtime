# Quickstart

## 1. Install

```sh
pip install 'beamtime[serve]'
```

Beamtime needs Python 3.11 or newer. The code you track only needs `pip install beamtime`, which
also works on Python 3.10.

Then, in your project folder:

```sh
beamtime setup
```

It looks at your project, asks a few questions (press Enter to take what it found), shows what it
will change and writes only when you confirm. You get `beamtime.yaml`, a `beamtime/` folder for
your runs (run data stays out of git, your notes and proposals don't), and, if you pick a coding
agent, its Beamtime server and rules. Earlier runs from TensorBoard, Weights & Biases, MLflow or CSV
files can come along. See [Setting up a project](guides/setup.md) for every question and flag, and
for changing an answer later.

## 2. Log a run

Add two lines to your script, whether it runs a simulation, trains a model or scans a parameter:

```python
import beamtime

run = beamtime.init(dir="dt-scan", config={"dt": 1e-3})

for step in range(1000):
    energy = simulate_step()
    run.log({"train/energy": energy})
```

Run your script as usual. Each run becomes a folder in `beamtime/dt-scan/`. Beamtime also records
what your script prints, errors, and whether the run finished, crashed or was stopped. You don't
need to call anything else. A smoke test can start hidden with `BEAMTIME_HIDDEN=1`: it is recorded but counts nowhere until you run `beamtime run promote`.

## 3. Look at it

```sh
beamtime serve --open
```

Your browser opens with your experiments on the left. Click one to see its curves and runs. Pages
update while runs are still going. `beamtime ps` lists your running Beamtime processes, and `beamtime stop` ends the serve.

No runs yet? `beamtime demo --open` opens a sample project to look around in.

## 4. Ask your agent

```sh
beamtime mcp install
```

If you chose an agent in the setup, this is done already. Now ask Claude Code something like *"How did last night's runs go?"* or *"Build a page that shows
which time step keeps the energy stable."* For Cursor and Codex, and for what agents may and may not do,
see [Working with an agent](guides/agents.md).

## Next

- Say what you expect before you run, and record what you found: [Proposals and verdicts](guides/research-record.md).
- Every setup question and flag, and updating after an upgrade: [Setting up a project](guides/setup.md).
- Running on a cluster? See [Runs on a cluster](guides/cluster.md).
- Using PyTorch Lightning? See [PyTorch Lightning](guides/lightning.md).
