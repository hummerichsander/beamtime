# Settings

Settings live in two files; the project's file wins, and command-line options win over both:

- `~/.config/beamtime/settings.yaml`: yours, for every project.
- `beamtime.yaml` in the project: for this project, shared through git.

```yaml
logdir: beamtime                 # where runs go, relative to the project
theme: beamtime                  # the web UI's theme
theme_mode: system               # light, dark or system
figure_style: [science, nature]  # matplotlib styles for PDF figures
remotes: {}                      # see Remote machines
```

```sh
beamtime settings                 # what is set, and where it comes from
beamtime set theme_mode dark      # change one setting of the project
```

The browser's settings page changes the same values.

## Figure style

PDF figures use matplotlib styles: names like `science` or `nature` (from SciencePlots), or your own
`.mplstyle` files in the project, e.g. `figure_style: [science, styles/paper.mplstyle]`.

## Environment variables

| Variable | What it does |
|---|---|
| `BEAMTIME_LOGDIR` | where runs go, for a script or a job (e.g. scratch space on a cluster) |
| `BEAMTIME_CACHE` | where Beamtime keeps its index cache; default `~/.cache/beamtime/` |
| `BEAMTIME_PROPOSAL` | a proposal for runs that don't pass one to `init()` |

## Remote machines

See [Remote machines](remotes.md).
