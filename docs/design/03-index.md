# Layer 3: Index and query

Status: **reviewed; v1 scope per the [overview](00-overview.md#scope).** Part 1 covers the metric
store, the most performance-critical piece. Part 2 covers the query language that views, CLI and MCP
share.

The index sits between the files ([layer 1](01-storage.md)) and everything that displays them:
views, CLI, MCP. It is a cache in `~/.cache/beamtime/<logdir-hash>/`, rebuildable from the files at
any time.

## Requirements

| Workload | Target |
|---|---|
| Run table: filter and sort 10k runs by config and run card | < 50 ms |
| Chart: 50 runs × 1 metric, full range, spikes preserved | < 100 ms |
| Zoom: window into a run with 10M steps | < 100 ms |
| Live: newly logged lines visible | < 1 s |
| Exact aggregate: mean over a step window across 500 runs | < 1 s |
| One-shot CLI or MCP call, whole process | as low as possible; agents call it repeatedly |
| Full rebuild: 1000 runs, ~10^8 points | ~1 min |

Constraints: several processes (web server, CLI, MCP) read concurrently; the CLI must not need a
running server; minimal dependencies; never on cluster filesystems.

## Store

**SQLite for metadata, raw column files for metrics, read by one pure-Python implementation.**
Ingest only appends bytes, every window and aggregate is exact, and nothing precomputed needs
maintaining. Rules it follows:

1. **Min/max per bucket, never random sampling**, so spikes survive. Plain min/max is one O(n) pass.
2. **Never discard data at ingest.** Keep everything; downsample at query time.
3. **Index continuously from file contents**, not when a run finishes; crashed runs must not degrade
   queries.
4. **Fixed bucket edges**, so a growing live curve doesn't jitter between refreshes.
5. **SQLite with one writer, locally only** (WAL: many readers, one writer), never on shared
   filesystems.
6. **Imports dominate one-shot latency.** NumPy (~67 ms), DuckDB (~98 ms) and PyArrow (~116 ms) each
   cost more than a query, so the CLI path imports none of them and runs as an installed console
   script, not through `uv run`.

At scale M (1000 runs, 1.2×10^8 points) this meets every target: a one-shot CLI chart of 50 runs
takes 100–165 ms as a whole process, an exact mean over 500 runs about 0.1 s, a full build about
65 s single-process. Scripts and numbers are in `bench/index/`.

```
~/.cache/beamtime/<logdir-hash>/
  index.sqlite                           # runs, config, run cards, notes, events, data entries
  series/<run-id>/<key>.<gen>.steps      # int64, appended; <key> percent-encoded
  series/<run-id>/<key>.<gen>.values     # float64, appended
  series/<run-id>/_manifest.json         # committed length per key, source offset, attempts
  index.lock                             # held by whoever is ingesting
  serve.json, serve.lock                 # the daemon's status and its lock
```

- **Ingest** reads each `_metrics.jsonl` from the last byte offset recorded in the manifest, appends
  to the column files, then publishes the new lengths by replacing the manifest. Readers never read
  past the manifest; after a crash, column files are truncated to it.
- **Attempts.** When ingest meets an `attempt_started` event with a resume step, it truncates each
  column of that run to the points before the resume step (a binary search) and continues appending.
  Steps therefore stay sorted, and the newer attempt wins ([layer 1](01-storage.md#_metricsjsonl)).
- **One indexer at a time**, chosen by a file lock. Whoever needs fresh data takes the lock and
  catches up only on the runs it queries, at 15–30 ms per run.
- **Readers** map the column files and need no lock. A step window is a binary search.
- **One read path.** Downsampling, windows and aggregates have exactly one implementation, in pure
  Python over `mmap` and `array`, with `math.fsum` for sums, used by the CLI, MCP and `serve` alike,
  so they never disagree, not even in the last bit. A NumPy path for long zooms in `serve` would be
  tested against it.
- **Charts** split the requested window into buckets and send min and max per bucket. Bucket edges are fixed per zoom level, so live curves don't jitter. **Each chart**
  has a point budget of about 30k, which keeps charts smooth in the browser.
- **Values stay float64**, so exact aggregates are exact.

### What we don't do

- **No precomputed levels.** They could become a cache on top of the raw files if long-range charts
  over very long runs get slow.
- **No DuckDB, PyArrow or NumPy on the CLI path** (imports; DuckDB's locking also conflicts with
  concurrent readers).
- **No Rust.** Parallel ingest plus optional `orjson` is fast enough.

## Discovery

The index must learn about new, moved and deleted runs without walking the whole log dir on every
call, which on a cluster filesystem would cost seconds and load the metadata server.

- **A query walks only its own subtree** (`from`), and skips folders whose modification time hasn't
  changed since the last walk.
- **`serve` walks the whole log dir once at start**, then re-walks changed folders as it polls.
- **Runs whose folder has vanished** (deleted, moved, trashed) are dropped from the index when a walk
  no longer finds them; a moved run is found again under its new path, with the same id.

## Freshness: the daemon

The cache only learns about new lines when a process reads them in. Beamtime has one long-running
process for that, `beamtime serve`:

- **`beamtime serve`** runs the web UI, the indexer and the connections to remotes
  ([layer 4](04-remotes.md)) for one root. `beamtime serve --no-ui` runs it as a pure daemon.
- **One daemon per root.** `serve` holds `serve.lock` in the cache. A second `serve` for the same root
  attaches instead of starting: it prints the running one's URL and exits 0 (`--open` opens that URL).
  `--replace` stops the running one first, as `beamtime stop` does, and starts anew, trying the old port
  first. When the running one cannot give what was asked (a UI asked of a `--no-ui` serve, other explicit
  sources, an older version), `serve` exits 1 with the hint to `--replace`, except for an older version,
  which exits 0 with the hint since the UI works. CLI calls, MCP servers and the headless renderer
  ([layer 7](07-web-ui.md#screenshots-and-the-headless-renderer)) are clients: they read the index and
  never start a daemon.
- **While it runs**, it polls running runs for new lines (the modification time of `_metrics.jsonl`
  every few seconds, only for runs whose status is `running`) and indexes them. Finished runs are
  indexed once.
- **The CLI and MCP never depend on it for correctness.** Without a running daemon, each call catches
  up on the runs it queries within a time budget (default 200 ms), then answers. With a `memory`
  cache (the setup's `cache` setting, [setup](10-setup.md#the-cache)) the daemon's index is private to
  its process, so a CLI or MCP call cannot read it and, with a daemon running, would skip its own
  catch-up and see no runs. Instead such a call sends every operation that is not user-only through the
  running UI serve (`via_serve.call`), and a memory index never skips its catch-up because a daemon runs.
  Writes are not routed: paths and stdin are relative to the caller's working directory. If the budget was
  not enough, the answer says so: "3 runs are up to 4 min behind".
- **A query reads every run it selects in full.** Before a query opens a run's column files
  (`Columns`, the one way a query reads a run's streams), `Index.ensure_streams` ingests that run's
  streams if they are stale, whatever the budget; the budget only bounds catch-up of the runs the
  query does not read. The runs catch-up skipped are `Freshness.deferred`; `query.run` drops those it
  ingested itself, so "N runs not yet indexed" counts only runs the answer didn't read, and a second
  query ingests nothing; `behind_s` is the largest lag among the runs left. The card ingests its run
  the same way. `ensure_streams` takes the index lock and waits for it up to 30 s (a daemon
  indexing holds it), then raises "the index is busy; try again"; a run it cannot read is skipped
  and named in `freshness.damaged`.
- **Run tables and overviews stay fresh either way**: card and preview are rewritten by the run every
  3 minutes and are small enough to read directly.
- **Overview charts are answered from previews** when the requested window and point budget fit the
  preview's buckets; zooms and exact statistics use the column files. The answer's meta says which.

### Daemon status for agents

`serve.json` holds the daemon's pid, port, version, start time and a heartbeat. From that:

- `beamtime status` (and the MCP tool `status`) reports whether the daemon runs, since when, with
  which version, and which remotes are connected or unreachable.
- Every CLI and MCP answer carries a freshness line: `live (daemon running)` or
  `catch-up only (daemon not running)`.
- Agents check the status before working with live runs and, if the daemon isn't running, ask the
  user to start `beamtime serve --no-ui` ([layer 8](08-cli-mcp.md#policy)).
- To see which Beamtime processes run (and which of them this directory's calls use), agents hand the
  user `beamtime ps` ([Processes](#processes)).

### Processes

Besides the daemon, Beamtime starts a few long-running processes. `beamtime ps` lists every one of this
user on this machine, grouped by kind:

| Kind | Process | Started by |
|---|---|---|
| `serve` | `beamtime serve`, the web UI with the indexer | the user |
| `index` | `beamtime serve --no-ui`, the pure daemon | the user |
| `remote` | `beamtime serve --stdio`, the remote end of a laptop's ssh connection | a laptop's `serve` |
| `mcp` | `beamtime mcp` | an agent client |
| `ssh` | a login kept open for a remote that `beamtime setup` configured | ssh (`ControlMaster`) |

**The registry** is the folder `procs/` in the runtime base: `<tempfile.gettempdir()>/beamtime-<uid>` (mode
0700), or `BEAMTIME_RUNTIME` when set (tests, and `runtime_dir(logdir)` moves with it). It is local disk and
the one place every process of a user agrees on, whatever its `cache` setting. A process registers on
start with a lock file `<kind>-<pid>-<6 hex>.lock` it holds for its whole life, then a JSON record with
the same stem, mode 0600, and removes the record before it releases the lock. `serve` and `index` register
after the daemon has started, `remote` in `serve --stdio`, `mcp` in the MCP server. Liveness is the held
lock, not the pid: a pid can be reused, and `os.kill(pid, 0)` terminates a process on Windows. A record
whose lock can be taken is **stale** (the process was killed). `ps` prints stale records once under
"stale (removed)" and deletes them.

| Field (`schema: 1`) | Meaning |
|---|---|
| `kind`, `pid`, `ppid`, `version`, `started` | what and since when |
| `root`, `logdir` | the project root as every call of the process resolves it (the working directory outside a project; `null` when unknown) and the log dir |
| `cache`, `cache_kind` | the cache folder (with `serve.lock`, `serve.json`, `serve.token`) or the index folder; `disk`, `memory` or `temporary` |
| `port`, `sources` | `serve` only: the port and the names of its remotes |
| `client` | the MCP client's name, or the ssh peer from `SSH_CONNECTION` for `remote`; else `null` |

`ps` also scans `<disk cache root>/*/serve.json` and `runtime_base()/*/serve.json` for serves without a
record (an older release's serve: its row comes from `serve.json`, with `schema` 0; a serve with
both is listed once) and removes a `serve.json` whose `serve.lock` is free. The token stays: it
outlives restarts by design. `ssh` rows come from the Beamtime-marked blocks in `~/.ssh/config`, checked
with `ssh -O check <host>`; `ps` names `ssh -O exit <host>` to end one, because Beamtime does not stop
them.

A row shows root or log dir, pid, URL (with `?token=`, as `serve` prints it), cache and uptime. For a serve
of this context's log dir it also says whether this directory's CLI and MCP calls use it:

| Used here | Meaning |
|---|---|
| `live index, remote calls` | UI serve on the same cache: calls read its fresh index and reach its remotes |
| `live index` | `--no-ui` serve on a disk cache |
| `all reads` | UI serve with a `memory` cache: reads go through it |
| `no: memory, no UI` | `--no-ui` with a `memory` cache: nothing to share |
| `no: this shell's cache is <path> (<source>)` | the shell's cache setting differs from the serve's (`<path>` is `memory` for a memory cache) |
| `-` | other kinds and other log dirs |

`beamtime stop [<root>|<pid>] [--all]` stops serves only: a root or log dir path matches a serve's `root`
or `logdir`, digits its pid as `ps` prints it, nothing means this context's serve, `--all` every listed
serve. It sends `POST /api/shutdown` with the bearer token (handled before the registry dispatch, so it is
no operation), or SIGTERM when the serve has no port (`index`) or the request fails, and waits for
`serve.lock` to be free: 10 s after the token, 10 s more after SIGTERM, then it reports
"still stopping (pid N); `kill -9 N` ends it now" and exits 1. It never sends SIGKILL. MCP, remote and ssh
processes are listed, never stopped: a pid of one is refused with "listed, not stopped: it belongs to
<client>". A pid that no Beamtime process has exits 4 (not found); a root or log dir without a
serve prints "no serve runs for <path>" and exits 0, so stopping twice is no error. Experiment processes are not Beamtime's: it records runs, it never runs experiments. Processes on
remote machines (`ps @cluster`) and the headless renderer are not listed.

## Query language

One query language serves views (YAML), the CLI (flags) and MCP (JSON). The **object form** is
canonical: a view writes it as YAML, MCP sends it as JSON, and every CLI command maps 1:1 onto it.
An agent that learned it in one place can use it everywhere.

Design goals:

- **Small and predictable.** Few concepts, no general-purpose expressions.
- **Validated with helpful errors.** An unknown metric fails with the closest matches and a pointer
  to `beamtime keys`, instead of returning nothing. A metric only a running run's columns have yet
  (its card lags up to 3 minutes) counts as known and is among the suggestions. `runs` with
  `metric.<k>.last` and `where` on such a key read the card's value, so they read `None` until the
  card catches up, the same lag as any metric's `last`.
- **Exact by default.** Every number comes from the full data; only curves are downsampled, and the
  answer says so.
- **Token-aware.** Defaults keep answers small; larger answers have to be asked for.

### Fields

Every value a query can filter, sort or show is a **field**, a dotted path with a namespace:

| Namespace | Example | Source |
|---|---|---|
| `run.` | `run.id`, `run.name`, `run.status`, `run.created_at`, `run.duration_s`, `run.steps`, `run.tags`, `run.path`, `run.commit`, `run.branch`, `run.dirty`, `run.code`, `run.epoch`, `run.progress`, `run.attempts`, `run.last_logged`, `run.hidden` | `_run.json`, run card |
| `config.` | `config.optimizer.lr` | `_config.json` |
| `metric.` | `metric.val/acc.max`, `metric.train/loss.ema_last` | run card statistics |
| `value.` | `value.test/acc` | explicit run card values |
| `proposal.` | `proposal.status`, `proposal.check`, `proposal.progress`, `proposal.verdict` | the check and the notes ([research record](09-research-record.md#the-check)) |

`run.hidden` is true for a hidden run: `_run.json` says `hidden`, unless the newest valid version in the
run's `visibility/` folder says otherwise ([layer 1](01-storage.md#_runjson); the index stores the one
answer of `run_hidden`, and the run's authored files are watched like the others).

For `metric.`, the last segment is the statistic when it names one and everything before it is the
metric key, so keys containing dots (`metric.layer.0.grad.max`) stay unambiguous. A bare
`metric.<key>` is `metric.<key>.last`, in `select`, `sort` and `where` alike, and the column keeps the
name as typed. The one trap is a key whose last segment is a statistic's name: `metric.loss.min` is
the minimum of `loss`, so the last value of a key literally named `loss.min` is written
`metric.loss.min.last`. The statistics are the run card's: `first`, `last`, `ema_last`, `min`, `min_step`, `max`, `max_step`, `mean`, `count`,
`last_step`, `nonfinite`, `slope_last10pct`. A config key that itself contains a dot is quoted:
`config["a.b"]`.

Two more statistics are series steps, computed from the column files like windowed fields (so a query
that reads them ingests the run's streams first, see [Freshness](#freshness-the-daemon)); neither has a card
entry or an SQL expression, and neither takes a window. **`nonfinite_step`** is the first step whose
value is NaN or infinite (`null` when every value is finite). **`rise_step:<k>`** is the first step whose
finite value is greater than `k` times the lowest finite value before it, or whose value is non-finite
(`null` when neither happens); `k` is a positive finite number (`rise_step:2.5`), and `rise_step` alone
means `k = 10`. The bar is literal: with a negative lowest value `k` times it lies below the lowest
value, so any later value at or above that minimum counts as a rise. A first value that is NaN makes both
fields its own step. A `k` that is not a positive number is an error naming the form. Both are fields like
any other, in `select`, `where`, `sort` and `to`: `metric.train/loss.rise_step:10` finds where a run
diverges without exporting its curve.

A **step-reference window** reads one metric at a step of another: `metric.<a>[<b>.<s>]`, with `s` one of
`min_step`, `max_step`, `last_step`, `nonfinite_step` or `rise_step:<k>`. Its value is the value of `a`
logged at that step of the same run, or the last value of `a` before it when `a` has no point there (the
columns' sorted steps are bisected); it is `null` when the step is `null`, when `a` has no point at or
before it, when the run has no `a` or `b`, and when the value is NaN or infinite (answers carry no
non-finite numbers). The reference takes no statistic of its own (`metric.a.mean[b.min_step]` is an error), and
a reference to a statistic that is not a step (`[val/loss.min]`) is an error naming the step statistics. It is
a field like any other, computed from the columns like the series steps: `metric.train/loss[val/loss.min_step]`
is the training loss at each run's best validation step, next to `metric.val/loss.min_step` itself. A numeric
window (`[1000:2000]`) is unchanged; the two forms differ in what stands inside the brackets.

`run.created_at` is when the run first started (`init` writes it together with the first attempt's
`started_at`; a resumed run keeps it), so `run.started` is accepted as the same field. It resolves
to `run.created_at`, and a column shows the name as typed.

**`run.code`** is one comparable identity for the code a run ran on: the short commit, plus the
short diff hash (`run.dirty`'s `diff_sha`) when the checkout was dirty (`f385eda+1a2b3c4d`), so the
same commit and the same uncommitted changes compare equal across runs and checkouts. It is `null`
without a git checkout, or on a dirty run without `diff_sha`. `keys` lists a
group's distinct codes by count (only when they differ: a single version isn't a fact worth
showing), and `check` adds a note to a proposal when its members didn't all run on the same code.

**`run.epoch`** and **`run.progress`** read the `epoch` clock from the run card and the config alone:
the current epoch (the last logged value, plus 1 when the metric starts at 0, as Lightning's does)
and the share of the config's `max_epochs` completed before it. Both are `null` without an `epoch`
metric, `run.progress` also without a positive `max_epochs`. The run's card (`beamtime card`) adds
`progress`, computed exactly from the epoch column's change points
(`query/progress.py`): `epoch`, `in_epoch` and `steps_per_epoch` (the step distance between the
last two changes, so an `epoch` logged every 50 steps with 100 steps per epoch gives 100), `total`
and `fraction`.

**`run.attempts`** is the number of attempts `_run.json` records (0 when it records none), so
`run.attempts>1` finds the runs that were resumed. **`run.last_logged`** is the modification time of
`_metrics.jsonl` as of the last ingest (the `metrics_mtime` column, beside `metrics_size`), `null`
for a run that never logged a metric; sorted descending it puts the runs that logged most recently
first.

**Run facts** (`query/facts.py`) are what the group tools (`compare`, `digest`, `diagnose`, `logs`, `wait`)
need to know about runs: `run_facts` selects them with the same machinery as `runs`, from the index alone
(status judged at `now`, `attempts`, `last_logged`, and the flattened config and the card's metric
statistics only when asked), after one catch-up. Only a run's output text is still read from its file.
`failure_key(error, traceback)` is the one failure-signature rule: the signature of the error the card
recorded, else of the output traceback (its lines joined). The signature is the last line with quoted
strings (`<str>`), paths (`<path>`), numbers and hex (`#`) normalized, cut at 120 characters; a last
line that is a bare exception type reads `KeyError (after: <the line before>)`, so different failures
re-raised without a message stay apart. Signatures are grouping labels, not identifiers.
`compare`, `digest`, `diagnose`, `logs` and `wait` take their runs from `run_members` (`compare` and `digest`
ask for config and metrics, `digest` for the failures by `failure_key(error, None)`), so a pulled snapshot
answers them at its own time like any other read. `last_logged` can lag behind the file
(a daemon behind, or a busy run the catch-up budget deferred), so `diagnose` stats `_metrics.jsonl` once for
a running run that looks stalled by it and judges by the fresher time; no other run costs a stat.

**Windowed statistics** are computed exactly from the column files, with a step window appended:
`metric.val/acc.mean[1000:2000]`. They support `first`, `last`, `min`, `max`, `mean` and `count`.
This is the same reduction as a prediction's `reduce: {metric, stat, steps}`
([research record](09-research-record.md#predictions)); predictions and queries share one
implementation.

### Selecting runs

Every query has the shape `<kind>: {from, where, …}`. It starts by selecting runs, the same way
for all kinds:

```yaml
from: .                        # a group; a run id also works
depth: all                     # all (default) | 1: only direct children
hidden: false                  # false (default): leave hidden runs out | true: include them
where:
  config.lr: {lt: 1.0e-3}
  run.status: finished
  run.tags: {has: baseline}
  any:                         # OR over the listed conditions
    - config.warmup: 500
    - config.warmup: 1000
```

- **Runs.** A run is named by its id; when no group of that name exists, by a unique id suffix of
  at least four characters or its run name (a name shared by several runs is refused; a shorter
  suffix matches by chance, so it is read as a group). One resolver (`query/resolve.py`) answers for
  queries, notes and proposals: it follows moved groups, refuses reserved names and paths leaving
  the log dir, and lists the siblings and top-level groups for an unknown group.
- **Hidden runs.** `hidden: false` (the default) leaves hidden runs out of every kind: listings, curves,
  aggregates, seeds, `keys` and `groups` counts, and the research record's membership
  ([layer 9](09-research-record.md#hidden-runs)). `hidden: true` (`--hidden` on the CLI) includes them, and
  `run.hidden` is a field a query can show or filter on. A run named in `from` (id, unique suffix or name)
  always counts, so a hidden run can be inspected before it is promoted; a group named in `from` does not
  bring its hidden runs back. A view's queries never include hidden runs unless the query opts in with
  `hidden: true`.
- **Paths.** In a view, `from` is relative to the viewed group (`.`, `..`, `lr-sweep`). In the CLI
  and MCP, it is relative to the log dir; `.` covers the local log dir and all connected remotes, and
  `@cluster/scaling` names a remote group ([layer 4](04-remotes.md#naming-remote-groups)).
- **Filters** are a mapping from field to condition, combined with AND. A plain value means
  equality. Operators: `eq`, `ne`, `lt`, `le`, `gt`, `ge`, `in`, `nin`, `has` (list contains),
  `exists`, `glob` (string pattern). `any` and `not` combine conditions.
- **Seeds** (`seeds: config.seed`, a field of `runs` and `series` only; any other kind refuses it as an
  unknown field) merge runs that agree on every field that distinguishes them
  apart from that key (`config.varying` minus the seed and its aliases), exactly as in predictions.
  The key is any config field, nested ones too (`config.trainer.seed`). Values then come as mean,
  standard deviation and count.
- **The seed rule** is one function, `distinguish.seed_key(varying)`: the one varying config key whose
  leaf is `seed`, `random_seed` or `rng_seed` (`data_seed` is a hyperparameter). With no such key, or
  several, there is none. `keys` answers it as `config.seed` (a key, or `null`); the default view, the
  chart's "seed mean" setting when a viewer's settings are saved, and validation use it, falling back to
  `config.seed` where a key must be written, and the default view merges nothing without one.
- **By** (`by: [config.lr]` on `runs`, as on `series`) makes one row per combination of the fields'
  values, aggregated like seeds (`runs` lists the run ids; `meta.groups` counts the rows). Without
  `select`, the default columns leave out the run name.
- **Across sources**, listings (rows, curves, data, timeline entries) are merged; aggregates (groups,
  seeds, importance, `keys` value ranges) are computed per source and labelled with it
  ([layer 4](04-remotes.md#federation)).

### Query kinds

There are eight kinds of queries. All share the selection above.

**`keys`**: what exists in a selection. This is the first call an agent makes in an unfamiliar
group.

```yaml
keys: {from: scaling/}
```

Returns the metric keys (with how many runs logged them, their step range, the most points one run
has, and whether they are `constant`: one value in every run, a single point in a single run
excepted), config keys (with distinct values or ranges), data keys (tables, images, text) and
tags. Config also carries `varying`: the keys that actually distinguish the selected runs, dropping
aliases (several keys that happen to split the runs the same way; the shortest name is kept, the
rest listed in `aliases`), keys a finer key determines (listed in `dropped`, each with the first key that
determines it) and noise unique to every run (a timestamped path, not a real sweep).
`varying_config` and the header's facts line read `varying`, not the raw per-key value lists.

**`runs`**: a run table.

```yaml
runs:
  from: scaling/lr-sweep
  where: {run.status: finished}
  select: [run.name, config.lr, metric.val/acc.max, metric.train/loss.ema_last, proposal.check]
  sort: [-metric.val/acc.max]   # leading "-" sorts descending
  limit: 20
```

Without `select`, the columns are name, status, steps and the last value of the most common metrics.

**`series`**: curves.

```yaml
series:
  from: .
  where: {config.warmup: 500}
  y: [train/loss]              # metric keys
  x: _step                     # _step (default), _t (wall time), _elapsed, or a metric key such as epoch
  steps: [0, 5000]             # optional window
  points: 1000                 # buckets per curve
  smooth: {ema: 0.9}           # optional, applied to the raw data before downsampling
```

- Each curve comes back either **raw** (when it has at most `points` points in the window) or
  **downsampled** as min, max and last per bucket, with the bucket edges. The answer always says
  which.
- **Every curve carries the drawing envelope** `x`, `y` and, unless raw, `lo`, `hi`, `n`, so a consumer
  draws any curve from four names without telling the variants apart. A raw curve is its own envelope
  (`x`, `y`, no band). A downsampled curve gains `y` = `last`, `lo` = `min`, `hi` = `max` and `n` =
  `count`. A grouped curve gains `y` = `mean` (`lo`, `hi` and `n` already carry these names; with
  `band: none` `lo` and `hi` are `null`). `len(y) == len(x)`, and `lo <= y <= hi` wherever all three are
  numbers. The variant fields (`raw`, `first`, `min`, `max`, `last`, `count`, `mean`) also flow to the
  web UI, `serve`'s HTTP API, `serve --stdio` and the kit, which kit v1 blocks and older hubs read.
- **The series meta says `running`**: how many matched runs have the derived status `running`, summed across
  sources in a merged answer, so a chart without a point yet can say it waits for the first value.
- **The CLI and MCP get the envelope only.** For callers `cli` and `mcp` the answer drops `last`, `min`, `max`,
  `count` and `mean` from every curve (`first`, `raw` and `width` stay), once and before the token cut
  (`budget.page`, `answers.paged`), so a page holds more curves (about two thirds more); the query layer never strips.
  A serve answering a CLI or MCP call (`x-beamtime-caller`) strips like the CLI, `serve --stdio` does not
  (`Context.wire`), and `remote.answer` strips what a remote or a serve answered, so a federated call ends up
  envelope-only too; what an older remote or an older running serve answered gains the envelope first
  (`answers.upgraded`), so the strip never takes a curve's values. A CSV export (`series --to`) is wide, one row per run and step with `<y>`, `<y>.lo`, `<y>.hi`, `<y>.n` columns and none of the variant names ([layer 8](08-cli-mcp.md#reading-cli-and-mcp)).
- A metric as `x` (`read.x_values`) pairs each point with that metric's most recent value at or before
  the same step (none where it isn't finite), so x is always a value the run logged and a stair-logged
  `epoch` stays a stair; there is no interpolation. Points before the axis'
  first value are dropped. Each curve says whether its `x` is `monotone` and, when `x` is not the
  step, keeps the `step` of each point.
- A per-run curve of a run with later attempts carries `resumes`: where each of them took over, on
  the curve's x axis (the resume steps for `_step`, `read.resume_marks` otherwise, none where the axis
  has no value). The web UI draws them ([layer 7](07-web-ui.md#charts)); aggregated curves have none.
- With `by: [fields]`, the runs sharing the fields' values come back as one aggregated curve per
  bucket: mean, a band (`band: minmax | std | stderr | none`) and the number of contributing runs.
  `seeds: config.seed` is the shorthand for aggregating by the varying config, apart from the seed.
  With another `x`, the buckets are `points` equal widths from the smallest to the largest x over the
  runs (the largest x belongs to the last bucket; a constant x is one bucket), each run is averaged
  per bucket first, and `x` in the answer is the bucket centre. Aggregating over an `x` that is not
  monotone in a run is an error: show each run instead. Steps keep power-of-two buckets.
- Each chart has a point budget of about 30k; `points` per curve shrinks when a chart requests many
  curves.

**`data`**: logged tables, images and text.

```yaml
data: {from: ., key: val/per_class, step: last}   # last | all | a step | [start, end] | [last, step]
```

Tables come back as columns, images and text as references the UI or agent can load. The entries are
those of the asked step, so a page loads one step's files at a time; `["last", s]` gives each run's latest
entries at or before `s` (a run that logged nothing by then has none); `meta.steps` lists every step at
which a run in scope logged the key (the union over runs, ascending), whatever `step` asks. With
`clock: <metric>` (an unknown metric is refused like any other), `meta.clocks` has the metric's value
at each of those steps (`read.x_values`: its most recent value at or before the step, from the first
run that has one; `null` where no run does). Merged answers union the `steps` and merge `clocks` by step.

**`timeline`**: notes and run events in time order.

```yaml
timeline: {from: scaling/, types: [verdict, decision], since: 2026-10-01, limit: 30}
```

`types` filters note types and event kinds. Each entry carries its one-line description; note
bodies are loaded only when asked for.

**`groups`**: the group tree with what's attached to it.

```yaml
groups: {from: ., depth: 2}
```

Returns each group with its research status, proposal statement, check, plan progress, current
verdict and run counts by status. The counts are of visible runs; a `hidden` column counts the hidden ones.

**`importance`**: how strongly config fields relate to a target metric.

```yaml
importance: {from: scaling/lr-sweep, target: metric.val/acc.max, fields: [config.lr, config.warmup]}
```

Returns, per field, the Spearman rank correlation with the target (numeric fields) and the share of
the target's variance explained by grouping on the field (η², numeric fields in quantile bins), plus
the number of runs. Without `fields`, every config key that varies in scope is used (the `varying` keys
of `keys`); a field constant across the runs is left out.

The answer is `{kind: importance, target, rows, notice, meta}`; a row is `{field, spearman,
eta_squared, n}`, sorted by η², then the absolute Spearman correlation, and `spearman` is null for a
non-numeric field (η² groups on its distinct values). Only finished, visible runs with a finite target
count, and a run whose field value is missing, NaN or infinite drops out of that field's row alone,
so `n` is per row. The target must be one number per run (`metric.<key>.<stat>` or `value.<key>`).
Below ten runs `rows` is empty and `notice` says how many there were.

**`file`**: a data file stored with a view ([layer 1](01-storage.md#views-in-storage)).

```yaml
file: {path: data/3f9a21c0-fit.parquet, columns: [lr, acc]}
```

The path is relative to the `view/` folder of the view that declares the query, not to the viewed
group. Returns the table as columns, labelled with the group it belongs to. `columns` narrows and
orders the answer; an unknown name is an error that lists the file's columns and names the closest.
Formats are CSV, JSON (records, or `{columns: {...}}`) and Parquet (needs PyArrow); a file above 2 MB
is a validator warning (the page loads all of it), above 16 MB an error (the remote bundle limit).
A CSV is comma-separated with a header row (a UTF-8 byte order mark and blank lines are ignored); a header cell that
holds `;` or a tab, an empty or repeated column name, and a row with another number of cells than the
header are errors that say how to write it (`df.to_csv(path, index=False)`). Numeric cells read as
numbers, an empty cell as `null`, anything else as text.

### Answers

- **One JSON shape per kind**, columnar for tables and curves (`{"columns": [...], "rows": [...]}`,
  `{"x": [...], "min": [...], "max": [...], "last": [...]}`), so large answers stay compact. The `bt`
  kit reshapes them for code ([layer 5](05-views.md#data)).
- **Every answer carries meta**: freshness (see [Freshness](#freshness-the-daemon)), whether curves
  were downsampled, how many runs matched, and whether `limit` cut the answer.
- **Defaults depend on the caller.** Views get up to 1000 rows and full point budgets. MCP answers
  default to 50 rows and 100 points per curve, so an agent sees the shape of a curve without
  flooding its context; it can ask for more.

### CLI and MCP

The CLI has one command per kind. Flags map 1:1 onto the object form, and `--where` takes a compact
condition string:

```sh
beamtime keys scaling/
beamtime runs scaling/lr-sweep --where 'run.status=finished' --where 'config.lr<1e-3' \
    --sort -metric.val/acc.max --select run.name,config.lr,metric.val/acc.max --limit 20
beamtime series . -y train/loss --steps 0:5000 --points 200
beamtime query query.yaml          # or --json '{...}': the object form directly
```

Condition strings use `= != < <= > >=`, `~` for glob, and `in` with a comma list. They belong to the
query language, not to the CLI: `src/beamtime/query/conditions.py` parses them for the CLI's `--where` and
for the operations that take one (`wait`'s `until`), and its error messages name the flag the caller
gives it. Output is a readable table by default, `--json` gives the canonical answer.

MCP has one tool per kind (`keys`, `runs`, `series`, `data`, `timeline`, `groups`, `importance`,
`file`) plus `query` for the object form of any kind ([layer 8](08-cli-mcp.md)).

## Implementation notes

- **Cache location.** `BEAMTIME_CACHE`, else `XDG_CACHE_HOME/beamtime`, else `~/.cache/beamtime`, then
  a directory per resolved log dir. The setup makes this one `cache` setting (`memory` or a path),
  resolved by `resolve_cache()` for the CLI, `serve`, MCP and `serve --stdio` alike, refusing network
  filesystems for memory ([setup](10-setup.md#the-cache)).
- **Column files** are named by the percent-encoded key and a generation number. Truncating for a
  resumed attempt writes the next generation and switches the manifest to it, so a reader that has
  the old files mapped is never cut short (shrinking a mapped file crashes readers). Wall time is
  stored as a column `_t` per run, so `x: _t` and `_elapsed` need no extra pass.
- **Ingest** always indexes the small files (`_run.json`, config, card, notes), so run tables are
  complete even when the time budget runs out; metric, event and data streams are indexed while the
  budget lasts (a query ingests the streams of the runs it reads itself). Finished runs are
  re-checked only when `_run.json` or their `notes/` change. Lines are parsed with msgspec, falling back to Python's parser for lines with `NaN` or `Infinity`.
- **A decreasing step without an `attempt_started` event** waits for the event while the run is
  running (the SDK may have written the metrics before the event); in a run that has ended, it is
  treated as a resume at that step.
- **Filters** fetch only the referenced fields with SQLite's `json_extract`, then evaluate conditions,
  windowed statistics and `any`/`not` in one small Python evaluator. Simple top-level comparisons are
  also sent to SQL as a prefilter, guarded by the value's type so it agrees exactly with the
  evaluator (numbers compare as numbers, strings as strings). Key checks stop at the first run that
  has the key; the full key list is built only to suggest names after a miss.
- **Freshness checks** cost one `stat` of `_run.json` and one of `notes/` per run in scope when no
  daemon runs (about 7 µs per run); finished runs are re-read only when those change.
- **Curves** name their metric in `metric` (a raw curve's values are in `y`) and carry the run's
  `name` next to its id.
- **Downsampling** covers finite values only, like the card and the preview. Buckets have the
  smallest power-of-two width that gives at most `points` buckets; edges sit at multiples of the
  width. A downsampled curve carries `x` (bucket start), `first` (first step with data), `min`,
  `max`, `last` and `count` (and the envelope `y`, `lo`, `hi`, `n`, the same lists as `last`, `min`,
  `max` and `count`); a raw curve carries `x` and `y`, with `null` for non-finite values so answers
  stay valid JSON.
- **Previews answer** full-range curves on `_step` without smoothing for runs that are not running,
  whenever the preview pins down the same bucket width; the answer is then identical to the one from
  the column files, and needs no ingest of the run's metrics.
- **Defaults per caller**: CLI and MCP 50 rows, 100 points per curve, 30 entries; views 1000 rows,
  1000 points, 200 entries. Run tables always start with `run.id`.
- **Concurrency.** Schema creation re-checks the version inside an immediate transaction, so two
  processes opening a new cache at once don't rebuild it under each other; the column files are
  deleted inside that transaction too, so a process that sees the new schema never ingests into a
  folder about to go. Switching to WAL retries while another process holds the lock.
- **`proposal.*` fields** are computed in Python after the SQL selection, like windowed
  statistics: on a `runs` row they describe the run's own proposal (a blank one is `open`), on a
  `groups` row the group's current proposal. `proposal.progress` is a fraction from 0 to 1;
  `groups` shows the progress as text ("9 of 15 grid points") and filters on `path` and
  `proposal.*`.
- **Links**: a `links` table (source note, kind, target) is filled at note ingest from the
  `[[...]]` links in bodies and from `evidence`, `resolves` and `supersedes`; it gives the backlinks of
  runs and predictions. The index schema version is 3; a cache of another version is rebuilt.
- **Change reports**: `catch_up` lists the runs it ingested in `Freshness.changed`; the
  daemon's also lists groups whose `notes/`, `proposal/`, `memory/` or `view/` changed since its
  last poll. `Daemon(on_change=...)` receives them after every poll (every 2 s); `serve` turns them
  into live updates ([layer 7](07-web-ui.md#implementation-notes)).
- **Deferred streams**: a run whose streams a time budget deferred has no `indexed_at`
  yet, and the next catch-up with time to spare reads them, also for runs that have ended.
- **Reserved names are not scopes**: `from` naming an authored or machine folder (`proposal/`,
  `notes/`, `_trash/`, …) is refused like a missing group.
- **Remote sources**: `beamtime serve --stdio` on a remote catches up only the scope of each
  request, into a temporary cache unless one is configured; a configured cache on NFS, Lustre or
  GPFS is refused for the temporary one, and `status` says why.
- **Run facts come from the index**: `compare` and `digest` read config, card statistics, code,
  status and error from the indexed rows, not from each run's files.

## Decisions

- Metric store: SQLite for metadata, raw column files per (run, metric) for curves, read with mmap.
- One pure-Python read path with `math.fsum`, used everywhere; NumPy is not a dependency of the CLI.
- Plain formats in v1: int64 steps and float64 values, no compression.
- Resumed attempts truncate the columns at the resume step; steps stay sorted.
- Discovery walks only the queried subtree, pruned by modification time; vanished runs are dropped.
- One `beamtime serve` per root, guarded by a lock; a second one attaches (prints the URL) or, with
  `--replace`, takes over; everything else is a client. The CLI and MCP catch up within a time budget when
  no daemon runs; with a `memory` cache they read through the running UI serve.
- Every long-running process registers in `runtime_base()/procs/` under a held lock; liveness is the
  lock, never the pid. `beamtime ps` lists them, `beamtime stop` stops serves only.
- Queries are validated with msgspec structs (about 25 ms to import), which also produce the JSON
  schema.
- Views write conditions in the object form only; the CLI keeps compact `--where` strings.
- The validator converts numeric strings on numeric fields to numbers, because PyYAML reads `1e-3`
  as a string.
- Across sources, listings are merged and aggregates are computed per source.
- Selection leaves hidden runs out by default; a run named by id always shows, `hidden: true` includes them.

## Later

- **Smaller cache.** Encode steps as runs of constant stride (saves about half the cache). float32
  values stay excluded: they would make prediction checks disagree with the logged data.
- **Auto-started daemon.** The first CLI call starts `serve --no-ui` in the background, exiting
  after a period without queries or running runs.
- **Precomputed levels** or a tested NumPy path for long zooms, if needed.
