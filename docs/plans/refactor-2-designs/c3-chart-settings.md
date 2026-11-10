# C3: one owner for a line chart's settings

Recommendation: **Shape A** (Python struct as source, generated TS constants at build time). Dependency category: in-process.

## 1. Verified diagnosis (current line refs)

- `src/beamtime/views/model.py:40-69` — `Line` struct: `x="_step"` (:44), `band="minmax"` (:52), `smooth=0.0` (:54), `raw=True` (:66), `legend=True` (:67), `scale=None` meaning "guess" (:55-61). Structs are `omit_defaults=True` (:21) — dumping a `Line` already drops defaults.
- `src/beamtime/views/compile.py:280-327` — `Compiler.line` hand-writes "None when default" per prop (`x=n.x if n.x != "_step" else None` :315, `raw=None if n.raw else False` :319) and splits settings between props and `data.main.params` (`band` always explicit, `seeds/by/steps` when set, :291-297). `tree()` builds the added-chart `template` from the first line's call at :82-88.
- `src/beamtime/views/prefs.py:124-174` — `settle()` with its own defaults table (:158-172) and the hand-written inverse of the by/seeds encoding (:139-144, hard-codes `"config.seed"`). `settle_colormap` (:177-186) is the scatter/bar sliver.
- `web/src/blocks/line.ts:37-53` — `seriesCall` deletes/rebuilds `seeds/by/steps`, hard-codes `"config.seed"` (:47); `defaultsOf` (:67-85) hand-decodes props+params back into `ChartPrefs`.
- `web/src/bt/prefs.ts:97-103` — `effective()` base table at :101.
- `web/src/api.ts:73-82` — `frozenKey` strips `x === "_step"`, `band === "minmax"` (:78-79).
- `web/src/blocks/line-settings.ts:29-31` — `LINE_FIELDS` (panel layout, not defaults — may stay).

**New findings:**

- **The "None when default" wire encoding is NOT load-bearing for storage.** Views persist only as YAML (`view/<version>.yaml`, `views/store.py:39-61`); no `_view` files exist; compiled trees are never stored server-side. The only persisted compiled trees live inside `beamtime export --html` snapshots (`views/export.py:312-314`), and each export bundles **its own frontend copy** (`export.py:291-301`, `INDEX` at :323-339 loads `snapshot.js` + its own `main.js`). So the wire encoding only needs to be self-consistent within one build; `frozenKey` exists to reconcile recorded params with lookup params inside that same build. We *may* change the wire shape — but we don't need to, and shouldn't.
- **Third copy of two defaults** server-side: the series query struct re-declares `x="_step"`, `band="minmax"` (`src/beamtime/query/models.py:66-76`, mirrored `ops/registry.py:107`). That one is behind the API's own interface and stays.
- **Scatter/bar/histogram do not share the pattern.** `compile.py` passes their props verbatim as values (:105-156, no None-when-default) and `plots.ts` reads props with two inline fallbacks (`p.error ?? "std"`, `p.sort ?? "x"`, :144,147); only `colormap` flows through the prefs cascade (`plots.ts:26-30` ↔ `settle_colormap`). One real duplication axis (Line) = one real seam; a generic all-charts settings framework would be a hypothetical second adapter. **Fix Line only**, with the defaults table keyed by block name (`{line: {...}}`) so a second chart kind can join if it ever earns it.
- `web/src/kit/figure.ts` also calls `effective()` for custom figures — whatever owns the cascade must stay importable from both bundle entries (`main.ts` and `kit/frame.ts`).
- **Precedent for build-time generation exists**: `scripts/build-tokens` (Python generates `design/tokens.css`, with `--check` failing when the committed file is stale; wired as npm script `tokens`). Shape A is this exact pattern.
- Minor, out of scope: the four x-axis clock labels are duplicated (`line-settings.ts:16-21` `X_AXES` vs `bt/axes.ts:8` `CLOCKS`); `guide/__init__.py:46` repeats the `seeds: config.seed` convention.

## 2. The deepened module, designed twice

The module: **chart-settings** — everything that maps between (a) the `m.Line` struct, (b) the compiled wire form, (c) the viewer's prefs as the web UI names them, and (d) the series call.

### Shape A — Python struct as source, generated TS constants at build time (RECOMMENDED)

**Python side** — new `src/beamtime/views/settings.py` (~100 lines):

