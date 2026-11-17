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

`beamtime setup` writes the ones it asks about, and leaves values at their defaults out
([Setting up a project](setup.md)). `beamtime set` changes `theme`, `theme_mode` and `figure_style`;
the other settings are edited in the file.

```sh
beamtime settings                 # what is set, and where it comes from
beamtime set theme_mode dark      # change one setting of the project
```

The browser's settings page changes the same values.

## Cache

`cache` says where Beamtime keeps its index on this machine: a directory, or `memory` for an index
that lives only as long as the process. It can be set in either file; `{user}`, `${VAR}` and `~`
expand on the machine that reads it, so one value in `beamtime.yaml` can serve a team.

```yaml
cache: /tmp/{user}/beamtime-cache
```

Without a setting the cache is `~/.cache/beamtime/`. A path on a network filesystem (NFS, Lustre,
GPFS, BeeGFS, CIFS, sshfs) is refused and the index is kept in memory instead, because SQLite's locks
are unsafe there; this includes the default when your home directory is on one. The command line,
`serve`, the MCP server and `serve --stdio` all resolve it the same way, and `beamtime doctor` shows
the result and what decided it. `BEAMTIME_CACHE` overrides the setting for one session. See
[Runs on a cluster](cluster.md).

## Agent

`agent` lives in the project's `beamtime.yaml` only: which agent you use is yours, how agents behave
in the project is the team's. `beamtime guide` and the rules block that `beamtime setup` writes read
it. It names a preset and, if you like, single keys that differ from it:

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

`main_metric`, `direction` (`min` or `max`), `seed_key` (a config field such as `config.seed`) and
`domain` (`ml` or `simulation`) have no default and are never detected or asked for: set them
yourself, and the guide then names them. They are the project's convention, so the guide labels
them `beamtime.yaml`.

These are guidance for agents, not enforcement: Beamtime never runs your experiments, so
`launch_runs: never` tells agents not to launch, and `research_record: required` tells them to
write a proposal first. `proposal_words` is how long agents keep a proposal (the words of its
statement, rationale and prediction descriptions); `beamtime proposal set` warns beyond it and
still writes. `mcp_tools` is for the MCP server: `core` lists 19 core tools and a `tools_more` tool that reaches
the views, blocks, run-control and export tools, which keeps the agent's first prompt small; `all` lists
every tool from the start. A key or value that isn't in the table is reported by `beamtime settings` and
`beamtime doctor`, and the default is used. After changing `agent`, `beamtime setup` offers to
rewrite the rules block to match.

## Themes

A theme recolors Beamtime's layout. Write a file with the colors you want to change; everything you
leave out keeps Beamtime's value. For a pair, name the files `<name>-light.json` and `<name>-dark.json`
(a single file is used in both modes):

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

Colormaps are not a setting: each chart has its own, in its settings (the sliders icon), and "Use this
on all charts on this page" applies a choice to the page. Numeric and grouped colors then follow matplotlib's
colormap (`viridis`, `plasma`, `inferno`, `magma`, `cividis`, `turbo`, `Blues`, `Greens`, `Greys`,
`Oranges`, `Purples`, `Reds`; `coolwarm`, `RdBu`, `bwr`, `seismic`, `PuOr`, `BrBG`, `PiYG`, `RdYlBu`,
`Spectral`). Without a choice, categories use the theme's palette and many numeric values use viridis.
A chart with one curve per run keeps each run's color, so the run matches its swatch everywhere: choose
"Color by" or a grouping there. "Save as view" keeps the choice in the view (`colormap:` on the chart).
An old `colormap` key in a settings file is ignored with one line.

## Figure style

PDF figures use matplotlib styles: names like `science` or `nature` (from SciencePlots), or your own
`.mplstyle` files in the project, e.g. `figure_style: [science, styles/paper.mplstyle]`.

## Remote machines

`remotes.<name>` has `host`, `command`, `path` and, in your own settings file, `enabled`. A remote
the project names that you don't use is switched off on this machine with `enabled: false`; `serve`,
`status` and the listings then skip it, and `beamtime settings` still shows it:

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
| `BEAMTIME_PROPOSAL` | a proposal for runs that don't pass one to `init()` |


