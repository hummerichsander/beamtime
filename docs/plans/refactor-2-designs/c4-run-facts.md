# C4: run facts belong to the query layer, not the G4 tools

Recommendation: **Shape B** (two new run fields + an internal `query/facts.py`); a new query kind is rejected. Dependency category: local-substitutable, seam internal.

## 1. Verified diagnosis

**`members()` — `src/beamtime/ops/reading.py:214-237`.** Confirmed: runs a `runs` query and unpacks `row[0]`…`row[5]` by position. Is it actually fragile? Less than claimed, but it is a trap. With an explicit `select` and no `by`/`seeds`, `runs_kind` deterministically answers `columns = ["run.id", *select]` (`query/kinds.py:71-72`), and `members()` never passes `by`/`seeds`, so nothing reorders the columns *today*. What would: (a) ever passing `by`/`seeds` — an aggregate answer prepends a `"runs"` column (`kinds.py:69`) and every index shifts by one, silently; (b) any change to `runs_kind`'s column layout — exactly what C1 and C5 touch. The answer carries `columns`; `members()` duplicates that part of the interface instead of reading it. **The depth problem is bigger than the fragility**: `members()` is a shallow adapter over the query that every tool then *bypasses* to read files.

**Every direct file read in the group tools** (the single-run ops `card` :866-937, `resume` :1015-1046, `output` :979-1012 also read files, but the spec sanctions that — "card and preview … small enough to read directly", 03-index.md:180-181):

| Site | Read | Serves |
|---|---|---|
| `entity_config` :309 | `read_config(m["dir"])` | compare: config diff |
| `last_values` :323-325 | `read_card(run_dir).metrics[*].last` | compare: metric table |
| `best_per_setting` :419-423 | `read_card(m["dir"])` (exists check + stats) | digest |
| `best_per_setting` :427 | `read_config(m["dir"])` | digest |
| `failures` :455 | `read_card(m["dir"]).error` | digest |
| `logs` :529 | `read_output(m["dir"], rank)` | logs (output text) |
| `logs` :537 | `read_card(m["dir"]).error` | logs |
| `diagnose` :653 | `read_card(m["dir"])` | diagnose |
| `diagnose` :673 | `mtime(m["dir"] / c.METRICS)` | diagnose: stalled |
| `diagnose` :675 | `read_run_info(m["dir"]).attempts` | diagnose: restarts |

All except `read_output` duplicate data the index already holds (`card`, `config`, `info` JSON columns; `fields.py:36-49` serves `run.error`, `run.steps`, `metric.X.<stat>`; `run.status` derived with `ctx.now` in `select.py:271-272`). Two facts the index holds but no field exposes: attempts count (`info.$.attempts`) and metrics freshness (ingest records `metrics_size` at `ingest.py:97,203` but not the mtime diagnose wants).

**Inverted layering — confirmed.** `reading.py:589` imports `beamtime.cli.conditions.parse_where` inside `wait`. `tests/test_boundaries.py` checks only `sdk`/`format`/`synth`, **and only module-level imports** (`module_level()` skips function bodies), so this edge is doubly invisible.

**Two failure rules — confirmed.** `failures()` :447-461 groups failed/killed/lost by `failure_signature(card.error)`; `logs` :536-538 groups failed only, by `failure_signature(trace[-1] if trace else card.error)` — the output's *last* traceback can postdate the card's recorded error (e.g. a second error at teardown), so the same run can carry two signatures.

**Coverage — one correction to the walk.** The tools *do* work over snapshots and routed remotes today: `routed()` forwards the whole op to a live remote (file reads happen there), and `from_snapshot` (`remote/route.py:132-165`) swaps `ctx.logdir` for the snapshot folder, which holds cards, configs and output with remote mtimes preserved (`pull.py:100-101`). The real gaps: these ops are not `listing=True`, so `from: "."` never federates across sources; and nothing tests them over a snapshot (`tests/ops/test_tools.py` goes through `ops.call` on a local synth dir only; its one `routed` use, :55, tests only the two-source refusal of `compare`). The file reads make the snapshot path *fragile in semantics* (diagnose's `stalled` stats a file live rather than judging at the snapshot's `now`) rather than non-functional.

## 2. The interface, designed twice

### Shape A — a new `facts` query kind (rejected)

```yaml
facts:
  from: scaling/lr-sweep
  where: {run.status: failed}
  depth: all
  include: [config, metrics, failure, attempts, freshness]   # closed set
```

Answer: `{"kind": "facts", "entries": [{run, name, status, code, group, path, error, steps, attempts, last_logged, config: {...}, metrics: {...}}], "meta": {...}}` — per-run dicts, not columnar. msgspec `Facts(Selection)` struct in `query/models.py`; federates for free once a listing kind.

### Shape B — deepen `runs`/fields + an internal `run_facts` aggregate (RECOMMENDED)

Two small additions to the *existing* external interface, and one new internal module:

