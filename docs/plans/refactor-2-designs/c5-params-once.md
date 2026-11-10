# C5: query params declared once, not three times

Verdict: **Go — scoped to registry ⇄ `query/models.py`. No-go for folding `views/model.py` in.**
Recommendation: **Design A** (inheritance). Dependency category: in-process.

## 1. Verified diagnosis (current line refs)

Three parallel declarations, all confirmed:

- `src/beamtime/ops/registry.py` — `Selection` 42–50, `KeysParams` 52, `GroupsParams` 56, `RunsParams` 60–81, `SeriesParams` 90–114, `DataParams` 117–122, `FileParams` 125–130, `TimelineParams` 183–189, plus `Where`/`Fields` aliases 14–26 and the hand-written kind list in `QueryParams`'s description 203–209.
- `src/beamtime/query/models.py` — `Selection` 39–45, `Keys` 48, `Runs` 52–58, `Smooth` 61–64, `Series` 67–76, `Data` 79–84, `Timeline` 87–93, `Groups` 96, `File` 100–104, `KINDS` 114–123.
- `src/beamtime/views/model.py` — `Node.from_/where/depth` 31–37; `src/beamtime/views/compile.py` — `Compiler.selection` 383–393; `src/beamtime/views/code.py:11` — `KINDS`, a hand copy of the query kinds minus `importance`.

**Measured duplication** (fields declared in both registry and models): Selection `from_/where/depth` = 3; Runs `select/sort/limit/by` = 4 + `seeds` = 1; Series `y/x/steps/points/by/band` = 6 + `seeds` + `smooth` = 2; Data `key/step/limit` = 3; Timeline `types/since/limit/full` = 4; File `path/view` = 2. **25 field declarations exist twice.** The ops layer's genuine additions are only `cursor` (paging, `Page` 36–39), `to` on runs/series (export), `draft` on file, and the flat `smooth: float`.

**Real drift, current:**
1. `SeriesParams.smooth: float | None` vs `models.Series.smooth: Smooth{ema} | None`, translated at `reading.py:150`.
2. `models.Selection.seeds` is accepted by every query kind but read only in `runs` and `series` (`query/kinds.py:58–84, 231–234`); `{keys: {seeds: x}}` validates and is **silently ignored**. The registry scopes `seeds` correctly to `RunsParams`/`SeriesParams` — the two declarations already disagree about the interface.
3. `FileParams.view` is required; `models.File.view` defaults to `"."`.
4. `views/code.py:11` `KINDS` omits `importance` with nothing pinning the relationship to `models.KINDS`; `QueryParams`'s description hand-lists the kinds a third time.

**Cost evidence, verified:** commit `01418dc` (`runs --by`) touched `query/models.py` (+1), `ops/registry.py` (+4), `ops/reading.py` (+1) for one field — plus `query/kinds.py` where the only real logic lives.

**Deletion test on the adapters** (`reading.py`: `selection` 92–97, `keys` 100–106, `groups` 109–115, `runs` 118–133, `series` 136–154, `data` 157–164, `timeline` 190–202): deleting `keys/groups/data/timeline` makes no complexity reappear anywhere — pure dict shuffles. `runs`/`series` concentrate exactly two real behaviours: the `to` export branch and the smooth flattening. One adapter at a hypothetical seam: nothing else will ever translate params structs into query dicts, so the seam carries no variation and earns no keep.

## 2. Go/no-go

**Why go:** 25 fields declared twice, drift already observed twice (`seeds`, `smooth`), a measured 6-lines-across-3-files tax per new field, and four adapters that fail the deletion test outright. The fix **deletes code** (~60 lines net), is pinned by existing tests, and raises locality: afterwards, adding a query field = one declaration in `models.py` + logic in `kinds.py`; it flows into the CLI flag, the MCP tool schema and the query body with zero further edits.

**Why the views part is a no-go:** `views/model.py`'s `Node.from_` is page-relative (not logdir-relative), `depth` is deliberately narrowed to `Literal[1, "all"]`, and the descriptions are view-specific. `Compiler.selection` **passes** the deletion test — it resolves `scope_of`, merges `view.filters`, normalizes depth; deleting it scatters that into every block compiler. It is a real adapter over a genuinely different interface; sharing structs would couple two interfaces that are supposed to differ. The one cheap pin that buys the views benefit: a test asserting `code.KINDS == tuple(k for k in models.KINDS if k != "importance")`.

