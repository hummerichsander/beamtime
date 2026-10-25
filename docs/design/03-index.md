# Layer 3: Index and query

Status: **draft, under discussion.** Part 1 covers the metric store, the most performance-critical
piece. Part 2 covers the query language that views, CLI and MCP share.

The index sits between the files ([layer 1](01-storage.md)) and everything that displays them:
views, CLI, MCP. It is a cache in `~/.cache/beamtime/<root-hash>/`, rebuildable from the files at
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

**Candidate B: SQLite for metadata, raw column files for metrics.** It is the simplest design and
meets every target. Ingest only appends bytes, every window and aggregate is exact, and no
precomputed structure needs maintaining.

```
~/.cache/beamtime/<root-hash>/
  index.sqlite                     # runs, config, run cards, notes, links, events, file offsets
  series/<run-id>/<metric>.steps   # int64, appended
  series/<run-id>/<metric>.values  # float64, appended
  series/<run-id>/_manifest.json   # committed length per metric, source byte offset
```

- **Ingest** reads each `_metrics.jsonl` from the last byte offset recorded in the manifest,
  appends to the column files, then publishes the new lengths by replacing the manifest. Readers
  never read past the manifest; after a crash, column files are truncated to it.
- **One indexer at a time**, chosen by a file lock. Whoever needs fresh data takes the lock and
  catches up only on the runs it queries, which costs 15–30 ms per run.
- **Readers** map the column files and need no lock. Steps are sorted, so a step window is a binary
  search.
- **Charts** split the requested window into buckets and send min and max per bucket, like W&B's
  full fidelity. Bucket edges are fixed per zoom level, so live curves don't jitter. The total
  point budget per chart is capped (around 30k) to stay within what Vega-Lite draws smoothly.
- **Two read paths with identical results:** the long-running `beamtime serve` uses NumPy; one-shot
  CLI and MCP calls use a pure-Python reader over `mmap` and `array`, keeping the whole process
  around 60–100 ms. NumPy is never imported on the CLI's hot path.
- **Values stay float64**, so exact aggregates are exact.

### What we don't do

- **No precomputed levels for now** (candidate A). They give the fastest long-range charts but are
  the most code and still need B's raw files for exact queries. They can be added later as a cache
  on top of B if long-range charts over very long runs become slow.
- **No DuckDB or PyArrow as dependencies.** Their imports alone exceed the CLI budget, and DuckDB's
  locking conflicts with concurrent readers. Either can be offered later as an optional extra for
  ad-hoc analysis over the same files.
- **No Rust for now.** Downsampling in NumPy is within 2× of Rust. The one place Rust would pay off
  is a full rebuild, and parallel ingest plus optional `orjson` get it to a few seconds per 10^8
  points without a native extension.

## Freshness: the daemon

The cache only learns about new lines when a process reads them in. Beamtime has one long-running
process for that, `beamtime serve`:

- **`beamtime serve`** runs the web UI, the indexer and the connections to remotes (layer 4) for
  one root.
  `beamtime serve --no-ui` runs the same without the web UI, as a pure daemon.
