# Metric index benchmark

All times are wall-clock seconds unless marked ms. Raw numbers: `results.jsonl`. Scripts: `gen.py` (data),
`cand_*.py` (candidates), `bench.py` (one phase per fresh process), `run_all.py` (driver), `extras.py`
(JSONL scan, W5, imports).

## Setup

- Apple M3 (8 cores), 16 GB RAM, internal SSD, macOS 26.5.2, CPython 3.11.9, SQLite 3.51.0, numpy 2.4.6,
  orjson 3.13.0, duckdb 2.0.0, pyarrow 26.0.0, tsdownsample 0.1.5.1.
- Data: 20 keys per run. 12 are logged every step, 8 (`val/*`) every 100 steps, so there are about 121k
  points per run. Curves are noisy, decaying and stored as float32-derived float64. `train/loss` gets
  upward spikes of 3 to 10x and `train/acc` gets downward spikes. Ground truth is in `spikes.json`.
  - S: 200 runs × 10k steps, 2.4×10^7 points, 848 MB of JSONL (4.2 MB per run).
  - M: 1000 runs × 10k steps, 1.2×10^8 points, 4.2 GB of logical JSONL. **Shortcut:** runs 200 to 999
    are hardlinks of runs 0 to 199, so only 848 MB is on disk. Every candidate still parses and indexes
    all 1000 files independently. M has about 0.6×10^8 fewer points than the 2×10^8 in the brief
    because 8 of the 20 keys are sparse.
  - L1: 1 run × 10M steps × 3 keys (3×10^7 points), 1.3 GB of JSONL, with 100 loss spikes.
  - Run table: 10k run folders with `run.json`, `config.json` and `summary.json` (30k files).
- Chart semantics: 500 equal-width buckets over the requested range, with min and max per bucket
  (≈1000 points per curve). A uses its own power-of-4 bucket grid (see below).
- "first" means the first call in a fresh process. "warm" is the median of 3 to 5 repeats in the same
  process. **Cold disk was not measured.** `purge` needs sudo, so the OS page cache was probably warm
  for all "first" numbers. Expect about +1 ms per 3 MB read from a cold SSD.
- Builds are single-process Python loops, except D2, which is one multi-threaded DuckDB statement.

### Candidates as implemented

- **A** (pure stdlib): SQLite only. Each row is (run, key, width, chunk) with one `array('d')` blob
  holding min, max, sum, count and last for 1024 buckets. Widths are 16, 64, 256, 1024 and 4096 steps,
  aligned to fixed step multiples so they are append-friendly. An append rewrites only the tail chunk
  of each level. I verified that an incremental build is byte-identical to a full build. Exact data is
  read back from the JSONL through sparse (step, byte offset) marks taken every 1024 lines. A chart uses
  the finest level with ≤1000 buckets and falls back to raw JSONL for windows of ≤1000 steps. The build
  uses `json`.
- **B**: SQLite for metadata plus per-(run, key) files `<key>.s` (int64) and `<key>.v` (float64), appended
  raw. Files under 1 MB are read with `np.fromfile`, larger ones with `np.memmap`. Downsampling uses
  `np.minimum/maximum.reduceat`, or `tsdownsample.MinMaxDownsampler`. Ingest parses with orjson.
- **C**: SQLite `m(run, key, step, value) PRIMARY KEY(run, key, step) WITHOUT ROWID`. Buckets come from
  `GROUP BY (step-lo)*nb/span`, with one query per run. WAL mode, `synchronous=NORMAL`.
- **D1**: DuckDB over Parquet. Each ingest batch writes one wide part file per run (`COPY ... FROM
  read_json`). Queries use `read_parquet([...], union_by_name)`. Ingest offsets live in SQLite.
- **D2**: DuckDB native long table (run, key, step, value). The build is a single
  `read_json → UNPIVOT → ORDER BY` over all files.
- **E**: B's files read with `mmap` + `memoryview.cast` + `bisect` + builtin `min`/`max`, without numpy.

## W1: ingest

