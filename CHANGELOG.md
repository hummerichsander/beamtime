# Changelog

## 0.3.0 (unreleased)

- **Fixed** `wait` and `compare` over a remote: `wait` no longer turns a status into a path
  (`changed[].from` stays `running`, not `@box/running`), and `compare` names its targets as
  `@box/...`. A path an answer carries as `@local/...` now maps onto the remote (`@box/...`)
  instead of nesting as `@box/@local/...`.
- **Fixed** `runs --by` and `--seeds` over several sources: the rows keep each source's own order
  (no re-sort by creation time) and a `source` column says where each group comes from. A merged
  run table cut at its limit now says so (`meta.cut`), with `meta.shown` counting every source.
- **Fixed** paging of listings over several sources: the cursor is applied once to the merged
  answer, so following `meta.next` lists every item of every source once, local first: every source
  answers whole (bounded by the `limit` and about 2 MB, asked by a `whole` flag on the request line
  that older remotes ignore), and only an old remote or an answer over the cap says so in
  `meta.sources[].cut`. `meta.groups` and `meta.means` are
  summed over the sources, like `meta.matched`.
- **Changed** how answers name a source: `.` for this machine and `@name` for a remote, everywhere.
  `by.source` of federated `series` curves was `local`/`box` and is now `.`/`@box`;
  `meta.sources[].name` and `status`'s `sources` say `.` where they said `local`; `meta.source` of
  an answer from this machine is `.`. Views and agents that compare with `"local"` should compare
  with `"."`.
- **Changed** a merged listing whose source cut its own answer now says so at the top: `meta.cut`
  and the hint `narrow from or where to see all of @<name>`, which the CLI prints in place of
  `--limit to see more` (a limit would not show what a source's budget left out).
- **Fixed** a data file's `path` over a remote: it stays relative to the view (it was prefixed
  with `@box/`), and a table column called `path` in a logged file is no longer prefixed.
- **Changed** how a run is named in `from`: one resolver answers for queries, writes and notes. A
  run is found by its id, else (when no group of that name exists) by a unique id suffix (four
  characters or more) or its name, and an unknown group lists the top-level groups. The message
  for an unknown source now names the configured remotes, like the CLI's.
- **Changed** run arguments and web pages resolve through the same resolver: `card`, `output`, `mv`
  and `rm` take a run id, a unique id suffix of four characters or more, or a name (one- to
  three-character suffixes matched runs by chance and are no longer accepted), and a page URL
  naming a reserved folder (`proposal`, `notes`, ...) is refused. A run page opens by unique id
  suffix, and an unknown group on a page lists the top-level groups.

## 0.2.2

- **Fixed** a crash in the live-update hub when a stale page (an older tab left open) sent a watch
  request in an earlier shape: the entry is skipped now instead of taking the hub down.
- **Steadied the browser tests** under CI load: the shared Playwright page fixture gets a longer
  default timeout, and matplotlib's font cache is warmed once per session so a view render's
  settle budget isn't spent building it. Test-only; nothing ships differently.

## 0.2.1

- **Fixed** the `synth` byte-stability test on Windows: it hashed `str(path)`, whose separator is a
  backslash there, so the digest never matched. The generated files were always identical across
  platforms; the test now hashes the posix path.

## 0.2.0

Charts, sources, the run lifecycle and the agent tools, after the first end-to-end tests. Logged runs,
notes, proposals and views keep working as they are: every file on disk still reads, and new fields in
`_run.json` and notes are optional.

**Breaking, with what to do:**

- **`series` with `by` or `seeds` and an `x` other than `_step`** now returns the real x values
  (bucket centres) instead of steps. The old answer was wrong; nothing to migrate.
- **`seeds` grouping** groups by the distinguishing config keys minus the seed, instead of the whole
  config minus the top-level seed, so curves that used to stay apart because of nested aliases or a
  timestamped `default_root_dir` now merge, as they should.
- **Default view**: sections by metric prefix (`train/*`, `val/*`, ...) replace the essential grid and
  "More metrics". Saved views are untouched.
