# Changelog

## Unreleased

- **Fixed** `beamtime setup` finding Beamtime on a remote: the probe now tries a venv (`.venv`, `venv`, `env`)
  in or above the remote log dir, the `PATH`, `~/.local/bin`, venvs below home or `$SCRATCH` and conda
  environments; a machine is probed again once its log dir is typed, and the command found is written to the
  user settings (`--remote-command NAME=COMMAND`), where before a venv's Beamtime was found but not kept.
  `beamtime source add` uses the same probe.

## 0.3.1

- **Added** `beamtime importance <group> --target <field>` and the `importance` MCP tool: one row per config
  field with its Spearman rank correlation, η² on quantile bins and the number of runs the row rests on, ordered by
  η²; below ten finished runs with the target the answer is a notice instead of numbers. `importance` is a query
  kind, so `beamtime query` answers it too.
- **Added** the `importance` view block, compiled to the same query, so the UI and MCP show the same numbers.
- **Added** the `script` MCP tool (family `scripts`, through `tools_more`) and `beamtime script` (code on stdin):
  for MCP clients without a shell; runs Python in a child `python -I` of the
  serving interpreter, in the project root, with `bt` preloaded, a timeout (60 s, at most 600 s) and capped output.
  Every non-user-only operation is a function in `bt` whose answer is a plain dict, so an agent joins, filters and
  formats several answers in one call. There is no OS sandbox: the code has the user's rights, like `serve`.
  `script` is not an API method, so the web UI, custom blocks and remotes cannot run code.
- **Added** `from beamtime import bt`, the namespace agents with a shell use to join and format answers. Reads are cached
  in `.beamtime/bt-cache/` of the project for five minutes; writes drop the cache, and `status`, `wait`, `resume`
  and `logs` are never cached.
- **Added** a `candidates` section to `beamtime block list <group>`: the custom blocks of saved views (the whole
  log dir is scanned) that several views use with the same declared queries, or, without queries, the same code, each
  with its group and the `block promote` command.
- **Added** the MCP tool reference, `docs/reference/mcp.md`, generated beside `docs/reference/cli.md` by
  `docs/site/reference.py` (a test checks it is current).
- **Changed** the agent guide: its rules state ops-first, the operations compute the statistics and Python joins,
  filters and formats the answers they return; a new topic covers scripts.
- **Changed** `beamtime block check`: query-less custom blocks count as duplicates only when their code is equal.
- **Removed** the benchmark's `script` arm and its Gaps section: with a shell the agents joined answers through Bash
  as cheaply, and behind `tools_more` the tool can no longer be hidden from the `mcp` arm (`bench/agents/README.md`).
- **Fixed** `beamtime serve`: a SIGINT or SIGTERM during startup is no longer lost; serve stops instead of serving on.

## 0.3.0

- **Added** `beamtime ps` (user-only): lists every Beamtime process of this user on this machine by kind: `serve`
  (web UI), `index` (`serve --no-ui`), `remote` (`serve --stdio`), `mcp` (with its client's name) and `ssh` (logins
  kept open for the remotes `beamtime setup` configured). Each row shows root or log dir, pid, URL (with token),
  cache, uptime and, for serves, whether this directory's CLI and MCP calls use it. Records of processes that died
  are printed once as stale and removed. Every long-running process registers itself under a held lock in the
  runtime base (`<tmp>/beamtime-<uid>/procs/`), so liveness never relies on the pid; `BEAMTIME_RUNTIME` moves the
  runtime base (tests and shared machines). `ps --json` gives the same rows.
- **Added** `beamtime stop [<root>|<log dir>|<pid>|--all]` (user-only): stops serves only, through the token with
  SIGTERM as the fallback, and never sends SIGKILL (it prints the `kill -9` command when a serve keeps running).
  MCP, remote and ssh processes are listed by `ps`, never stopped. A pid no Beamtime process has exits 4; a root
  without a serve says so and exits 0.
- **Added** `beamtime serve --replace`: stops the running serve of the root like `beamtime stop`, then starts as
  usual, trying the old port first.