**Fallback if the go were refused:** a ~50-line test asserting, per pair (KeysParams/Keys … TimelineParams/Timeline), that every query-struct field appears in the params struct with the same encode name, type and default, with `{cursor, to, draft}` and the `smooth` override as the only allowed extras. That freezes drift but keeps the 3-file tax forever; the go buys strictly more at similar risk.

## 3. The interface, designed twice

**Hard constraints, checked in source:**
- **msgspec** (verified by execution): a subclass **can** override an inherited field with a different type, and the override keeps the parent's field position — so `SeriesParams(models.Series)` with `smooth: float | None = None` yields a clean flat JSON schema and a correct argparse flag. **Multiple inheritance of two field-bearing Structs fails** (`multiple bases have instance lay-out conflict`) — so `Page` cannot be mixed in; `cursor`/`to` are declared per struct via shared `Annotated` aliases.
- **Import budget** (measured): `import beamtime.query.models` triggers `beamtime/query/__init__.py`, which eagerly imports `Index` + `query.kinds` + `query.select` — ~40 ms incremental, ~29 beamtime modules. **`models.py` alone is 0.6 ms.** The registry is imported on every CLI call (`cli/__init__.py:173`) against a 150 ms wall budget (`tests/test_budgets.py:33`). So the design **requires making `query/__init__.py` lazy**: keep `from beamtime.query.models import QueryError` eager, move the heavy imports into `run()`'s body. Importers (`reading.py:27–28`, `record/proposals.py:13`) unchanged; `tests/test_boundaries.py` constrains only sdk/format/synth, so registry → query.models is a legal, downward, in-process dependency.

### Design A — inheritance (RECOMMENDED)

```python
Cursor = Annotated[str | None, Meta(description="a cursor from an earlier, cut answer")]
To = Annotated[str | None, Meta(description="write all of it to this .csv or .json file ...")]

class KeysParams(q.Keys, kw_only=True):      cursor: Cursor = None
class RunsParams(q.Runs, kw_only=True):      cursor: Cursor = None; to: To = None
class SeriesParams(q.Series, kw_only=True):  smooth: float | None = None  # flat EMA weight, the ops layer's form
                                             cursor: Cursor = None; to: To = None
# Selection(q.Selection) + cursor stays, for LogsParams/WaitParams/DiagnoseParams (not query kinds)
```

The field descriptions (`Where`, `Fields`, and the per-field `Meta`s at registry 45–114) move into `models.py`, which stays a 0.6 ms import.

**Invariant** (document it in the registry docstring): *a query op's params struct subclasses its query struct; everything it adds — `cursor`, `to`, `draft`, the flat `smooth` — belongs to the ops layer and is stripped before the query runs.* With that invariant, `msgspec.to_builtins(p)` minus the extras is a valid query body **by construction**; drift is a type error, not a test failure.

**Error modes unchanged**: `forbid_unknown_fields` is inherited; MCP conversion errors still name the params struct; `QueryError.explain` untouched. **MCP-schema consequences**: property order changes (`from, depth, where, …, cursor` — cursor moves from first to last), descriptions identical, size ~neutral against the 6000-token budget at `tests/mcp/test_server.py:97`. **CLI consequences**: same flags, same positionals (`op.positional` is name-keyed), only `--help` ordering shifts; the name-keyed special cases in `add_field` (`where`, `steps`, `depth` at `cli/__init__.py:116–147`) keep working.

### Design B — composition (rejected)

`class RunsParams(Page): query: q.Runs; to: To`. Rejected: the MCP tool schema becomes nested (`runs(query={...})`) — a breaking, worse interface for agents — and `build_parser`/`add_field` iterate flat fields, so the CLI would need a new flatten/unflatten adapter pair, i.e. the design re-creates the shuffling it set out to delete. A dynamic-`defstruct` variant (generate flat params from models + extras) keeps the flat interface but trades greppable declarations for metaprogramming — against the lean-code philosophy.

