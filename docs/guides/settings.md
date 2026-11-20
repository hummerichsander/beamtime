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
cache: memory                    # where the index lives; see Cache (either file)
agent: {style: careful}          # how much agents do; see Agent (project only)
```

`beamtime setup` writes the ones it asks about, leaving defaults out ([Setting up a
project](setup.md)). `beamtime set` changes `theme`, `theme_mode` and `figure_style`; edit the
others in the file.

```sh
beamtime settings                 # what is set, and where it comes from
beamtime set theme_mode dark      # change one setting of the project
```

The browser's settings page changes the same values.

## Cache

`cache` is where this machine keeps the index: a directory, or `memory` for an index that lives as
long as the process. `{user}`, `${VAR}` and `~` expand on the reading machine, so one value in
`beamtime.yaml` can serve a team.

```yaml
cache: /tmp/{user}/beamtime-cache
```

The default is `~/.cache/beamtime/`. A path on a network filesystem (NFS, Lustre, GPFS, BeeGFS,
CIFS, sshfs), the default included, is refused and the index stays in memory, because SQLite's locks
are unsafe there. Every command resolves it the same way; `beamtime doctor` shows the result and why.
`BEAMTIME_CACHE` overrides it for one session. See [Runs on a cluster](cluster.md).

A `memory` serve publishes its address in Beamtime's runtime folder, `<tmp>/beamtime-<uid>/`, which
`BEAMTIME_RUNTIME` can move. Beamtime sets that folder to owner-only (0700), also when it already exists.

## Running processes

`beamtime ps` lists your Beamtime processes on this machine: serves, the index daemon, remote
sessions, MCP servers and ssh logins kept open for remotes. `beamtime stop` ends serves only
(`stop <root>`, `stop <pid>` or `stop --all`). It exits 0 when there is no serve to stop and 4 when
the pid is not a Beamtime process.

## Agent

`agent` lives only in the project's `beamtime.yaml`: how agents behave is the team's choice.
`beamtime guide` and the rules block read it. It names a preset and any keys that differ:

```yaml
agent:
  style: hands-on          # careful (default), hands-on or analysis
  seeds: 5
  proposal_words: 300
  main_metric: val/loss
  direction: min
```

| Key | Values | careful | hands-on | analysis |
|---|---|---|---|---|
| `launch_runs` | `never`, `ask`, `allowed` | `ask` | `allowed` | `ask` |
| `memory_updates` | `suggest`, `after_verdicts` | `after_verdicts` | `after_verdicts` | `suggest` |
| `save_views` | `draft`, `save` | `save` | `save` | `save` |
| `research_record` | `off`, `encouraged`, `required` | `encouraged` | `encouraged` | `off` |
| `seeds` | an integer, 1 or more | 3 | 3 | 3 |
| `significance` | a number between 0 and 1 | 0.95 | 0.95 | 0.95 |
| `proposal_words` | an integer, 1 or more | 150 | 150 | 150 |
| `memory_tokens` | an integer, 1 or more | 1500 | 1500 | 1500 |
| `render_rounds` | an integer, 1 or more | 2 | 2 | 2 |
| `custom_blocks` | `builtin_first`, `free` | `builtin_first` | `builtin_first` | `builtin_first` |
| `mcp_tools` | `core`, `all` | `core` | `core` | `core` |

`main_metric`, `direction` (`min` or `max`), `seed_key` (e.g. `config.seed`) and `domain` (`ml` or
`simulation`) have no default and are never asked: set them, and the guide names them.

The keys guide agents; nothing enforces them. `proposal_words` counts a proposal's statement,
rationale and prediction descriptions; `beamtime proposal set` warns beyond it and still writes.
`mcp_tools: core` lists 19 tools plus `tools_more`, which reaches the views, blocks, run-control and
export tools; `all` lists every tool. An unknown key or value is reported by `beamtime settings` and
`beamtime doctor`, and the default is used. After changing `agent`, `beamtime setup` offers to
rewrite the rules block.

## Themes

A theme recolors the layout. List only the colors you change. For a pair, name the files
`<name>-light.json` and `<name>-dark.json`; a single file serves both modes:

```json
{
  "schema": 1,
  "name": "Atom One Dark",
  "type": "dark",
  "colors": {
    "paper": "#282c34", "surface": "#21252b", "line": "#3b4048", "border": "#5c6370",
    "ink": "#abb2bf", "muted": "#7f848e", "accent": "#61afef",
    "good": "#98c379", "bad": "#e06c75", "warn": "#e5c07b"
  }
}
```

Colors are `#rrggbb`. The names are `paper`, `surface`, `line`, `border`, `ink`, `muted`, `accent`, `good`,
`bad`, `warn` and `data-1` to `data-6` (the runs). Put the file in `themes/` next to `beamtime.yaml`, or
in `~/.config/beamtime/themes/` for every project, and choose it:

```sh
beamtime set theme atom-one
```

Fonts, sizes and spacing stay Beamtime's.

## Colormaps

Each chart picks its colormap in its settings (the sliders icon); "Use this on all charts on this
page" applies it to the page. Numeric and grouped colors follow matplotlib's colormap (`viridis`, `plasma`, `inferno`, `magma`, `cividis`, `turbo`, `Blues`, `Greens`, `Greys`,
`Oranges`, `Purples`, `Reds`; `coolwarm`, `RdBu`, `bwr`, `seismic`, `PuOr`, `BrBG`, `PiYG`, `RdYlBu`,
`Spectral`). Without a choice, categories use the theme's palette and many numeric values use viridis.
A chart with one curve per run keeps each run's color; choose "Color by" or a grouping to change
that. "Save as view" keeps the choice (`colormap:` on the chart).

## Figure style

PDF figures use matplotlib styles: names like `science` or `nature` (from SciencePlots), or your own
`.mplstyle` files in the project, e.g. `figure_style: [science, styles/paper.mplstyle]`.

## Remote machines

`remotes.<name>` has `host`, `command`, `path` and, in your own settings file, `enabled`. With
`enabled: false`, `serve`, `status` and the listings skip a project remote you don't use:

```yaml
# ~/.config/beamtime/settings.yaml
remotes:
  lab-gpu: {enabled: false}
```

`beamtime setup --skip-remote lab-gpu` writes that line. See [Remote machines](remotes.md).

## Environment variables

| Variable | What it does |
|---|---|
| `BEAMTIME_LOGDIR` | where runs go, for a script or a job (e.g. scratch space on a cluster) |
| `BEAMTIME_CACHE` | where Beamtime keeps its index cache; default `~/.cache/beamtime/` |
| `BEAMTIME_RUNTIME` | where Beamtime keeps its runtime files (process records, memory serves); default `<tmp>/beamtime-<uid>/`, set to owner-only (0700) |
| `BEAMTIME_PROPOSAL` | a proposal for runs that don't pass one to `init()` |
