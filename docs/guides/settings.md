# Settings

Settings live in two files; the project's file wins, and command-line options win over both:

- `~/.config/beamtime/settings.yaml`: yours, for every project.
- `beamtime.yaml` in the project: for this project, shared through git.

```yaml
logdir: beamtime                 # where runs go, relative to the project
theme: beamtime                  # the web UI's theme
theme_mode: system               # light, dark or system
colormap: viridis                # for numeric groups and heatmaps
colormap_diverging: coolwarm     # the same, for values around a center
figure_style: [science, nature]  # matplotlib styles for PDF figures
remotes: {}                      # see Remote machines
```

```sh
beamtime settings                 # what is set, and where it comes from
beamtime set theme_mode dark      # change one setting of the project
```

The browser's settings page changes the same values.

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

Numeric groups and heatmaps are colored by matplotlib's colormaps; individual runs keep their own
colors and line styles. Choose them on the settings page or with `beamtime set colormap magma`.

- `colormap`: `viridis`, `plasma`, `inferno`, `magma`, `cividis`, `turbo`, `Blues`, `Greens`, `Greys`,
  `Oranges`, `Purples`, `Reds`.
- `colormap_diverging`: `coolwarm`, `RdBu`, `bwr`, `seismic`, `PuOr`, `BrBG`, `PiYG`, `RdYlBu`, `Spectral`.

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