- **Main metric** is no longer guessed from names. Pin charts in the UI; the proposal's predicted metrics
  are the default pins. "Save as view" writes them as `main_metrics:`, and without a proposal or pins
  there is none. A view from before has its first `metrics:` entry as its main metric.
- **`init()` on a SLURM requeue** continues the job's only run in that folder instead of starting a new
  one. Give runs that must stay separate their own `key` or `name`. A job with several runs in the folder
  starts a new run with a warning.
- **Chart `added` pref** now comes with `removed`; old prefs still read.
- **Colormap settings are gone**: `colormap`, `colormap_diverging` and `beamtime set colormap` no longer
  exist (0.1.1 introduced them). A colormap is chosen per chart in its settings, or for the page with
  "Apply to all charts", and "Save as view" keeps it. An old settings key loads with one problem line.
- **`/` with no local log dir** opens the first source instead of failing.
- **Remote view operations** (`view_*`, `block_*`) work through ssh; the remote needs Beamtime 0.2 or
  newer for them. Upgrade the remote.
- **`git.dirty`** also counts untracked files. Old files read as before.
- **`view render`** writes `.jpg` instead of full-page `.png`, page shots are capped at 2520 px with
  `cut` naming what lies below. Read `shots[].file` rather than assuming a name.
- **Lightning**: SLURM auto-requeue never worked alongside `BeamtimeLogger` before 0.2.0. It does now,
  and a Lightning requeue records no `requeue_requested` event.

What's new:

- **Charts**: every chart shares one frame (settings beside the chart, legend, downloads, Expand), with
  axis titles, a truthful x axis from the server (any logged metric, wall clock, elapsed, epoch; never
  interpolated), single points drawn, correct bands in log mode, and nested hyperparameters resolved.
- **Run lifecycle**: resume after a wall-time limit, `beamtime cp`, code versions in tables and groups
  (also untracked files), attempts, time limits and checkpoints in the UI.
- **Sources**: a remote alone is enough, views and blocks work on remotes, and links on a remote's pages
  name the remote.
- **Custom blocks**: `bt.chart.Figure` and the app's vocabulary in the kit, a built-in scorecard block,
  validator lints for captions, titles and headings, and live updates for custom charts.
- **Agents**: the guide by topic (`beamtime guide <topic>`), generated skills for `mcp install --skills`,
  the `bench/agents/` harness, and new tools: `compare`, `digest`, `logs`, `wait`, `diagnose`,
  `plan missing`, `runs --by` and `--to FILE`.
- **Notes** have a `theory` label, editable in the UI; the favicon shows live runs.

## 0.1.1

The web UI's new look, built from a design system that now lives in `design/`. Logged runs, notes,
proposals and views keep working as they are.

**Update by hand**, if you use them:

- **Custom blocks**: CSS variables are now `--ink`, `--muted`, `--line`, ...; `--bt-*` is gone, so a
  saved block that uses it draws in black until it has a new version. `bt.theme.tokens` has a new
  shape: colors are in `colors`, by the new names. `bt.theme.scale`, `runColor` and `groupColor` work
  as before.
- **Theme files**: a theme now changes colors only, by the new token names (`paper`, `ink`, ...).
  `extends`, `data`, `fonts`, `sizes` and `shape` are gone; older theme files need rewriting
  ([Settings](docs/guides/settings.md#themes)).

What changed:

- **The look**: pages are columns of Sections with labels in the margin, and the proposal comes right
  after the header. XCharter and IBM Plex ship with the frontend. Each run has a color and a line
  style, the same in charts, legends and tables, with new `bt.theme.runDash(id)` for custom blocks.
- **Colormaps**: matplotlib's colormaps color numeric groups and heatmaps; choose them with the
  `colormap` and `colormap_diverging` settings.
- **Sidebar**: hosts have a symbol and collapse, the local one too.
- **Agent guide**: agents try built-in blocks first, and write a custom block only when none can show
  the result or it would look visibly worse.
- **Fixes**:
  - With a remote configured, the light/dark switch and the other settings on the settings page
    snapped back; they now stick.
  - `beamtime.yaml` is replaced atomically, so writes at the same moment can't corrupt it.

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