- **Changed** `beamtime serve` for a root that already has a serve prints "Beamtime already serves <log dir>
  (pid N) at <URL>" and exits 0 instead of failing (`--open` opens that URL); it exits 1 with a hint to `--replace`
  when the running serve cannot give what was asked (a UI from an `index` serve, other explicit sources). Scripts
  that relied on the failure check `beamtime ps --json`.
- **Changed** `serve --no-ui` stops cleanly on SIGTERM instead of being killed without cleanup.
- **Fixed** with `cache: memory`, a CLI or MCP call while a serve runs answered from an empty index: reads now go
  through the running UI serve, and a memory index never skips its catch-up because a daemon runs.
- **Fixed** a query on a log dir the index had not caught up with (a first call within the 200 ms budget) answered
  from the runs it had indexed and left the others out: `series` missed curves and windowed fields were empty.
  A query now ingests the streams of every run it reads, whatever the budget; "N runs not yet indexed" counts
  only runs the answer didn't read.
- **Fixed** a promotion, rename or note written while the index read that run (or within one clock tick of
  the folder's last change, common on Linux) could stay unindexed until the run changed again: a promoted run
  kept counting as hidden in its group. The index now reads a run's times before its files and reads a
  folder changed in the last 2 s again on the next catch-up.
- **Added** `run.started` as an alias of `run.created_at` in `select`, `sort` and `where` (the column keeps the name
  as typed), and a bare `metric.<key>` means `metric.<key>.last`; a key whose last segment is a statistic's name
  still needs the explicit `.last` (`metric.loss.min.last`).
- **Added** the run-table fields `metric.<key>.nonfinite_step` (the first step with a NaN or infinity) and
  `metric.<key>.rise_step:<k>` (the first step above k times the lowest finite value before it, or non-finite;
  `rise_step` alone is k = 10), usable in `select`, `where`, `sort` and `to`; they are empty for a run where it
  never happens, and `rise_step:0` or `rise_step:x` is an error naming the form.
- **Added** step-reference windows: `metric.<a>[<b>.<step stat>]` (step stats `min_step`, `max_step`, `last_step`,
  `nonfinite_step`, `rise_step:<k>`) is the value of `a` at that step of the same run, or its last value before
  it, e.g. `metric.train/loss[val/loss.min_step]` for the training loss at the best validation step; empty without
  a step, a point or a metric. Numeric windows `[10:20]` work as before.
- **Changed** the error for a group given as `note add` evidence shows an example of each form, built from the
  group, and lists the group's prediction names.
- **Changed** `status` answers the root memory's text with its version (`memory: {version, notes_since, text}`), and
  `beamtime status` prints it below the table: one call starts a work session. `memory_show` stays for older
  versions and the chain.
- **Changed** a command line usage error (unknown flag, missing required flag, bad value) prints the command's whole
  help to stderr before the error line, so `--help` is not needed upfront; exit code 2 and `--help` are unchanged.
- **Changed** the agent rules block (`beamtime setup`, `mcp install --instructions`) starts a work session with
  `status` and sends a question about data straight to the narrowest tool, says a usage error prints the help, and
  holds a table "question -> tool or field" including `min_step`, `nonfinite_step`, `rise_step` and step-reference
  windows. The MCP instructions say the same and give the new series fields as examples.
- **Changed** the MCP tool list is smaller: the `where` operators, field examples, `from`/`group`/`depth` and `to`
  are written once in the server instructions instead of in every schema, and the tool definitions with the
  instructions come to 11.4k characters instead of 14.2k. Every tool keeps every parameter (`depth` is now typed
  as an integer; leave it out for all levels).
- **Breaking:** a series CSV export (`series --to out.csv`) is wide: the header is `run, name, step, <y1>, <y2>, ...`
  (the `by` labels instead of `run, name` for grouped curves; a metric as `x` adds its own column after `step`), with
  one row per run and step where any metric was logged and empty cells where one has no point; downsampled curves add
  `<y>.lo`, `<y>.hi` and `<y>.n` per metric. It was one row per curve point with `metric`, `x`, `y` columns. JSON
  exports keep their layout. Every export answer (CLI and MCP) lists the file's `columns` and its `first_row`; the CLI
  prints them on two lines after the path.

- **Added** `beamtime view data <draft> <file>` (MCP `view_data`): copies a CSV, JSON or Parquet file from inside the
  project into the draft's `data/` and answers its columns, row count, first rows and the `data_table` and custom
  `file` query snippets to paste. A file outside the project is refused with the `cp` command to run, an unknown
  format or a file over 16 MB is an error, one over 2 MB a warning; the same name with other content is refused.
- **Added** the guide topic `beamtime guide data-files`: one recipe from a table of your own to a saved view (copy it
  in, show it in a `data_table`, draw it in a custom block), the rules and every finding with its fix; the example
  `view new <group> --from data` shows a data file in a table and in a chart.
- **Added** a `columns` parameter on the `file` query (a custom block's data file query) to choose and order its
  columns, and a `columns` setting on a `data_table` with a `file`; a wrong column name is a finding listing the
  file's columns, and `columns` on a table of logged data (a `key`) is an error.
- **Changed** the `file` query reads tables reliably: an empty CSV cell is `null`, and a semicolon- or
  tab-separated CSV, an empty or duplicate column name (usually a pandas index) and a row with the wrong number of
  cells are errors that say how to write the file (`df.to_csv(path, index=False)`).
- **Fixed** a custom block's `file` query was not copied with the view: `view save`, `view new --from` and
  bundles now copy every data reference (`data_table` files, custom code and custom
  `file` queries) once under its content hash, so the saved page shows what the draft showed. A custom `file` query
  with keys other than `path` and `columns` is a schema error (it was dropped silently). The validator checks each
  data reference once with a fix per mistake (a file outside the draft, a missing file, an unknown format, a file too
  large, a wrong column) and skips `$placeholder` paths.
- **Changed** kit charts given data that is not a `bt.useData` result show an error instead of an empty plot.
- **Changed** the MCP server lists 19 core tools and `tools_more`: about 3.3k tokens of definitions instead of
  about 5.8k for all 43 tools. The tools for views, blocks, run control and export are reached through
  `tools_more`: `tools_more(family="views")` describes a family, `tools_more(tool="view_show", args={...})` calls
  any tool, core tools included, with the same validation and errors as a direct call. Calling an unlisted tool
  directly still works. Claude Code 2.1.322 does not reload the tool list after a change, so the listing never
  changes and `tools_more` is a dispatcher, not a switch.
- **Added** the setting `agent: {mcp_tools: core | all}` (default `core`). `all` lists every tool directly and
  leaves out `tools_more`. The guide's topics that call a family tool say to call it through `tools_more` under
  `core`.
- **Changed** a bare `beamtime guide` prints a short index: one line per topic and the defaults, and nothing
  else. Read the topic you need with `beamtime guide <topic>`; the view guide is `beamtime guide views`
  (was `overview`). Every topic stays listed in the index.
- **Added** the CLI takes MCP tool names as commands: `beamtime memory_show` runs `beamtime memory show`, so an
  agent that copies a name from the MCP listing runs it. A command that needs a log dir and finds none names
  `--root <project>` in its error.
- **Changed** the parameters of `keys`, `groups`, `runs`, `series`, `data` and `timeline` are their query structs
  plus `cursor`, `to` and `smooth`, so MCP tool schemas list the properties in the query's order (`from`, `depth`,
  `where`, then the kind's own fields, then `cursor`/`to`; `logs`, `wait` and `diagnose` list `cursor` after
  `where`), and `series` documents `seeds` like `runs` does.
- **Changed** `seeds` is a field of the `runs` and `series` queries only; on `keys`, `data`, `timeline`,
  `groups` and `importance` it was silently ignored and is now an error naming the kind's fields.
- **Changed** `logs` groups failed runs by the error the run's card recorded when there is one, and by
  the output's traceback otherwise (before: the traceback first). `wait`, `diagnose` and `logs` read run
  facts from the index instead of each run's files; `diagnose` checks the metrics file itself before it
  calls a running run stalled, so a lagging index never makes a live run look stalled, and no
  longer calls a running run stalled that has not logged a metric yet.
- **Added** the run fields `run.attempts` (how many attempts a run recorded) and `run.last_logged` (when it
  last wrote a metric), for `--where`, `--sort` and `--select`. The index cache rebuilds once (schema 3).
  The CLI text shows `run.last_logged` as its age (`3m ago`); `--json` and MCP keep the epoch.
- **Fixed** `beamtime export --html` and `--figures` printed a `KeyError` instead of the line naming the page
  they wrote. Every operation declares the kind of its answer and the text renderer for it in the
  operation set, and a test calls each read operation to check its text.
- **Fixed** the MCP instructions named only eight of the eighteen user-only commands; they now list every
  one, generated from the operation set. Which operations federate and which accept targets from one
  source only is declared on the operation (`listing`, `one_source`) and no longer repeated in the
  remote code.
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
- **Changed** a saved view leaves out every line-chart setting equal to its default, the same on
  both paths: `view save` from a draft no longer keeps an authored `smooth: 0`, as saving from the
  web UI never did. The only saved files that differ are views that spelled a float default out;
  `scale` stays explicit.
- **Changed** how answers name a source: `.` for this machine and `@name` for a remote, everywhere.
  `by.source` of federated `series` curves was `local`/`box` and is now `.`/`@box`;
  `meta.sources[].name` and `status`'s `sources` say `.` where they said `local`; `meta.source` of
  an answer from this machine is `.`. Views and agents that compare with `"local"` should compare
  with `"."`.
- **Changed** a merged listing whose source cut its own answer now says so at the top: `meta.cut`
  and the hint `narrow from or where to see all of @<name>`, which the CLI prints in place of
  `--limit to see more` (a limit would not show an old remote's budget or the size cap).
- **Added** a drawing envelope to every `series` curve: `x`, `y` and, unless the curve is raw, `lo`,
  `hi` and `n` (a downsampled curve gets `y` = `last`, `lo` = `min`, `hi` = `max`, `n` = `count`; a grouped
  curve `y` = `mean`). The web UI, `serve`'s HTTP API, `serve --stdio` and the kit keep the old fields next
  to it, so kit v1 blocks and older hubs read the same answers.
- **Breaking:** `series` answers of the CLI (`--json`) and MCP carry the envelope only: `last`, `min`,
  `max`, `count` and, for grouped curves, `mean` are gone from every curve (read `y`, `lo`, `hi`, `n`;
  `first`, `raw` and `width` stay). The answer is about 40% smaller and a page holds more curves. This
  holds for calls answered through a running `serve` or over ssh too. The web UI, `serve`'s HTTP API and a
  remote's answers keep the old fields, so older clients and older remotes still work.
- **Breaking:** `beamtime series --to out.csv` writes `y`, `lo`, `hi`, `n` and no longer `last`, `min`,
  `max`, `count` or `mean`; a `.json` export is stripped the same way.
- **Added** `y`, `lo`, `hi` and `n` to the curves custom blocks read (`bt.subscribe`, `data.curves`), beside
  the kit v1 fields `min`, `max`, `last`, `mean` and `count`, which stay. The web UI draws from the envelope alone.
- **Changed** the one-line curve summary of `beamtime series` reads the envelope: a grouped curve's
  min and max now come from its band (`lo`, `hi`) instead of repeating the mean.
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
- **Added** hidden runs for test runs that should not count: `beamtime.init(hidden=True)` or `BEAMTIME_HIDDEN=1`
  records the run as usual, but `runs`, `keys`, `series`, `groups`, `status`, the group tools, the web UI's tables,
  charts and tree, and every prediction, check, plan progress, proposal freeze and `ref` leave it out. A run named
  by id is always shown, so `card`, `output` and the run page still work for it. `--hidden` on a listing (and
  `hidden: true` in a query) shows hidden runs too.
- **Added** `beamtime run promote <run>...` (MCP `run_promote`): makes hidden runs count like any run from then on,
  and writes a `visibility/` file next to the run. It takes runs, never a group; runs that were not hidden are
  reported, not an error. The web UI has the same as a Promote button on a hidden run and on `?hidden`, which lists
  the group's hidden runs; the group header says "N hidden".
- **Changed** `status` counts visible runs and adds a `hidden` line with the number of hidden runs; when some are
  older than 7 days it lists up to five ids with the command to promote them. A hidden run that was started
  again keeps its visibility.
- **Added** `heartbeat_age_s` on the card of a lost run: the CLI says `lost (no heartbeat for 7 min)`, the run
  header and drawer say the same.
- **Added** one seed rule: `keys.config.seed` names the seed key a group varies, as the default view, the viewer's
  "mean over seeds" and validation find it. A config field named `seed`, `random_seed` or `rng_seed` counts,
  nested ones included.
- **Changed** a metric's direction (lower is better) comes from whole name tokens (`loss`, `error`, `rmse`, ...),
  not from substrings: `power` is higher-is-better now.
- **Changed** failure signatures ignore paths and quoted strings and read a bare exception line (`ValueError:`
  alone) with the line before it, so the same failure groups together in `logs`.
- **Breaking:** the index cache is schema 4 and rebuilds itself on first open; the `groups` columns end with `hidden`
  (read them by name).
- **Breaking:** `status` run counts are visible runs only; hidden runs appear in their own `hidden` entry.
- **Breaking:** a metric whose name contains a lower-is-better word only as a substring is now higher-is-better.
  Set `metrics: {power: {higher_is_better: false}}` in a view to keep the old direction.
- **Breaking:** the default view and "mean over seeds" use the one seed key of the group (`seed`, `random_seed`,
  `rng_seed` or the config field `seed`) instead of `config.seed` only; name `seeds:` in a view to pin it.
- **Breaking:** failure signatures replace paths with `<path>` and quoted strings with `<str>`, so a signature no
  longer matches one written by 0.2.

**UI refinements** (the charts, the sidebar, the look, and what agents are told about type):

- **Added** a metric a running run has just logged charts at once, and a chart whose runs are running but have
  not logged a value yet says "Waiting for the first value of <title>." instead of an error. A live key is a known
  key for `series`, `data`, `runs` and `where` (`runs` and `where` read the run card's value, which lags the
  stream by a moment), and the `series` meta gains `running` (summed across sources).
- **Added** the sidebar opens and closes at every level: the chevron is a 24 px wide, full-row target, a click on the
  name of the current group toggles it, and the ancestors of the current group open once on navigation. While the
  filter has text, every match is shown expanded and the chevrons are inert.
- **Added** a Markers setting on line charts (`markers: auto | on | off`, default `auto`): `auto` marks every point
  of every curve when the shown curve with the most finite points has at most 30, `on` always, `off` never; a curve
  with a single point is marked in every mode. It was decided per curve and flickered.
- **Changed** hiding a run shrinks the x axis to the shown curves; a zoom still wins.
- **Added** "Color by" offers run fields (`status`, `tags`, `name` and the folder, as `run.group`) next to the
  varying config keys, and lists the keys that vary together ("`<key>` · same split as `<canon>`") and the keys
  Beamtime dropped because another determines them ("`<key>` · set by `<finer key>`"), all selectable. The `keys`
  answer gains `config.dropped` (key -> the key that determines it), and a merged answer lists a key that varies
  somewhere as varying.
- **Added** the default view colors a sweep's charts by its one swept key (no merged seeds, exactly one varying
  config key besides the seed). "Color by -> none" undoes it.
- **Changed** sections accept `val/`, `val.` and `val_`: `/` always separates, `.` and `_` separate after a known
  prefix (`val`, `valid`, `eval`, `test`, `validation`, `train`, `training`, matched case-insensitively), and a
  prefix with a single metric keeps its own section. A viewer's open or closed state of sections that moved resets.
- **Changed** the log scale comes from the values: a chart without an explicit `scale` is log when every finite
  value is positive and spans more than two decades, else linear (it was log for any name with `loss`). A live loss
  that crosses two decades turns log. The y-scale control shows the resolved scale; an explicit `scale` in the
  block, the view's `metrics` or the viewer's choice wins.
- **Changed** clocks come from the leaf of a metric's name (`epoch`, `step`, `global_step`, `iteration`, `iter`
  after `/` or `.`): they get no chart and are offered as x axes under "Progress". A view can still chart one by
  naming it. `run.progress` stays on the `epoch` metric.
