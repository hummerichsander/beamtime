# Changelog

## Unreleased

- **The design system**: the web UI, docs site and exports follow Beamtime's design system
  (`docs/design.md`): pages as columns of Sections with margin labels, the proposal right after the
  header, XCharter and IBM Plex shipped with the frontend, runs drawn in a color and a line style.
- **Themes**: a theme file now changes colors only, by the new token names (`paper`, `ink`, ...).
  `extends`, `data`, `fonts`, `sizes` and `shape` are gone; older theme files need rewriting.
- **Custom blocks**: CSS variables are now `--ink`, `--muted`, `--line`, ...; `--bt-*` is gone, and
  `bt.theme.tokens` has the new shape. Added `bt.theme.runDash(id)`.
- **Fixes**: with a remote configured, the light/dark switch and the other settings on the settings page
  snapped back, because a new setting never reached the next page load; `beamtime.yaml` is now replaced
  atomically, so writes at the same moment can't corrupt it.
- **Sidebar**: hosts have a symbol and collapse, the local one too.
- **Colormaps**: matplotlib's colormaps color numeric groups and heatmaps; choose them with the
  `colormap` and `colormap_diverging` settings.

## 0.1.0

The first release.

- **Logging**: `beamtime.init()` and `run.log()` record metrics, config (dicts, dataclasses,
  Pydantic, argparse, OmegaConf), output, crashes, signals and resumes as plain files; images,
  tables, text and histograms; artifacts and checkpoints; hardware and system metrics; git state.
  Only rank 0 records under torchrun, SLURM and Lightning. The SDK needs Python 3.10 and PyYAML.
- **Clusters**: SLURM jobs, preemption and requeue; runs that stop sending updates show as lost.
- **Looking at runs**: `beamtime runs`, `series`, `card`, `output`, `timeline`, `keys`, and a query
  language with filters, seeds and windowed metric statistics.
- **Proposals and verdicts**: versioned proposals frozen once runs record them, plans, predictions
  checked with t-intervals, notes, verdicts, a group status, and a memory for agents.
- **Web UI**: `beamtime serve`, live while runs train; charts with zoom, smoothing, grouping and
  downloads (PNG, CSV, PDF in your matplotlib style); notes and texts edited in place.
- **Views**: pages agents build from blocks, custom blocks in a sandbox, and library blocks shared
  between groups and projects.
- **Agents**: an MCP server with the same operations as the CLI, prompts for the research loop,
  and `--instructions` for Claude Code, Cursor and Codex. Agents add; they never delete or move.
- **Remote machines**: a cluster's runs next to yours over ssh, live; read-only snapshots for when
  it's away.
- **Export**: a page as a folder that opens from disk (`beamtime export --html`), and its charts as
  figures for a paper (`--figures`).
- **Lightning**: `BeamtimeLogger`.