1. **Two new run fields** (`query/fields.py`): `run.attempts` → `json_array_length(info, '$.attempts')`; `run.last_logged` → a new `metrics_mtime` column written at ingest (schema version bump; caches rebuild, as the spec already did for `links`). Both become usable in any `runs`/`where`/`sort` — leverage for every caller, not just the tools.
2. **`query/facts.py`** — the interface the tools consume:

```python
@dataclass(frozen=True)
class RunFacts:
    id: str; name: str | None; status: str; code: str | None
    group: str; path: str; dir: Path          # dir: logdir / path, for output text only
    error: str | None; steps: int | None
    attempts: int; last_logged: float | None
    config: dict[str, Any] | None             # flattened; only when asked
    metrics: dict[str, dict[str, Any]] | None # card stats by key; only when asked

def run_facts(index: Index, *, scope: str, run_id: str | None, now: float,
              where: dict | None = None, depth: Any = "all",
              config: bool = False, metrics: bool = False) -> list[RunFacts]: ...
```

Implemented on `select_runs` (which already fetches `_config` whole when asked) plus one decode of the card's `metrics` JSON — **zero file reads**. **Invariants:** one index open + one `catch_up` per call (makes `wait`'s poll loop cheaper than today's three `members()` queries per tick); `status` is `derived_status(now)`; `config`/`metrics` are `None` unless requested, so `wait` never pays for them; everything is index-backed, so it answers identically over a snapshot folder with the snapshot's `now`. **Error modes:** `QueryError` exactly as `query.run` raises it; `ops/reading.py` keeps a 6-line `run_members(ctx, target, where, depth, *, config, metrics)` wrapper that resolves `from`, maps `QueryError → OpError` (same policy as `evaluate`, :73-76) and passes `ctx.now` — error policy stays local to ops.

### Why Shape B

- **Depth:** B hides the same implementation (SQL, JSON paths, derived status, code identity, flattening, freshness) behind a *smaller* interface: one function and two fields, versus a ninth query kind with its own answer schema, msgspec struct, CLI command, MCP tool, merge case and spec section. A's interface grows almost as fast as what it hides — shallow.
- **Deletion test:** delete A and little vanishes — most of its entries are already expressible as `runs` fields; it's largely a pass-through over `select_runs`. Delete B's `run_facts` and the card/config decoding reappears in five tools — it earns its keep.
- **Locality:** either shape concentrates run-file knowledge below `query/`; B also upgrades the public field catalog, so `--where run.attempts>1` works everywhere, and views/`kinds.py` can reuse the same facts.
- **Seam placement:** the dependency is local-substitutable; there is exactly one implementation — one adapter means a hypothetical seam, so no port at query's external interface; the seam stays internal, which is precisely B. The *existing* external seam that varies (local logdir vs snapshot folder) already sits at `logdir`, and B rides it.
- **No-overengineering:** the brief's own caution holds. Eight kinds stay eight.

## 3. Usage after the change

```python
# digest (reading.py)
facts = run_members(ctx, p.group, config=True, metrics=True)
answer["runs"] = dict(Counter(f.status for f in facts))
answer["best"] = best_per_setting(facts, metric, stat)      # f.metrics[k][stat], f.config
answer["failures"] = failures(facts)                        # failure_key(f.error, None)

# diagnose
facts = run_members(ctx, p.from_, p.where, p.depth, metrics=True)
# flags: f.metrics stats (nonfinite, diverging via slope_last10pct);
# stalled: f.status == "running" and now - (f.last_logged or 0) > STALLED_S
# restarts: f.attempts - 1;  stopped_early: f.steps vs group median

# logs
facts = run_members(ctx, p.from_, p.where, p.depth)
lines = read_output(f.dir, rank=p.rank)                     # the one remaining file read: output text
trace = last_traceback(lines)
sig = failure_key(f.error, trace)

# wait
from beamtime.query.conditions import parse_where
condition = None if p.until == "finished" else parse_where([p.until])
before = {f.id: f for f in run_members(ctx, p.from_, p.where, p.depth)}   # cheap: no config/metrics
```

