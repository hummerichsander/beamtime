# Beamtime

Beamtime keeps track of your machine-learning experiments, for you and your coding agent.

- **Two lines in your training script.** Metrics, config, output, crashes and resumes are recorded
  as plain files in your project. No server, no account, nothing uploaded.
- **Every experiment says what you expect and what you found.** Write a proposal before you run;
  Beamtime checks it against the numbers; you or your agent record the verdict.
- **Your agent works with it.** Claude Code, Cursor or Codex read your runs, answer questions about
  them and build pages for you.
- **Laptop and cluster side by side.** Runs on a cluster show up next to your local ones, live,
  over ssh.

```sh
pip install 'beamtime[serve]'
beamtime init
```

```python
import beamtime

run = beamtime.init(dir="lr-sweep", config={"lr": 3e-4})
for step in range(1000):
    run.log({"train/loss": train_step()})
```

```sh
beamtime serve --open      # your experiments in the browser
beamtime mcp install       # and in Claude Code
```

## Documentation

**[hummerichsander.github.io/beamtime](https://hummerichsander.github.io/beamtime/)**: start with
the [quickstart](https://hummerichsander.github.io/beamtime/quickstart.html), then
[how it works](https://hummerichsander.github.io/beamtime/how-it-works.html). The guides cover
agents, proposals and verdicts, pages, clusters, remote machines, PyTorch Lightning, sharing and
figures, and settings. The same pages are in [`docs/`](docs/index.md).

## License

Apache 2.0. The web interface bundles third-party packages under MIT, ISC, BSD-3-Clause,
Apache-2.0 and Unlicense terms; their licenses ship with it in `THIRD_PARTY_LICENSES.txt`.
