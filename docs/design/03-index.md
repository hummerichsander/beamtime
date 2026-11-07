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

## Prior art

| Tool | Metric storage | Downsampling | Lesson |
|---|---|---|---|
| TensorBoard | event files, all in memory (Rust data server since 2.5) | random reservoir, 1000 points | spikes vanish; memory and startup grow with the logdir; dropped its SQLite mode |
| W&B | server: MySQL/BigTable hot store, Parquet export | "full fidelity": x-buckets with min/max band and last value, recomputed on zoom | moved away from random 1500-point sampling because it lost spikes |
| MLflow | file store (no index, "severely limits performance"), now SQLite by default; one row per value | even stride, ≤ 2500 points/run, min/max *step* only | spikes can be missed; per-value rows are large |
| Aim | RocksDB per run plus merged index, SQLite for metadata | every n-th point, default 50 | crashed runs were never indexed and slowed queries; years of lock and index redesigns |
| Trackio | SQLite per project in `~/.cache`; JSONL fallback on Lustre/GPFS/NFS | power-of-two stride for live charts, min/max bins for plots | independently arrived at Beamtime's split of files on clusters and SQLite locally |
| ClearML | Elasticsearch | mean per bucket | averages hide spikes; servers ran out of memory |
| Guild AI | files plus SQLite cache of per-tag summaries | – | summaries are what run tables need; re-reading whole folders on change is not |

Recurring lessons:

1. **Random sampling is the most common regret.** Use min/max per bucket.
2. **Never discard data at ingest.** Keep everything; downsample at query time.
3. **Index continuously from file contents**, not when a run finishes; crashed runs must not degrade
   queries.
4. **Keep downsampling stable** for live charts: fixed bucket edges, so a growing curve doesn't
   jitter between refreshes.
5. **SQLite is fine locally with one writer**, never on shared filesystems.

## Techniques

- **Downsampling.** M4 (min, max, first, last per pixel column) renders a line chart without
  visible error; plain min/max never loses a spike. LTTB looks smooth but can drop spikes.
  Min/max is a single O(n) pass: NumPy does 10M points in ~10 ms, within 2× of the Rust library
  tsdownsample. **Rust is not needed for downsampling.**
- **Storage.** Time-series databases (Prometheus, VictoriaMetrics, QuestDB) store one append-only
  column per series and publish a committed length separately, so readers never see partial
  writes. Parquet and Arrow files have footers and cannot be appended in place.
- **Engines.** SQLite in WAL mode allows many readers alongside one writer. DuckDB allows either one
  read-write process or several read-only ones, which conflicts with a web server, CLI and MCP
  reading while something indexes.
- **Rust in a Python package.** Mature (maturin, manylinux2014 wheels cover clusters back to
  CentOS 7), but it adds a CI matrix per platform, and the source fallback needs a Rust toolchain,
  which clusters rarely have. Worth it only for a measured bottleneck.
- **Browser.** Vega-Lite gets sluggish beyond roughly 20–50k points per chart. uPlot handles
  hundreds of thousands and is the escape hatch for dense interactive charts.

## Benchmarks

Measured on an Apple M3, 16 GB, SSD, with synthetic runs of 20 metrics (12 every step, 8 every
100 steps) with known spikes. Scale M is 1000 runs and 1.2×10^8 points in 4.2 GB of JSONL; L1 is
one run with 10M steps. Charts use 500 buckets with min and max, about 1000 points per curve.
Scripts and raw numbers are in `bench/index/`.

Candidates:

- **A**: SQLite with precomputed bucket levels as packed blobs, exact values from JSONL.
- **B**: SQLite for metadata, raw column files per (run, metric) read with mmap, downsampled on
  the fly with NumPy.
- **E**: B's files read in pure Python, without NumPy.
- **C**: SQLite with one row per point.
- **D1 / D2**: DuckDB over Parquet files / with its own database file.

Results at scale M (first call in a fresh process / warm):

| | A | B | E | C | D1 | D2 |
|---|---|---|---|---|---|---|
| Full build | 146 s | 65 s | = B | 198 s | 45 s | 40 s |
| Index size | 0.8 GB | 1.9 GB | = B | 2.9 GB | 0.8 GB | 1.0 GB |
| Live: 1000 new lines queryable | 30 ms | 14–71 ms | = B | 29 ms | 15 ms | 28 ms |
| Chart, 50 runs | 11 / 10 ms | 9 / 8 ms | 80 / 55 ms | 143 / 146 ms | 27 / 23 ms | 23 / 23 ms |
| Zoom 1% of 10M steps | 0.2 ms | 11 ms | 7 ms | 26 ms | 10 ms | 2 ms |
| Exact mean, 500 runs, any window | 4.6 s (rescans JSONL) | 0.35 / 0.07 s | 0.11 / 0.09 s | 0.49 / 0.21 s | 0.08 s | 0.18 / 0.08 s |
| One-shot CLI chart, whole process | **55–59 ms** | 115–130 ms | 100–165 ms | 205 ms | 171–187 ms | 183–188 ms |