**One deliberate interface change rides along**: move `seeds` from `models.Selection` down to `models.Runs` and `models.Series` (matching both the registry and `kinds.py`'s actual behaviour). `{keys: {seeds: x}}` then errors instead of being silently ignored — a fix, not a regression; CLI/MCP never exposed it.

## 4. Usage: what the adapters collapse to

`reading.selection` (92–97) is deleted. One helper replaces the shuffling:

```python
def body(p) -> dict[str, Any]:
    out = msgspec.to_builtins(p)          # encode names: "from", not "from_"
    out.pop("cursor", None); out.pop("to", None)
    return out

def keys(ctx, p):     return ask(ctx, {"keys": body(p)})
def groups(ctx, p):   return ask(ctx, {"groups": body(p)}, p.cursor)
def data(ctx, p):     return ask(ctx, {"data": body(p)}, p.cursor)
def timeline(ctx, p): return ask(ctx, {"timeline": body(p)}, p.cursor)

def runs(ctx, p):
    q = body(p)
    if p.to is not None:
        return export(ctx, evaluate(ctx, {"runs": q | {"limit": p.limit or 10**6}}), p.to)
    return ask(ctx, {"runs": q}, p.cursor)

def series(ctx, p):
    q = body(p) | {"smooth": {"ema": p.smooth} if p.smooth is not None else None}
    ...
```

Deleted outright: `selection`, and the field-by-field dicts in `runs`/`series`/`data`/`timeline` (~45 lines). What remains in `runs`/`series` is exactly the behaviour that passed the deletion test: paging, export, smooth flattening. `file` stays as is — `draft` handling (173–187) is real behaviour, and `FileParams` keeps its own 3 fields (the required-`view` difference is a deliberate ops choice; inheriting 2 fields buys nothing). A deeper variant — passing the params struct straight to `KIND_FUNCTIONS[kind]` since it IS-A query struct — would need `query.run` to accept pre-parsed structs; not worth the query-layer change now; note it as a later option.

## 5. Testing

**Survive unchanged:** `tests/mcp/test_server.py::test_tools_match_the_registry` (names identical, size ~neutral — re-check the `size/4 < 6000` margin), `test_arguments_sent_as_json_text_are_decoded_once`, `tests/ops/test_tools.py` (23 tests; constructors are keyword-based and keep every name), `tests/ops/test_ops.py`, `tests/cli/*`, `tests/query/test_queries.py`.
**Dies deliberately:** `tests/test_docs.py` until `docs/reference/cli.md` is regenerated (field order shifts; it is generated from the registry).
**Must stay green with measurement:** `tests/test_budgets.py` CLI 150 ms — guaranteed by the lazy `query/__init__.py` (step 2), verify with `pytest -n0 tests/test_budgets.py`.

**Drift-pinning tests (new, small):** (a) `views/code.py` `KINDS == tuple(k for k in models.KINDS if k != "importance")`; (b) each query op's params struct is a subclass of its query struct and its extra fields are a subset of `{cursor, to, draft, smooth}` — after inheritance this is nearly enforced by construction, so the test is ~15 lines and mainly documents the invariant; (c) optional: `QueryParams`'s kind list derived from `models.KINDS` instead of prose.

## 6. Migration path (each step green)

1. **Scope `seeds`**: move it from `models.Selection` to `models.Runs` + `models.Series`; changelog note that `{keys: {seeds: …}}` now errors. `kinds.py` untouched. (~½ day)
2. **Lazy `query/__init__.py`**: heavy imports (`Index`, `KIND_FUNCTIONS`, `select`) move into `run()`; `QueryError` stays eager from `models`. Verify the budget tests serially. (~½ day)
3. **Move descriptions**: port the `Annotated`/`Meta` descriptions and the `Where`/`Fields` aliases from registry into `models.py`; registry re-imports them for its remaining uses. MCP schemas byte-compare before/after. (~½ day)
4. **Re-parent the six param structs** on their query structs (+`Cursor`/`To` aliases, the `smooth` override, `Selection(q.Selection)` for logs/wait/diagnose); add the pin tests from §5; regenerate `docs/reference/cli.md`. (~1 day)
5. **Collapse the reading adapters** to `body()` as in §4; delete `selection`. (~½ day)

Net ~3 dev-days, ~−60 lines in `src`, one new small test file. If only steps 1–2 land and the rest stalls, write the field-agreement pin from §2 as the fallback ticket.

## 7. Interactions

- **C2 (operation descriptors):** both edit `registry.py` on different axes — this re-parents param structs, that reshapes `Op`/dispatch; **land this after C2** so the `Op` list reshaping doesn't rebase over 15 struct edits (the shared `body()` can then hang off the descriptor).
- **C4 (reading.py tools):** this deletes the five shallow query adapters C4 would otherwise reorganize; sequence C4 first, or scope C4 away from `keys/groups/runs/series/data/timeline`.

### Critical files
- src/beamtime/query/models.py
- src/beamtime/ops/registry.py
- src/beamtime/ops/reading.py
- src/beamtime/query/__init__.py
- tests/mcp/test_server.py
