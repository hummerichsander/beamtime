# C6: one curve shape instead of three guessed variants

Recommendation: **Design A** (canonical envelope, additively emitted at the source). Dependency category: in-process.

## 1. Verified diagnosis (current line refs)

The `series` kind is hot (kinds.py: 24 changes in the last 300 commits; curves.ts 11; kit/shape.ts 1) and emits three untagged curve shapes that every consumer re-detects by probing.

**Producers** (all in-process, module `beamtime.query`):
- `src/beamtime/query/read.py:102-151` `downsample` → `{raw: True, x, y}` or `{raw: False, width, x, first, min, max, last, count}`.
- `src/beamtime/query/read.py:153-199` `from_preview` → the downsampled shape with `first: [None]*n`.
- `src/beamtime/query/kinds.py:217-265` `series_kind`; `:280-328` `run_curve` (adds `run, name, metric, monotone, source`, rewrites `x`/`step` for metric-x, `resumes` at 249-252); `:331-383` `grouped_curve`, `:385-445` `grouped_curve_by_x`, `:448-473` `band_stats` → `{by, runs, metric, width, x, mean, lo, hi, n}`.

**Consumers that guess the variant:**
- `src/beamtime/cli/format.py:118-146` `curve_line` — probes `"by" in curve` (123, 131) and `curve.get("raw")` (129, 133).
- `src/beamtime/ops/reading.py:800-841` `table_of` — curves branch 829-841; generic flattening (scalars as labels, point-length lists as columns), so the variant's field names leak into CSV headers.
- `web/src/bt/curves.ts:28-68` `reshape` — probes `"by" in c` (30) and `c.raw` (56); maps min→lo, max→hi, count→n, last→y, mean→y.
- `web/src/kit/shape.ts:40-52` `curve` — maps the **opposite** way: `c.min ?? c.lo`, `c.max ?? c.hi`, `c.count ?? c.n`. The two TS normalizers disagree on canonical names (bt: lo/hi/n; kit: min/max/count).
- `web/src/blocks/table.ts:120` `sparks` — `c.raw ? c.y : c.last` (**a fourth prober the walk missed**).
- Internal: `kinds.py:319` (`curve["x"] if curve["raw"] else curve["first"]`) and `kinds.py:262` (`meta.downsampled`).

**Mutator in transit:** `src/beamtime/remote/route.py:393-404` — `merge` wraps grouped curves' labels as `{"source": src, **c["by"]}` when several sources answer. It touches only `by`, never the value arrays.

**Do curves persist on disk?** Only in HTML snapshot exports: `src/beamtime/views/export.py:311-315` writes full series answers into `snapshot.js` — but the export bundles its own frozen web app (`static/export/main.js`), so the reader is frozen with the data; no live reader ever decodes an old snapshot. `query/files.py` reads view data files as CSV/JSON/Parquet tables, not curves. Figure CSVs are write-only. **The real forever-compat surface is the remote wire:** `docs/design/04-remotes.md:217-227` — same protocol major on both sides, "minor versions only add". A newer hub will receive old untagged curves from an older remote forever (within a major), and an older hub must keep understanding a newer remote's answers.

**Does the kit expose curve shapes to block authors?** **Yes, as a public interface with compatibility expectations**: `src/beamtime/guide/parts/kit-api.md:7` and `docs/design/05-views.md:353-355` document curves to user-written block code as `{run, key, group, x, y | min, max, last, mean, count}`, and `05-views.md:337-338` promises "Version 2 only adds to version 1". So `min/max/last/mean/count` must keep flowing to kit blocks; **renaming them is off the table.** Additions are allowed.

## 2. The interface, designed twice

### Design A — canonical envelope, additively emitted at the source (RECOMMENDED)

Every curve the kind emits carries, besides its existing fields, one uniform drawing set:

```
{ ..., x: [..], y: [..], lo?: [..|null], hi?: [..|null], n?: [..] }
```

- raw: already is the envelope (`x, y`); no `lo/hi/n`.
- downsampled: gains `y = last`, `lo = min`, `hi = max`, `n = count`.
- grouped: gains `y = mean` (`lo/hi/n` already carry the right names today).

**Invariants:** `len(y) == len(x)`; `lo[i] <= y[i] <= hi[i]` wherever all three are numbers; `band: none` ⇒ `lo/hi` all null; `raw` and `by` remain honest facts (fidelity, group label) but no consumer branches on them to *find values*. **Error mode:** none new — a curve without `y` is a bug, not a variant.

### Design B — explicit `shape: "raw" | "downsampled" | "grouped"` tag (rejected)

Each curve gains a tag; readers switch on it instead of probing. Invariants: `shape=raw ⇒ x,y`; `shape=downsampled ⇒ x,first,min,max,last,count,width`; `shape=grouped ⇒ by,runs,x,mean,lo,hi,n`. Error mode: unknown tag ⇒ fall back to legacy probes.

### Why Design A

