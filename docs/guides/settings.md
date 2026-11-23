# Settings

Command-line options win over the project's `beamtime.yaml` (shared through git), which wins over
your `~/.config/beamtime/settings.yaml`.

```yaml
logdir: beamtime                 # where runs go, relative to the project
theme: beamtime                  # the web UI's theme
theme_mode: system               # light, dark or system
figure_style: [science, nature]  # matplotlib styles for PDF figures
remotes: {}                      # see Remote machines
cache: memory                    # where the index lives (either file)
agent: {style: careful}          # how much agents do (project only)
```

```sh
beamtime settings                 # each value and where it comes from
beamtime set theme_mode dark      # theme, theme_mode or figure_style
```

`beamtime setup` writes what it asks about, and the browser's settings page changes the same values;
edit the rest in the file.

## Cache

`cache` is where this machine keeps the index: a directory, or `memory` for an index that lives as
long as the process. `{user}`, `${VAR}` and `~` expand on the reading machine, so one value can
serve a team:

```yaml
cache: /tmp/{user}/beamtime-cache
```

The default is `~/.cache/beamtime/`. A path on a network filesystem (NFS, Lustre, GPFS, BeeGFS,
CIFS, sshfs) is refused and the index stays in memory, since SQLite's locks are unsafe there.
`beamtime doctor` shows the result and why; `BEAMTIME_CACHE` overrides it for one session.

## Running processes

`beamtime ps` lists your Beamtime processes here: serves, the index daemon, remote sessions, MCP
servers and kept-open ssh logins. `beamtime stop` ends serves only (`stop <root>`,
`stop <pid>`, `stop --all`); it exits 0 when there is none and 4 when the pid is not Beamtime's.

## Agent

`agent` lives only in the project's `beamtime.yaml` (the team's choice) and is read by `beamtime
guide` and the rules block. Name a preset and the keys that differ:

```yaml
agent:
  style: hands-on          # careful (default), hands-on or analysis
  seeds: 5
  main_metric: val/loss
  direction: min
```

| Key | Values | Default |
|---|---|---|
| `launch_runs` | `never`, `ask`, `allowed` | `ask`; hands-on `allowed` |
| `memory_updates` | `suggest`, `after_verdicts` | `after_verdicts`; analysis `suggest` |
| `research_record` | `off`, `encouraged`, `required` | `encouraged`; analysis `off` |
| `save_views` | `draft`, `save` | `save` |
| `seeds` | integer ≥ 1 | 3 |
| `significance` | between 0 and 1 | 0.95 |
| `proposal_words` | integer ≥ 1 | 150 |
| `memory_tokens` | integer ≥ 1 | 1500 |
| `render_rounds` | integer ≥ 1 | 2 |
| `custom_blocks` | `builtin_first`, `free` | `builtin_first` |
| `mcp_tools` | `core`, `all` | `core` |

- `main_metric`, `direction` (`min`/`max`), `seed_key` (e.g. `config.seed`) and `domain` (`ml` or
  `simulation`) have no default; set them and the guide names them.
- The keys guide agents; nothing enforces them.
- `proposal_words` counts statement, rationale and prediction descriptions; `beamtime proposal set`
  warns beyond it and still writes.
- `mcp_tools: core` lists the core tools plus `tools_more` (views, blocks, run control, export, scripts);
  `all` lists every tool; see the [MCP tools](../reference/mcp.md).
- An unknown key or value falls back to the default; `beamtime settings` and `beamtime doctor`
  report it.
- After a change, `beamtime setup` offers to rewrite the rules block.

## Themes

A theme recolors the layout; fonts, sizes and spacing stay. List only the colors you change, as
`#rrggbb`:

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

Colors are `paper`, `surface`, `line`, `border`, `ink`, `muted`, `accent`, `good`, `bad`, `warn`
and `data-1` to `data-6` (the runs). Save it in `themes/` next to `beamtime.yaml` or in
`~/.config/beamtime/themes/`; one file serves both modes, or name a pair `<name>-light.json` and
`<name>-dark.json`. Then `beamtime set theme atom-one`.

## Colormaps

Each chart picks its colormap in its settings (the sliders icon); "Use this on all charts on this
page" applies it page-wide, and "Save as view" keeps it (`colormap:`). The choices are matplotlib
colormaps, sequential (`viridis`, `magma`, `Blues`, ...) and diverging (`coolwarm`, `RdBu`, ...). By
default categories use the theme's palette and many numeric values use viridis; a chart with one
curve per run keeps each run's color until you choose "Color by" or a grouping.

## Figure style

PDF figures use matplotlib styles: SciencePlots names like `science` or `nature`, or `.mplstyle`
files in the project, e.g. `figure_style: [science, styles/paper.mplstyle]`.

## Remote machines

`remotes.<name>` has `host`, `command`, `path` and, in your own settings file, `enabled`. With
`enabled: false`, `serve`, `status` and the listings skip a project remote you don't use
(`beamtime setup --skip-remote lab-gpu` writes it):

```yaml
# ~/.config/beamtime/settings.yaml
remotes:
  lab-gpu: {enabled: false}
```

See [Remote machines](remotes.md).

## Environment variables

| Variable | What it does |
|---|---|
| `BEAMTIME_LOGDIR` | where runs go, for a script or job (e.g. scratch on a cluster) |
| `BEAMTIME_CACHE` | the index cache; default `~/.cache/beamtime/` |
| `BEAMTIME_RUNTIME` | runtime files (process records, the address of a `memory` serve); default `<tmp>/beamtime-<uid>/`, owner-only (0700) |
| `BEAMTIME_PROPOSAL` | a proposal for runs that don't pass one to `init()` |
| `BEAMTIME_HIDDEN` | `1` starts runs hidden until `beamtime run promote` |
