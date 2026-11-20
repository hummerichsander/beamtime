# Quickstart

## 1. Install

```sh
pip install 'beamtime[serve]'   # Python 3.11+
beamtime setup                  # in your project folder
```

The code you track needs only `pip install beamtime`, which also works on Python 3.10.

`beamtime setup` asks a few questions (Enter takes what it found) and writes after you confirm:
`beamtime.yaml`, a `beamtime/` folder for runs (run data stays out of git, notes and proposals
don't) and, if you pick a coding agent, its Beamtime server and rules. It can also import runs from
TensorBoard, Weights & Biases, MLflow or CSV. See [Setting up a project](guides/setup.md).

## 2. Log a run

```python
import beamtime

run = beamtime.init(dir="dt-scan", config={"dt": 1e-3})

for step in range(1000):
    energy = simulate_step()
    run.log({"train/energy": energy})
```

Each run becomes a folder in `beamtime/dt-scan/` with the metrics, the printed output and whether it
finished, crashed or was stopped. Start a smoke test with `BEAMTIME_HIDDEN=1`: it is recorded but
counts nowhere until `beamtime run promote`.

## 3. Look at it

```sh
beamtime serve --open   # experiments on the left, live updates
beamtime demo --open    # a sample project, if you have no runs yet
beamtime ps             # your running Beamtime processes
beamtime stop           # end the serve
```

## 4. Ask your agent

```sh
beamtime mcp install    # Claude Code; done already if you picked it in setup
```

Ask *"How did last night's runs go?"* or *"Build a page that shows which time step keeps the energy
stable."* Cursor, Codex and what agents may do: [Working with an agent](guides/agents.md).

## Next

- [Proposals and verdicts](guides/research-record.md): say what you expect, record what you found.
- [Runs on a cluster](guides/cluster.md) and [PyTorch Lightning](guides/lightning.md).