Further findings:

- **Imports dominate one-shot latency.** The bare interpreter starts in 20 ms; `sqlite3` and
  `json` add 6 ms. NumPy adds 67 ms, DuckDB 98 ms, PyArrow 116 ms. Every candidate's query is
  faster than its imports. Launching through `uv run` adds another 160–230 ms, so the CLI must be
  an installed console script.
- **Run tables don't separate the candidates.** SQLite with config and run card as JSON columns
  answers in 10–13 ms (38 ms as a fresh process); scanning the 30k files directly takes about 1 s.
- **JSONL parsing is the cost of a full rebuild.** `json` reads 117k lines/s, `orjson` 546k,
  PyArrow's reader about 1M. The builds were single-process; building runs in parallel would cut
  them by up to the core count.
- **Spikes were preserved by every candidate.** The few misses sat in the same bucket as a larger
  spike, which no min/max downsampling can show. All candidates agreed on the exact aggregates.

## Recommendation

**SQLite for metadata, raw column files for metrics (candidate B), read by one pure-Python
implementation.** It is the simplest design and meets every target. Ingest only appends bytes, every
window and aggregate is exact, and no precomputed structure needs maintaining.

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
  Python over `mmap` and `array`, with `math.fsum` for sums, used by the CLI, MCP and `serve` alike.
  The CLI, the UI and prediction checks can therefore never disagree, not even in the last bit. The
  benchmark puts it at 55–90 ms for a 50-run chart. A NumPy path may be added later for long zooms in
  `serve`, tested against this reference.
- **Charts** split the requested window into buckets and send min and max per bucket, like W&B's
  full fidelity. Bucket edges are fixed per zoom level, so live curves don't jitter. **Each chart**
  has a point budget of about 30k, which keeps charts smooth in the browser.
- **Values stay float64**, so exact aggregates are exact.

### What we don't do

- **No precomputed levels for now** (candidate A). They can be added later as a cache on top of the
  raw files if long-range charts over very long runs become slow.
- **No DuckDB, PyArrow or NumPy as dependencies of the CLI path.** Their imports alone exceed the CLI
  budget, and DuckDB's locking conflicts with concurrent readers.