- **Changed** the default view merges seeds when `config.seed` varies and some arm (the runs sharing every other
  varying key) has two or more seeds, instead of above 8 runs. "Each run" in the chart settings undoes it.
- **Added** logged images step through every logging: a scrubber under the images (stops are the logged steps;
  arrow keys, Home and End), "by step / by epoch" when the page has a clock, and a run without an image at the
  scrubbed step shows its latest earlier one, muted and labelled with its own step. A view's `step:` is where the
  scrubber starts; live updates follow the last stop until the viewer moves it.
- **Added** the images block is a chart frame: download gives the original file of each image (inline "Latest
  image" and "All images (n)", and "This image" and "All images" in the dialog), and a click or Expand opens a large
  dialog that zooms (wheel, pinch, `+`/`-`), pans, resets on double-click and steps to the previous or next run.
- **Added** the `data` query takes `clock: <metric>` and `step: ["last", s]` (CLI `--step last:S`: each run's latest
  entries at or before step `s`), and its meta lists `steps` (every step at which a run in scope logged the key) and,
  with a clock, `clocks`.
- **Added** the top bar and the favicon carry the `///` mark: it gathers to the left on hover and on page load
  (420 ms; a jump under reduced motion), and the live favicon (`favicon-live.svg`) is drawn gathered. A data table
  says when rows are hidden, and a render mounts every chart before the screenshot.
- **Changed** the look: cool neutral grays, a centered column of at most 1120 px, Section labels in mono above the
  content, sans titles, panels for sub-groups and stats, rows with a rounded hover tint, 12 px corners and drawn
  checkboxes, ranges, selects and number fields. Serif is only for what people and agents wrote, sans for what
  Beamtime names, labels and counts, mono for ids, keys, code and section labels. Themes recolor through the same
  tokens; custom blocks keep `var(--margin)`, which the app no longer uses. The agent guide and the spec follow.
- **Added** the guide topic `beamtime guide type` (also in the `beamtime-views` skill): which type class to use for
  each kind of text in custom blocks and views. `view_validate` rejects font literals in custom code (`font-size`,
  `font-family`, `fontSize`, `fontFamily`, `line-height`, `lineHeight`, the `font` shorthand and an assigned
  `.font = "<literal>"`, comments masked) as an error `font literal ...`; font weight stays allowed, and canvas
  code uses `bt.theme.tokens.font`.
- **Fixed** `beamtime serve` could crash with a segmentation fault when a page's first requests arrived together:
  two threads set up the same request type at once. The serve (and `serve --stdio`) now sets up every request type
  at startup, which adds about 0.8 s to it. A page whose serve died this way showed charts that never loaded.
- **Fixed** an images block on a group page could show step 0's images for every run when its first answer came
  back quickly; it now settles on the step the viewer picked.
- **Changed** the size limits to fit this: the chart kit may be 50 000 bytes compressed (was 48 000) and the MCP tool
  definitions with the instructions 12 000 characters (was 11 500).
- **Breaking:** the default chart scale is log when every value is positive and spans more than two decades, no
  longer for names with `loss` (set `scale:` in the view or the view's `metrics`); sections, clocks, seed merging
  and sweep coloring follow the rules above (Color by -> none and "each run" undo the last two); the `images`
  block's `step:` is now where the scrubber starts; `view_validate` reports font literals in custom code as errors
  (use a type class, see `beamtime guide type`). The `keys` answer's `config.dropped`, the `series` meta `running`
  and the `data` query's `clock`, `step: ["last", s]` and meta `steps` and `clocks` are additive.

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
