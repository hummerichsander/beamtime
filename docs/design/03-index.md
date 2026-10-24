# Layer 3: Index and query

Status: **draft, under discussion.** This part covers the metric store, the most
performance-critical piece. The query language follows in a second part.

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

- **`beamtime serve`** runs the web UI, the indexer and sync (layer 4) for one root.
  `beamtime serve --no-ui` runs the same without the web UI, as a pure daemon.
- **While it runs**, it polls running runs for new lines (stat calls every few seconds, only for
  runs whose status is `running`, since every stat loads a cluster filesystem's metadata server)
  and indexes them. Finished runs are indexed once and not polled again.
- **The CLI and MCP never depend on it for correctness.** Without a running daemon, each call
  catches up on the runs it queries within a time budget (default 200 ms), then answers. If the
  budget was not enough, the answer says so: "3 runs are up to 4 min behind". With the daemon
  running, the catch-up is almost always empty.
- **Run tables stay fresh either way**: the run card is rewritten by the run every 60 s and is
  small enough to read directly.

### Daemon status for agents

The daemon writes `~/.cache/beamtime/<root-hash>/serve.json` with its pid, port, version, start time
and a heartbeat. From that:

- `beamtime status` reports whether the daemon runs for this root, since when, with which version,
  and when each remote last synced. MCP exposes the same as a tool.
- Every CLI and MCP answer carries a short freshness line: `live (daemon running)` or
  `catch-up only (daemon not running)`.
- Agents are instructed (layer 7) to check the status before working with live runs and, if the
  daemon is not running, to ask the user to start `beamtime serve --no-ui` rather than starting a
  long-running process themselves.

## Decisions

- Metric store: SQLite for metadata, raw column files per (run, metric) for curves, read with mmap.
- Plain formats in v1: int64 steps and float64 values, no compression.
- `beamtime serve` is the daemon (web UI, indexer, sync); `--no-ui` runs it headless. The CLI and
  MCP catch up within a time budget when it isn't running.
- Agents can check the daemon with `beamtime status` and ask the user to start it.
- One-shot CLI and MCP calls use a pure-Python reader; NumPy is used only by `serve`.

## Later

- **Smaller cache.** Encode steps as runs of constant stride (saves about half the cache). float32
  values stay excluded: they would make prediction checks disagree with the logged data.
- **Auto-started daemon.** The first CLI call starts `serve --no-ui` in the background, one per root
  (guarded by a lock file), exiting after a period without queries or running runs, as watchman or
  `dmypy` do. This changes only who starts the daemon, not the design.
- **Precomputed levels** on top of the raw files, if long-range charts over very long runs become
  slow.

## Open questions

1. **Sync and indexing.** The daemon owns both pulling remotes and indexing, so it can index the
   runs rsync reports as changed right after each pull. The `lost` status of remote runs then needs
   to be measured against the last successful sync of their remote, not against the current time,
   so a stalled sync shows "unknown, last synced 20 min ago" instead of marking healthy runs as
   lost. Settle with layer 4?