| | A | B | C | D1 | D2 |
|---|---|---|---|---|---|
| Full build S (s) | 29.2 | 15.3 | 39.0 | 9.8 | 6.6 |
| Full build M (s) | 145.9 | 65.0 | 198.0 | 45.3 | 40.0 |
| Full build L1 (s) | 78.9 | 14.8 | 52.4 | 2.1 | 5.3 |
| Index size M | 787 MB | 1.93 GB | 2.89 GB | 794 MB¹ | 1.01 GB |
| Index size L1 | 204 MB | 480 MB | 1.37 GB | 255 MB¹ | 194 MB |
| Incremental, 1000 lines, S (ms) | 27 | 14 | 30 | 15 | 24 |
| Incremental, M (ms) | 30 | 71 | 29 | 15 | 28 |
| Incremental, L1 (10M-step run) (ms) | 26 | 24² | 20 | 28³ | 19³ |

Incremental time covers everything from the append until it is queryable: ingest, commit, and a chart
query that returns the new tail.
¹ D1 also keeps `_t`. ² The first run measured 231 ms and a rerun 24 ms; I treat the first as a page-cache
outlier. ³ After fixing my `tail()`, which first read the whole 1.3 GB file (that version took 976 ms and
292 ms).

JSONL source sizes for comparison: S 848 MB, M 4.2 GB, L1 1.3 GB. The index costs 0.2 to 0.7× the
JSONL size, except C, which is the largest.

### JSONL scan speed (50 runs, 222 MB, 500k lines × 14 fields)

| Parser | MB/s | lines/s |
|---|---|---|
| `json.loads` per line | 52 | 117k |
| `orjson.loads` per line | 242 | 546k |
| columnar `read_jsonl` with `json` (dict → per-key `array`) | 43 | 98k |
| columnar `read_jsonl` with `orjson` | 116 | 261k |
| `pyarrow.json.read_json` per file | 459 | 1.03M |
| DuckDB `read_json` over all 50 files, 1 query | 357 | 803k |

## W2: chart (50 runs × `train/loss`, full range, ≈1000 points per curve)

| ms (first / warm) | A | B numpy | B tsdownsample | E (no numpy) | C | D1 | D2 |
|---|---|---|---|---|---|---|---|
| S | 8.8 / 7.4 | 9.8 / 8.6 | 9.8 / 10.4 | 65 / 88 | 144 / 144 | 23 / 22 | 23 / 21 |
| M | 11.0 / 10.3 | 9.4 / 8.3 | 9.6 / 10.2 | 80 / 55 | 143 / 146 | 27 / 23 | 23 / 23 |

## W3: zoom (L1, ≈1000 points)

| ms (first / warm) | A | B numpy | B tsd | E | C | D1 | D2 |
|---|---|---|---|---|---|---|---|
| 1% window (100k steps) | 0.23 / 0.21 (level 256, 391 buckets) | 12.7 / 10.7 | 10.2 / 8.7 | 7.3 / 7.0 | 26 / 26 | 9.9 / 9.6 | 2.4 / 2.1 |
| 0.01% window (1000 steps) | 6.9 / 6.5 (raw JSONL via offset marks) | 7.6 / 8.1 | 8.0 / 8.2 | 1.0 / 0.7 | 0.48 / 0.48 | 8.9 / 8.0 | 1.6 / 1.4 |

B's roughly 8 ms floor on L1 is per-call `np.memmap` and numpy overhead on an 80 MB mapping. E reads
the same files through `mmap` + `memoryview` in 0.7 ms, so `np.frombuffer(mmap)` would most likely close
that gap. I did not test that.

## W4: exact mean of `train/loss` over steps [2000, 7999]

| s (first / warm) | A levels⁴ | A JSONL orjson | A JSONL json | B | E | C | D1 | D2 |
|---|---|---|---|---|---|---|---|---|
| S, 200 runs | 0.017 / 0.013 | 1.83 / 1.85 | 10.3 / 10.4 | 0.078 / 0.027 | 0.047 / 0.038 | 0.16 / 0.08 | 0.032 / 0.032 | 0.021 / 0.016 |
| M, 500 runs | 0.43 / 0.042 | 4.6 / 4.6 | 26.2 / 26.8 | 0.35 / 0.066 | 0.11 / 0.094 | 0.49 / 0.21 | 0.082 / 0.080 | 0.18 / 0.076 |