```python
SEEDS_FIELD = "config.seed"          # the one home of the convention
SETTINGS = (...)                     # the settable Line fields, web-named
def line_defaults() -> dict[str, Any]   # derived from msgspec.structs.fields(m.Line)
def settle(props: dict, settings: dict) -> None   # moved from prefs.py
def wire_props(n: m.Line) -> dict[str, Any]       # the omit-when-default props for compile
def generated_ts() -> str            # the text of web/src/bt/chart-defaults.ts
```

`settle` is implemented by the deletion-test move: merge web-named settings into the node (folding `by: "seeds"` ⇔ `seeds: SEEDS_FIELD`, `by: k` ⇔ `by: [k]`), decode into `m.Line`, dump with `omit_defaults` — the hand-written table at `prefs.py:158-172` and the inverse at :139-144 vanish. `wire_props` is `msgspec.to_builtins(n)` restricted to the setting fields — the per-prop `!= default` lines in `compile.line` vanish.

`scripts/build-chart-defaults` (clone of `build-tokens`): writes `web/src/bt/chart-defaults.ts`; `--check` fails when the committed file is stale. One pytest calls `--check` — **that test is what pins the copies to each other.**

**TS side** — new `web/src/bt/chart-settings.ts` (~120 lines), importing the generated `DEFAULTS` and `SEEDS_FIELD`:

```ts
export function effective(node: Node, prefs: ViewPrefs): Effective   // decodes node, cascades
export function seriesCall(node: Node, prefs: Effective, opts: {zoom, width}): Call
export function normalizeSeries(params: Record<string, unknown>): Record<string, unknown>
```