- **No Rust.** Parallel ingest plus optional `orjson` bring a full rebuild to a few seconds per 10^8
  points without a native extension.

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
- **One daemon per root.** `serve` holds `serve.lock` in the cache; a second `serve` for the same root
  refuses to start and points to the running one. CLI calls, MCP servers and the headless renderer
  ([layer 7](07-web-ui.md#screenshots-and-the-headless-renderer)) are clients: they read the index and
  never start a daemon.
- **While it runs**, it polls running runs for new lines (the modification time of `_metrics.jsonl`
  every few seconds, only for runs whose status is `running`) and indexes them. Finished runs are
  indexed once.
- **The CLI and MCP never depend on it for correctness.** Without a running daemon, each call catches
  up on the runs it queries within a time budget (default 200 ms), then answers. If the budget was
  not enough, the answer says so: "3 runs are up to 4 min behind".
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

## Query language

One query language serves views (YAML), the CLI (flags) and MCP (JSON). The **object form** is
canonical: a view writes it as YAML, MCP sends it as JSON, and every CLI command maps 1:1 onto it.
An agent that learned it in one place can use it everywhere.

Design goals:

- **Small and predictable.** Few concepts, no general-purpose expressions.
- **Validated with helpful errors.** An unknown metric fails with the closest matches and a pointer
  to `beamtime keys`, instead of returning nothing.
- **Exact by default.** Every number comes from the full data; only curves are downsampled, and the
  answer says so.
- **Token-aware.** Defaults keep answers small; larger answers have to be asked for.

### Fields

Every value a query can filter, sort or show is a **field**, a dotted path with a namespace:

| Namespace | Example | Source |
|---|---|---|
| `run.` | `run.id`, `run.name`, `run.status`, `run.created_at`, `run.duration_s`, `run.steps`, `run.tags`, `run.path`, `run.commit`, `run.branch`, `run.dirty`, `run.code` | `_run.json`, run card |
| `config.` | `config.optimizer.lr` | `_config.json` |
| `metric.` | `metric.val/acc.max`, `metric.train/loss.ema_last` | run card statistics |
| `value.` | `value.test/acc` | explicit run card values |
| `proposal.` | `proposal.status`, `proposal.check`, `proposal.progress`, `proposal.verdict` | the check and the notes ([research record](09-research-record.md#the-check)) |

For `metric.`, the last segment is always the statistic and everything between is the metric key,
so keys containing dots (`metric.layer.0.grad.max`) stay unambiguous. The statistics are the run
card's: `first`, `last`, `ema_last`, `min`, `min_step`, `max`, `max_step`, `mean`, `count`,
`last_step`, `nonfinite`, `slope_last10pct`. A config key that itself contains a dot is quoted:
`config["a.b"]`.

**`run.code`** is one comparable identity for the code a run ran on: the short commit, plus the
short diff hash (`run.dirty`'s `diff_sha`) when the checkout was dirty (`f385eda+1a2b3c4d`), so the
same commit and the same uncommitted changes compare equal across runs and checkouts. It is `null`
without a git checkout, or on a dirty run recorded before `diff_sha` existed. `keys` lists a
group's distinct codes by count (only when they differ: a single version isn't a fact worth
showing), and `check` adds a note to a proposal when its members didn't all run on the same code.

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
where:
  config.lr: {lt: 1.0e-3}
  run.status: finished
  run.tags: {has: baseline}
  any:                         # OR over the listed conditions
    - config.warmup: 500
    - config.warmup: 1000
```

- **Paths.** In a view, `from` is relative to the viewed group (`.`, `..`, `lr-sweep`). In the CLI
  and MCP, it is relative to the log dir; `.` covers the local log dir and all connected remotes, and
  `@cluster/scaling` names a remote group ([layer 4](04-remotes.md#naming-remote-groups)).
- **Filters** are a mapping from field to condition, combined with AND. A plain value means
  equality. Operators: `eq`, `ne`, `lt`, `le`, `gt`, `ge`, `in`, `nin`, `has` (list contains),
  `exists`, `glob` (string pattern). `any` and `not` combine conditions.
- **Seeds** (`seeds: config.seed`) merge runs that agree on every field that distinguishes them
  apart from that key (`config.varying` minus the seed and its aliases), exactly as in predictions.
  Values then come as mean, standard deviation and count.
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
rest listed in `aliases`) and noise unique to every run (a timestamped path, not a real sweep).
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
- A metric as `x` (`read.x_values`) pairs each point with that metric's most recent value at or before
  the same step (none where it isn't finite), so x is always a value the run logged and a stair-logged
  `epoch` stays a stair.
  Interpolating a metric that never decreases was tried and dropped: it can't tell a stair from a
  plateau, and continued a learning-rate warmup far past any logged value. Points before the axis'
  first value are dropped, and each curve says whether its `x` is `monotone`.
- With `by: [fields]`, the runs sharing the fields' values come back as one aggregated curve per
  bucket: mean, a band (`band: minmax | std | stderr | none`) and the number of contributing runs.
  `seeds: config.seed` is the shorthand for aggregating by the varying config, apart from the seed.
  With another `x`, the buckets are `points` equal widths from the smallest to the largest x over the
  runs (the largest x belongs to the last bucket; a constant x is one bucket), each run is averaged
  per bucket first, and `x` in the answer is the bucket centre. Aggregating over an `x` that is not
  monotone in a run is an error: show each run instead. Steps keep power-of-two buckets.
  (The parameter is `by`, not `group`, since a group is a folder of runs.)
- Each chart has a point budget of about 30k; `points` per curve shrinks when a chart requests many
  curves.

**`data`**: logged tables, images and text.

```yaml
data: {from: ., key: val/per_class, step: last}   # last | all | a step | [start, end]
```

Tables come back as columns, images and text as references the UI or agent can load.

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
verdict and run counts by status.

**`importance`**: how strongly config fields relate to a target metric.

```yaml
importance: {from: scaling/lr-sweep, target: metric.val/acc.max, fields: [config.lr, config.warmup]}
```

Returns, per field, the Spearman rank correlation with the target (numeric fields) and the share of
the target's variance explained by grouping on the field (η², numeric fields in quantile bins), plus
the number of runs. Without `fields`, every config key that varies in scope is used.

**`file`**: a data file stored with a view ([layer 1](01-storage.md#views-in-storage)).

```yaml
file: {path: data/3f9a21c0-fit.parquet}
```

The path is relative to the `view/` folder of the view that declares the query, not to the viewed
group. Returns the table as columns, labelled with the group it belongs to.

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

Condition strings use `= != < <= > >=`, `~` for glob, and `in` with a comma list. Output is a
readable table by default, `--json` gives the canonical answer.

MCP has one tool per kind (`keys`, `runs`, `series`, `data`, `timeline`, `groups`, `importance`,
`file`) plus `query` for the object form of any kind ([layer 8](08-cli-mcp.md)).

## Implementation notes

Decided while building the index and the queries (milestone M2):

- **Cache location.** `BEAMTIME_CACHE`, else `XDG_CACHE_HOME/beamtime`, else `~/.cache/beamtime`, then
  a directory per resolved log dir.
- **Column files** are named by the percent-encoded key and a generation number. Truncating for a
  resumed attempt writes the next generation and switches the manifest to it, so a reader that has
  the old files mapped is never cut short (shrinking a mapped file crashes readers). Wall time is
  stored as a column `_t` per run, so `x: _t` and `_elapsed` need no extra pass.
- **Ingest** always indexes the small files (`_run.json`, config, card, notes), so run tables are
  complete even when the time budget runs out; metric, event and data streams are indexed while the
  budget lasts. Finished runs are re-checked only when `_run.json` or their `notes/` change. Lines
  are parsed with msgspec, falling back to Python's parser for lines with `NaN` or `Infinity`.
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
  `max`, `last` and `count`; a raw curve carries `x` and `y`, with `null` for non-finite values so
  answers stay valid JSON.
- **Previews answer** full-range curves on `_step` without smoothing for runs that are not running,
  whenever the preview pins down the same bucket width; the answer is then identical to the one from
  the column files, and needs no ingest of the run's metrics.
- **Defaults per caller**: CLI and MCP 50 rows, 100 points per curve, 30 entries; views 1000 rows,
  1000 points, 200 entries. Run tables always start with `run.id`.
- **Concurrency.** Schema creation re-checks the version inside an immediate transaction, so two
  processes opening a new cache at once don't rebuild it under each other; switching to WAL retries
  while another process holds the lock.
- **`proposal.*` fields** (M4) are computed in Python after the SQL selection, like windowed
  statistics: on a `runs` row they describe the run's own proposal (a blank one is `open`), on a
  `groups` row the group's current proposal. `proposal.progress` is a fraction from 0 to 1;
  `groups` shows the progress as text ("9 of 15 grid points") and filters on `path` and
  `proposal.*`.
- **Links** (M4): a `links` table (source note, kind, target) is filled at note ingest from the
  `[[...]]` links in bodies and from `evidence`, `resolves` and `supersedes`; it gives the backlinks of
  runs and predictions. The index schema version is 2; older caches are rebuilt.
- **Change reports** (M5): `catch_up` lists the runs it ingested in `Freshness.changed`; the
  daemon's also lists groups whose `notes/`, `proposal/`, `memory/` or `view/` changed since its
  last poll. `Daemon(on_change=...)` receives them after every poll (every 2 s); `serve` turns them
  into live updates ([layer 7](07-web-ui.md#implementation-notes)).
- **Deferred streams** (fixed in M5): a run whose streams a time budget deferred has no `indexed_at`
  yet, and the next catch-up with time to spare reads them, also for runs that have ended.
- **Reserved names are not scopes**: `from` naming an authored or machine folder (`proposal/`,
  `notes/`, `_trash/`, …) is refused like a missing group.
- **Remote sources** (M8): `beamtime serve --stdio` on a remote catches up only the scope of each
  request, into a temporary cache unless one is configured; a configured cache on NFS, Lustre or
  GPFS is refused for the temporary one, and `status` says why.
- **Not yet**: `importance` for v1.1.

## Decisions

- Metric store: SQLite for metadata, raw column files per (run, metric) for curves, read with mmap.
- One pure-Python read path with `math.fsum`, used everywhere; NumPy is not a dependency of the CLI.
- Plain formats in v1: int64 steps and float64 values, no compression.
- Resumed attempts truncate the columns at the resume step; steps stay sorted.
- Discovery walks only the queried subtree, pruned by modification time; vanished runs are dropped.
- One `beamtime serve` per root, guarded by a lock; everything else is a client. The CLI and MCP
  catch up within a time budget when no daemon runs.
- Queries are validated with msgspec structs, which also produce the JSON schema. Measured on the
  M3: Pydantic costs 65–81 ms to import plus about 2.5 ms per model; msgspec about 25 ms in total.
- Views write conditions in the object form only. In a blind test (20 tasks, Sonnet and Haiku, two
  repetitions each; `bench/query-forms/`) agents got all 160 answers right in both the object and
  the string form, so there is no reason for a second syntax. The CLI keeps compact `--where`
  strings.
- The validator converts numeric strings on numeric fields to numbers, because PyYAML reads `1e-3`
  as a string.
- Across sources, listings are merged and aggregates are computed per source.

## Later

- **Smaller cache.** Encode steps as runs of constant stride (saves about half the cache). float32
  values stay excluded: they would make prediction checks disagree with the logged data.
- **Auto-started daemon.** The first CLI call starts `serve --no-ui` in the background, exiting
  after a period without queries or running runs.
- **Precomputed levels** or a tested NumPy path for long zooms, if needed.