⁴ The levels give an exact answer only because the window is aligned to the 16-step grid (sum/count of
whole buckets). Any other window needs the JSONL path. All candidates return the same checksum
(629.156126 at M), so all results are exact.

## W5: run table (10k runs, `config.optimizer == 'adam'`, sort by `summary["val/acc"]`, top 100)

| Variant | Build | Query first / warm |
|---|---|---|
| No index: scan 30k JSON files | — | 1.19 / 0.59 s |
| SQLite, config/summary as JSON text, `->>` in WHERE/ORDER BY | 1.6 s, 4.3 MB | 12.6 / 9.9 ms |
| SQLite, load all rows + filter in Python | (same) | 73 / 73 ms |
| SQLite, fresh process incl. interpreter (one-shot) | — | 38 ms |
| DuckDB in-memory table from `read_json` over the 30k files | 1.4 s | 6.3 / 1.9 ms |

## W6: one-shot CLI (fresh `python bench.py oneshot`, answers W2)

| ms, median of 7 | A | B | E | C | D1 | D2 |
|---|---|---|---|---|---|---|
| S | 55 | 130 | 165⁵ | 204 | 171 | 183 |
| M | 59 | 115 | 101 | 205 | 187 | 188 |

⁵ Noisy, since E's warm W2 alone is 55 to 88 ms.

Interpreter start and imports (fresh process, median of 10, includes the ≈20 ms start):

| `python -c` | ms | Over bare start |
|---|---|---|
| `pass` | 20 | — |
| `pass` with `-I -S` | 16 | −4 |
| `import json` / `import sqlite3` | 27 / 26 | +6 |
| `import orjson` | 39 | +19 |
| `import numpy` | 87 | +67 |
| `import tsdownsample` (pulls numpy) | 89 | +69 |
| `import duckdb` | 118 | +98 |
| `import pyarrow` | 136 | +116 |
| `import numpy, duckdb, pyarrow` | 207 | +187 |
| `uv run --no-project ... python -c pass` | 180–250 | +160–230 |

## Observations

- **Python startup and imports dominate one-shot latency.** On W2, A's query takes 10 ms and its whole
  process 55 ms. B's query takes 8 ms, but its process takes 115 ms, mostly numpy's import (+67 ms).
  DuckDB's import alone (+98 ms) costs more than any of its queries. `uv run` adds another 160 to 230 ms
  per call, so the CLI must run as an installed console script and never through `uv run`.
- **Spike preservation:** all candidates keep every spike that can be kept at the resolution. At M,
  0/300 spikes are missed; on L1 zooms, 1/1. At S, 5/300 are "missed" (4/300 for A, whose grid differs).
  I checked each one: it shares its 20-step bucket with a larger spike of the same series, which
  min/max downsampling cannot show by construction. tsdownsample gives identical coverage.
- **Plain SQLite (C) is the slowest and largest.** GROUP BY in SQLite processes about 3.5M rows/s, so
  W2 takes 145 ms. The index is 2.9 GB, the biggest of all and 24 bytes per point, and the build is the
  slowest at 200 s. It is fast only for tiny exact windows (0.5 ms).
- **DuckDB is fast and compact but has a cost floor.** Every query costs about 20 ms however small, and
  the import costs 100 ms. D1 (Parquet) builds L1 fastest (2 s) thanks to its C++ JSON reader. However,
  every incremental append adds a part file, so a live run needs compaction. D2 needs a single-writer
  process: DuckDB takes an exclusive file lock, so the server and CLI cannot both write to it.
- **Pure-Python ingest is the bottleneck, not storage.** Parsing to columns runs at 98k lines/s with
  `json` and 261k with orjson. A full M rebuild takes 1 to 3 minutes in one process. It parallelizes
  across runs trivially (8 cores), and pyarrow/DuckDB's readers are 4 to 10× faster. Incremental ingest
  is 15 to 30 ms for every candidate at every scale, so live updates are not a differentiator.