`defaultsOf` becomes private to this module. `bt/prefs.ts` keeps storage and the cascade mechanics (`cascade(defaults, prefs, id)` — today's `effective`, base table deleted), which `kit/figure.ts` keeps using.

**Invariants** (the interface, beyond the signatures):
1. `m.Line` is the only place a setting's name, type or default is written; generated TS, `settle`, `wire_props`, `normalizeSeries` all derive from it.
2. On the wire, a setting at its struct default is absent. **Exception**: `scale` is always present and resolved (compile's loss guess, `compile.py:302-303`); never defaultable on the wire, and `settle` keeps writing it explicitly (`prefs.py:146-147`). `DEFAULTS.line.scale = "linear"` is the UI fallback only.
3. Round-trip law: for any settings `s`, decoding `compile(settle(props, s))` yields `defaults ⊕ s`.
4. Unknown setting keys are dropped silently (old localStorage prefs, future frontends — today's `case _: pass`).
5. `seeds` and `by` are mutually exclusive; the fold is owned by this module on both sides.

**Error modes**: a stale generated file fails at build/test time, never at runtime; `settle` on invalid values raises `SchemaError` (already mapped to `OpError` code 3 in `ops/views.py:617-619`). No new runtime failure anywhere.

**Encode/decode pairs**: Python pair (`wire_props` encode / `settle` decode) in `views/settings.py` next to the struct; TS pair (`defaultsOf` decode / `seriesCall` encode) in `chart-settings.ts`. Two adapters of one vocabulary = the seam is real; the generated file + `--check` test is the pin.

### Shape B — defaults served at runtime through `meta` (rejected)

`api.py meta()` (already serving `colormaps` the same way, :241-242) grows `"chart_defaults": {"line": {...}}`; the shell fills a `Store` in `chart-settings.ts`; `effective`/`normalizeSeries` read the store. Same Python side; no generated file.

**Why it loses**: the defaults become *async-available*, which widens the interface of every consumer — `effective` and `frozenKey` must either block, tolerate `undefined`, or fall back to… a second hard-coded table, the thing being deleted. `frozenKey` runs in exported pages at module level before any call resolves. A live-reconnect window exists where an old server feeds a new frontend. And the data varies only at code-change time — serving it at runtime puts the seam where nothing varies (one adapter = hypothetical seam), paying availability and staleness error modes for zero leverage.

### Why Shape A

- **Depth**: callers learn three functions; everything else (the table, the by/seeds fold, `config.seed`, omit-when-default, the points clamp and zoom window) is implementation.
- **Locality**: adding or re-defaulting a setting = edit `m.Line`, run the generator, one commit; the `--check` test makes a forgotten regeneration a red build, not silent drift.
- **Seam placement**: at build time, where the variation actually happens; follows the existing `build-tokens` seam exactly.
- **Schema-forever**: nothing changes on any wire or in any file format. View YAML stays schema 1, `Line` untouched; old views, old prefs payloads and old exports (self-contained) all keep decoding. Bundle cost ≈ 0.2 KB.

## 3. Usage after the change

`compile.py` (wire shape unchanged, hand-written comparisons gone):
```python
return node("line", n.id, data=data, y=ys[0] if len(ys) == 1 else ys,
            scale=scale, note=note, **settings.wire_props(n), **common)
```

`prefs.py` — `settle` body is the struct round-trip; `apply_prefs` calls `settings.settle`, signature unchanged.

`line.ts`:
```ts
const prefs = effective(node, usePrefs(path));                       // chart-settings.ts
const call = visible ? seriesCall(node, prefs, { zoom, width }) : null;
```
(no `defaultsOf`, no `"config.seed"`, no param surgery in the block)

`prefs.ts` — keeps stores, `setChart`, `setView`, `changed`, and `cascade(defaults, prefs, id)`; the base literal at :101 is gone; `kit/figure.ts` passes its own defaults to `cascade` as today.

`api.ts frozenKey`:
```ts
if (method === "series") p = normalizeSeries(p);   // strips any param equal to DEFAULTS.line
```

## 4. What the seam hides

The names-and-defaults table itself; the by/seeds/band/steps ↔ series-params mapping and `config.seed`; the omit-when-default wire convention; the scale-is-always-resolved rule; the series-call construction (points clamp, zoom window vs. stored-curve zoom in exports); the axis-label-dropping rule when x or y change. Callers (blocks, `apply_prefs`, `frozenKey`) see only settings in web names.

## 5. Testing

- **Die**: nothing wholesale — the tables die inside implementations. `web/test/prefs.test.ts` survives with import updates (semantics identical); `web/test/snapshot.test.ts:7-12` survives (now asserts table-backed behaviour); `tests/views/test_views.py:112` survives unchanged.
- **New, replacing Playwright as the only cross-wire check**: one checked-in fixture `web/test/fixtures/chart-settings.json` — cases of `{settings, node, effective, series_params, frozen_key}`. `tests/views/test_settings.py` asserts `settle`+`compile` produce each `node` (plus settle idempotence, and that default settings leave props clean); `web/test/chart-settings.test.ts` asserts `effective`/`seriesCall`/`normalizeSeries` produce the rest from the same `node`. **Python writes the view side, TS reads it: the fixture is the wire contract, exercised on both sides in unit tests.**
- **Pin test**: pytest runs `scripts/build-chart-defaults --check`.
- Playwright `tests/serve/test_chart_settings.py` stays for panel geometry and UI behaviour only.

## 6. Migration (each step green)

1. **`views/settings.py`**: `line_defaults`, `SEEDS_FIELD`, `settle` moved and rewritten via struct round-trip; `prefs.py` delegates. pytest only. (~S, 150 lines)
2. **Generator**: `scripts/build-chart-defaults` + committed `web/src/bt/chart-defaults.ts` + `--check` pytest + npm script `defaults`. The file is unimported yet, so `npm run build` output is unchanged; still run `cd web && npm ci && npm test && npm run build` and commit static. (~S, 120 lines)
3. **`web/src/bt/chart-settings.ts`**: move `defaultsOf`/`effective`/`seriesCall`, add `normalizeSeries`; rewire `line.ts`, `prefs.ts` (base table out, `cascade` kept for the kit), `api.ts`, `kit/figure.ts`; update web tests. `npm ci && npm test && npm run build`, commit static, confirm shell under 120 KB compressed (delta is a move, ≈+0.1 KB). (~M, 250 lines moved)
4. **Cross-wire fixture** + `tests/views/test_settings.py` + `web/test/chart-settings.test.ts`. (~S/M, 150 lines)
5. **Tighten `compile.line` to `wire_props()`** and write the deviation back into `docs/design/05-views.md` (one paragraph in the Charts section: chart settings have one owner, the `line` struct; defaults reach the frontend as generated constants; wire omits defaults, `scale` always resolved). (~S, 60 lines)

## 7. Interaction with C6

**Land C3 first**: C6 (one normalized curve shape) rewrites the same blocks' data path and `line.ts` call sites, and is cleaner built on a stable `effective`/`seriesCall` seam than interleaved with it — the only ordering constraint is both editing `line.ts`'s call-building.

### Critical files
- src/beamtime/views/prefs.py
- src/beamtime/views/compile.py
- src/beamtime/views/model.py
- web/src/blocks/line.ts
- web/src/bt/prefs.ts
