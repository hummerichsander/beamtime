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

It asks a few questions (Enter takes what it found), shows the changes and writes when you confirm:
`beamtime.yaml`, a `beamtime/` folder for runs (run data stays out of git, notes and proposals
don't) and, if you pick a coding agent, its Beamtime server and rules. Runs from TensorBoard, Weights
& Biases, MLflow or CSV can come along. See [Setting up a project](guides/setup.md).

## 2. Log a run

Add two lines to your script, whether it runs a simulation, trains a model or scans a parameter:

```python
import beamtime

run = beamtime.init(dir="dt-scan", config={"dt": 1e-3})

for step in range(1000):
    energy = simulate_step()
    run.log({"train/energy": energy})
```

Run your script as usual. Each run becomes a folder in `beamtime/dt-scan/`, with what the script
prints and whether it finished, crashed or was stopped. A smoke test can start hidden with `BEAMTIME_HIDDEN=1`: it is recorded but counts nowhere until you run `beamtime run promote`.

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

(Done already if you chose an agent in the setup.) Ask Claude Code something like *"How did last night's runs go?"* or *"Build a page that shows
which time step keeps the energy stable."* For Cursor and Codex, and for what agents may and may not do,
see [Working with an agent](guides/agents.md).

## Next

- Say what you expect before you run, and record what you found: [Proposals and verdicts](guides/research-record.md).
- Every setup question and flag, and updating after an upgrade: [Setting up a project](guides/setup.md).
- Running on a cluster? See [Runs on a cluster](guides/cluster.md).
- Using PyTorch Lightning? See [PyTorch Lightning](guides/lightning.md).