- **A's precomputed levels are the fastest for charts at any range length** (0.2 ms for a 1% zoom of
  10M steps) and need no numpy. A has three weaknesses as implemented:
  1. It stores full-density levels even for sparse `val/*` keys, so 8 of 20 series waste space. The
     fix is to start at a width matched to the key's density, or to skip empty chunks.
  2. Exact queries over arbitrary windows go back to the JSONL: 4.6 s with orjson and 27 s with `json`
     for 500 runs × 6000 lines.
  3. It is the most code (the tail cascade of levels) and builds slowest because it is pure Python.
- **E (no numpy) is competitive on small requests.** It is the fastest exact zoom after C (0.7 ms). It is
  6× slower than numpy on 50 × 10k-point charts (55 ms against 8 ms), but because it skips numpy's
  import, its one-shot time ends up level with B's.
- `np.memmap` has a measurable per-call overhead (≈8 ms floor on L1 zoom). A plain `mmap` +
  `np.frombuffer` would likely avoid it.

## Ranking

1. **B (SQLite metadata + raw append-only column files), reading through `mmap`.** It is the simplest
   design: ingest is "append bytes", there are no levels to maintain, and a corrupt cache is deleted and
   rebuilt. It is fast on every workload (8 to 11 ms charts, ~10 ms zooms, exact aggregates in
   ≤70 ms warm for 500 runs) and needs no precomputation, so any window and any aggregate is exact. The
   costs are disk size (16 B/point, 1.9 GB at M; float32 values or delta-encoded steps would cut that by
   30 to 50%) and the numpy import (+67 ms per CLI call). The stdlib read path (E) on the same files
   avoids the import for one-shot calls. A combination would serve one-shot CLI and MCP calls with E's
   pure-Python reader (~60 to 100 ms total) and the long-lived `beamtime serve` with numpy.
2. **A (stdlib levels).** It has the best one-shot latency (55 ms) and the best large-range charts.
   However, exact data comes only from JSONL, so it needs B's raw files anyway for exact windows. With
   those, A turns into "B plus a level cache", an optimization that can be added later if charts over
   10^7+ step runs become common. It is not a starting point.
3. **D2 / D1 (DuckDB).** These are the most compact (D2 194 MB for L1) with the fastest bulk ingest, and
   D2's 2 ms L1 zoom is excellent. The ~100 ms import, the ~20 ms per-query floor, the exclusive write
   lock (D2) and part-file compaction (D1) make them worse for an agent-driven CLI. They are fine as an
   optional analytics backend over exported Parquet.
4. **C (SQLite long table).** It is the largest, the slowest to build and the slowest to chart. It is only
   competitive for tiny exact windows.

The run table (W5) does not discriminate between candidates. SQLite with JSON columns answers in 10 ms
(38 ms as a fresh process) and builds in 1.6 s, so keep run metadata in SQLite whichever metric store
wins.

## Shortcuts and caveats

- M runs 200 to 999 are hardlinked copies of runs 0 to 199, so the content repeats 5×. Every index and
  every query still processes all files. I measured with the data actually at M scale and did not
  extrapolate.
- The OS page cache was not purged (no sudo), so "first" means cold process and SQLite cache but warm OS
  cache.
- Builds are single-process, except D2's single multi-threaded statement. Python-loop builds would gain
  up to 8× from per-run multiprocessing, and none was tried.
- A's W4 levels result relies on a grid-aligned window, and A's edge buckets of a chart can include up to
  15 steps outside the requested range.
- Each workload ran once per process with 3 to 5 warm repeats, not many trials, so single-digit-ms
  differences are within noise. Example: E's S one-shot was 165 ms and its M one-shot 101 ms.
- float32 value storage, delta/compressed steps and `np.frombuffer(mmap)` for B were not measured.
- Generated data (about 2.3 GB) and all indexes were deleted after the run. Only the scripts,
  `results.jsonl` and this file remain.