- **While it runs**, it polls running runs for new lines (stat calls every few seconds, only for
  runs whose status is `running`, since every stat loads a cluster filesystem's metadata server)
  and indexes them. Finished runs are indexed once and not polled again.
- **The CLI and MCP never depend on it for correctness.** Without a running daemon, each call
  catches up on the runs it queries within a time budget (default 200 ms), then answers. If the
  budget was not enough, the answer says so: "3 runs are up to 4 min behind". With the daemon
  running, the catch-up is almost always empty.
- **Run tables and overviews stay fresh either way**: the run card and the preview
  (`_preview.json`) are rewritten by the run every 60 s and are small enough to read directly.
- **Overview charts are answered from previews** when the requested window and point budget fit
  the preview's buckets; zooms and exact statistics use the column files. The answer's meta says
  which source was used.

### Daemon status for agents

The daemon writes `~/.cache/beamtime/<root-hash>/serve.json` with its pid, port, version, start time
and a heartbeat. From that:

- `beamtime status` reports whether the daemon runs for this root, since when, with which version,
  and which remotes are connected or unreachable. MCP exposes the same as a tool.
- Every CLI and MCP answer carries a short freshness line: `live (daemon running)` or
  `catch-up only (daemon not running)`.
- Agents are instructed (layer 7) to check the status before working with live runs and, if the
  daemon is not running, to ask the user to start `beamtime serve --no-ui` rather than starting a
  long-running process themselves.

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
| `run.` | `run.name`, `run.status`, `run.created_at`, `run.duration_s`, `run.steps`, `run.tags`, `run.path` | `_run.json`, run card |
| `config.` | `config.optimizer.lr` | `_config.json` |
| `metric.` | `metric.val/acc.max`, `metric.train/loss.ema_last` | run card statistics |
| `value.` | `value.test/acc` | explicit run card values |
| `proposal.` | `proposal.check`, `proposal.verdict` | index (layer 1 evaluation) |

For `metric.`, the last segment is always the statistic and everything between is the metric key,
so keys containing dots (`metric.layer.0.grad.max`) stay unambiguous. The statistics are the run
card's: `first`, `last`, `ema_last`, `min`, `min_step`, `max`, `max_step`, `mean`, `count`,
`last_step`, `nonfinite`, `slope_last10pct`. A config key that itself contains a dot is quoted:
`config["a.b"]`.

**Windowed statistics** are computed exactly from the column files, with a step window appended:
`metric.val/acc.mean[1000:2000]`. This is the same reduction as a prediction's
`reduce: {metric, stat, steps}`; predictions and queries share one implementation.

### Selecting runs

Every query has the shape `<kind>: {from, where, …}`. It starts by selecting runs, the same way
for all kinds:

```yaml
from: .                        # a folder; a run id also works
depth: all                     # all (default) | 1: only direct children
where:
  config.lr: {lt: 1.0e-3}
  run.status: finished
  run.tags: {has: baseline}
  any:                         # OR over the listed conditions
    - config.warmup: 500
    - config.warmup: 1000
```

- **Paths.** In a view, `from` is relative to the viewed folder (`.`, `..`, `lr-sweep`). In the CLI
  and MCP, it is relative to the log dir; `.` is the whole log dir.
- **Filters** are a mapping from field to condition, combined with AND. A plain value means
  equality. Operators: `eq`, `ne`, `lt`, `le`, `gt`, `ge`, `in`, `nin`, `has` (list contains),
  `exists`, `glob` (string pattern). `any` and `not` combine conditions.
- **Seeds** (`seeds: config.seed`) merge runs whose configs differ only in that key, exactly as in
  predictions. Values then come as mean, standard deviation and count.

### Query kinds

There are six kinds of queries. All share the selection above.

**`keys`**: what exists in a selection. This is the first call an agent makes in an unfamiliar
folder.

```yaml
keys: {from: scaling/}
```

Returns the metric keys (with how many runs logged them and their step range), config keys (with
distinct values or ranges), data keys (tables, images, text) and tags.

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
- A metric as `x` pairs each point with that metric's most recent value at or before the same step.
- With `seeds`, curves of merged runs come back as mean with a min/max band per bucket.
- Each view has a total point budget (around 30k); `points` per curve shrinks when many curves are
  requested.

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

**`folders`**: the folder tree with what's attached to it.

```yaml
folders: {from: ., depth: 2}
```

Returns each group with its proposal statement, check, current verdict and run counts by status.

### Answers

- **One JSON shape per kind**, columnar for tables and curves (`{"columns": [...], "rows": [...]}`,
  `{"x": [...], "min": [...], "max": [...], "last": [...]}`), so large answers stay compact.
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

MCP has one tool per kind (`keys`, `runs`, `series`, `data`, `timeline`, `folders`), each taking
the object form. Separate tools give agents a small, precise schema for each.

## Decisions

- Metric store: SQLite for metadata, raw column files per (run, metric) for curves, read with mmap.
- Plain formats in v1: int64 steps and float64 values, no compression.
- `beamtime serve` is the daemon (web UI, indexer, remote connections); `--no-ui` runs it headless. The CLI and
  MCP catch up within a time budget when it isn't running.
- Agents can check the daemon with `beamtime status` and ask the user to start it.
- One-shot CLI and MCP calls use a pure-Python reader; NumPy is used only by `serve`.
- Queries are validated with msgspec structs, which also produce the JSON schema. Measured on the
  M3: Pydantic costs 65–81 ms to import plus about 2.5 ms per model, together 110–150 ms per CLI
  call; msgspec costs about 25 ms to import and almost nothing per model.
- Views write conditions in the object form only. In a blind test (20 tasks, Sonnet and Haiku, two
  repetitions each; `bench/query-forms/`) agents got all 160 answers right in both the object and
  the string form, at nearly the same length, so there is no reason for a second syntax and a
  second parser. The CLI keeps its compact `--where` strings.
- The validator converts numeric strings on numeric fields to numbers, because PyYAML reads `1e-3`
  as a string.

## Later

- **Smaller cache.** Encode steps as runs of constant stride (saves about half the cache). float32
  values stay excluded: they would make prediction checks disagree with the logged data.
- **Auto-started daemon.** The first CLI call starts `serve --no-ui` in the background, one per root
  (guarded by a lock file), exiting after a period without queries or running runs, as watchman or
  `dmypy` do. This changes only who starts the daemon, not the design.
- **Precomputed levels** on top of the raw files, if long-range charts over very long runs become
  slow.

## Open questions

None for this layer. The earlier question about sync and indexing is resolved by layer 4: each
machine indexes its own files, and status, including `lost`, is computed where the files are.