- **Depth.** A consumer learns four fields and can draw anything; the three vocabularies disappear behind the kind. Design B is **shallow — it legalizes the guessing** rather than removing it: every consumer still carries a three-way mapping, and the bt/kit naming disagreement survives. Deletion test: delete B's tag and the probes just come back; delete A's envelope and four consumers regrow min/last/mean mapping tables.
- **Locality.** The min→lo knowledge lives once, in `read.py`/`band_stats`, next to the code that computes those numbers. Today it lives in four consumers in two languages, two of which contradict each other.
- **Seam placement.** The seam stays where it is — the kind's answer — which is the interface the spec (`03-index.md`) already names the test surface. One extra adapter: **`upgrade_curve` at the remote merge seam** (`route.py`), so a newer hub normalizes answers from older remotes; that gives the hypothetical "old shape" seam its second adapter (local kind + remote upgrade) and keeps the legacy knowledge in exactly one Python function forever. CLI/web/kit only ever see same-version or upgraded answers, so they keep zero legacy code.
- **Schema-forever rule.** Design A is purely additive: old fields keep being emitted (satisfying the kit:1 contract and older hubs under "minors only add"), old untagged answers keep decoding via `upgrade_curve` at the hub. **Cost:** downsampled answers carry 4 duplicate arrays (~1.7× JSON, cheap under gzip, bounded by the 30k-point chart budget); retiring the duplicates is a parked ticket for the next protocol major. Deviation to write back into `docs/design/03-index.md` (series spec, ~329-331 and 452-458) and `05-views.md` (kit reshaping, ~353-355).

## 3. Usage after the change

- `format.curve_line`: one path — `ys = curve["y"]`; band lows/highs from `lo/hi` else `y`; label from `by` or `name`; probes at 123-136 die (~10 lines shorter).
- `table_of`: code unchanged (generic flattening) plus a tiny generic dedup: identical arrays collapse to one column, envelope names preferred — no variant knowledge, and CSVs don't double in width.
- `curves.ts reshape`: lines 51-63 collapse to `y: c.y ?? []`, `lo: c.lo ?? null`, `hi: c.hi ?? null`, `n: c.n ?? null`. `"by" in c` stays only for labelling (a real fact, not a value probe). `blocks/table.ts:120` becomes `c.y`.
- `kit/shape.ts`: **this normalizer dies.** The cross-mappings `c.min ?? c.lo` etc. become plain passthrough of the answer's own fields (both vocabularies are present); `KitCurve` additively gains `lo/hi/n` and the uniform `y`, documented in kit-api.md — allowed since kit versions only add.

## 4. What the implementation hides behind the seam

Preview-vs-columns sourcing, bucket math and fixed edges, band statistics and the band kinds, point budgeting, which fidelity fields exist per variant, the legacy upgrade of old remotes' curves, and (unchanged) the merge's `by.source` labelling — merge stays shape-agnostic because it never needed the value arrays.

## 5. Testing

- **Survive:** everything in `tests/query/test_queries.py` (asserts on `raw/min/max/mean/n` — all retained), `tests/remote/test_federation.py:48-51` (`by.source` untouched), kit tests.
- **Die/rewritten:** `web/test/curves.test.ts:6-18` fixtures encode the untagged shapes; rewritten to envelope fixtures in the same step the reshape branches die.
- **New, at the kind's interface** (the `ask` fixture, one per variant): raw ⇒ `y` present, no band; downsampled ⇒ `y==last, lo==min, hi==max, n==count`, `lo<=y<=hi` pointwise; grouped ⇒ `y==mean`, `band: none` ⇒ null band. Plus the **forever-compat test**: a pinned old-shape answer fixture (never regenerated) pushed through `merge`/`upgrade_curve` comes out enveloped.

## 6. Migration path (each step green)

1. **Emit the envelope** in `read.py` (`downsample`, `from_preview`) and `kinds.py` (`band_stats`/grouped out-dicts); new interface tests; write the deviation back into `03-index.md`. (~0.5 d, Python only.)
2. **Python consumers read it**: `curve_line` single path, `table_of` dedup, clean `kinds.py:319`. (~0.5 d.)
3. **Route seam**: `upgrade_curve` applied to remote answers in `merge`, pinned-fixture test in `tests/remote`; note in `04-remotes.md`. (~0.5 d.)
4. **Web reads it**: `reshape` and `blocks/table.ts` drop probes, rewrite `curves.test.ts` fixtures; `cd web && npm ci && npm test && npm run build`, commit rebuilt `src/beamtime/serve/static/`. (~0.5-1 d.)
5. **Kit passthrough**: delete shape.ts cross-maps, add envelope fields to `KitCurve`; update `kit-api.md` and `05-views.md`; rebuild + commit bundle. (~0.5 d.)
6. **Parked** (next protocol major): stop emitting the duplicate legacy arrays; `upgrade_curve` stays forever.

## 7. Interactions

- **C1 (federated series merging):** the envelope keeps `merge` shape-agnostic — it rewrites `by` and never inspects value arrays; a tagged form (Design B) would have forced merge to switch on shapes, another reason for A.
- **C3 (chart settings, line.ts):** orthogonal — `prefs.raw` in line.ts is a display preference, not the curve variant; line.ts only gets a simpler `reshape` underneath it. **Land C3's web step before C6's web step** (both edit line.ts's call-building).

### Critical files
- src/beamtime/query/read.py
- src/beamtime/query/kinds.py
- web/src/bt/curves.ts
- src/beamtime/remote/route.py
- web/src/kit/shape.ts