**`parse_where` lands in `query/conditions.py`** (moved whole from `cli/conditions.py`; the compact condition string is part of the query language's surface per 03-index.md:411-422, not a CLI ornament). `cli/__init__.py:227` imports from the new home; `wait` stops crossing into `cli`. Messages take an optional flag name (default `--where`; `wait` passes `until`).

**`tests/test_boundaries.py` newly enforces:** a second test that scans *all* imports (not `module_level` — walk function bodies too) in `query/`, `index/`, `ops/`, `record/`, `remote/`, `format/`, `sdk/` and asserts none names `beamtime.cli` or `beamtime.mcp`. That is the guard the current test misses and the one that would have caught `reading.py:589`.

## 4. What the implementation hides behind the seam

Run-file formats and locations (`_card.json`, `_config.json`, `_run.json`, `_metrics.jsonl` and their `c.*` names disappear from `reading.py`'s group tools); the SQLite schema and JSON paths; derived status (heartbeat vs `now`); the code-identity SQL; attempts counting; metrics freshness (the new `metrics_mtime` ingest column — diagnose no longer stats files, so `stalled` is judged at `ctx.now` and is correct over snapshots); config flattening; catch-up and its budget; snapshot-vs-live logdir. **Deliberately not hidden:** `RunFacts.dir` and `read_output` — output text is not a number, "runs are plain directories" is the product philosophy, and an output-text accessor in `query/` would be a one-adapter seam with no second adapter in sight.

## 5. One failure-signature rule

One function, in `query/facts.py` next to the facts it reduces:

```python
def failure_key(error: str | None, traceback: list[str] | None) -> str:
    """signature(error) if the card recorded one, else signature of the traceback's exception line."""
```

with today's `failure_signature` regex as the shared reduction. `digest.failures` passes `(f.error, None)` — unchanged behaviour, still groups failed/killed/lost. `logs` passes `(f.error, trace)` — the *card's* error now leads; the output traceback remains the displayed detail and the fallback for runs that died before writing a card. Each tool keeps its population (failed/killed/lost vs failed-only); only the key rule is shared, so **one run can no longer carry two signatures**. **Answer schema:** unchanged on both — digest keeps `{status, signature, count, runs}`, logs keeps `{signature, runs, traceback}`; only signature *values* can shift for runs where card and output disagreed, and signatures are grouping labels, not identifiers, so readers accept old answers forever. Write that sentence into the spec.

## 6. Testing

- **Survive:** all of `tests/ops/test_tools.py` — it tests through `ops.call` at the ops interface, which is unchanged. `test_logs_group_tracebacks_by_signature` (:84) asserts the signature value `"FloatingPointError: train/loss is inf"`; synth writes the same traceback into the card's error, so it should stay green — if it doesn't, that is the rule unification showing, and the assertion moves to the card-led value (replace, don't layer).
- **Die:** nothing — no test reaches `members()` or the helpers directly. `members()` itself is deleted with its callers.
- **New, at the interface:** `tests/query/test_facts.py` over the `synth` logdir — statuses derived at `now`, `where` filtering, flattened config on request, `attempts`, `last_logged` after ingest, `QueryError` for a bad target; plus the two new fields through ordinary `runs` queries; plus the strengthened boundary test.
- **Snapshot capability becomes testable:** one test that builds a snapshot-shaped folder (copy a synth group, preserve mtimes, write `_snapshot.json`) and runs `digest`/`diagnose` through `routed`'s `from_snapshot` path, asserting `stalled` is judged at the snapshot's time. Live-remote federation of these tools stays out of scope here (C1).

## 7. Migration path (each step green)

1. **Move `cli/conditions.py` → `query/conditions.py`**; update the two import sites (`cli/__init__.py:227`, `reading.py:589`); strengthen `test_boundaries.py` (all-imports ban on → cli/mcp). ~S, no behaviour change.
2. **Add `run.attempts` field; add `metrics_mtime` at ingest + `run.last_logged` field**; schema version bump; update 03-index.md fields table and implementation notes. ~M.
3. **Add `query/facts.py`** (`RunFacts`, `run_facts`, `failure_key`) + `tests/query/test_facts.py`; add the `run_members` wrapper in `reading.py`. Nothing consumes it yet. ~M.
4. **Switch `wait`, `diagnose`, `logs`** to `run_members`; delete their `read_card`/`read_run_info`/`mtime` reads; logs adopts `failure_key`. ~M.
5. **Switch `compare` and `digest`** (`entity_config`, `last_values`, `best_per_setting`, `failures` rewritten over `RunFacts`); **delete `members()`**. ~M.
6. **Snapshot test + spec write-back**: 03-index.md (conditions module home; new fields; `metrics_mtime`; "run facts come from the index; one failure-signature rule; signature values are labels, not identifiers"). ~S.

## 8. Interactions

- **C1 (remote answer seam):** `run_facts` is already a `runs`-shaped selection, so federating the tools reduces to sending it through that seam — it needs whole-config/whole-metrics to be requestable over the wire (an API param or two pseudo-fields) and per-source entry concatenation; until then the tools keep today's route-whole-op behaviour, which `run_facts` does not worsen.
- **C5 (params declared once):** same file; **land C4 first** — it deletes `members()` and shrinks `reading.py`'s parameter plumbing, and `run_members` consumes exactly the shared `(from, where, depth)` Selection triple that C5 wants declared once.

### Critical files
- src/beamtime/ops/reading.py
- src/beamtime/query/fields.py (plus the new src/beamtime/query/facts.py)
- src/beamtime/query/select.py
- src/beamtime/index/ingest.py (metrics_mtime; with index/store.py schema)
- tests/test_boundaries.py (with docs/design/03-index.md for the write-back)
