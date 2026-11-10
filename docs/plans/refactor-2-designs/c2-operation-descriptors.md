# C2: one descriptor per method — deepening the registry

Recommendation: **Design A** (one flat extended `Op`), taking Design B's `params=None` marker. Dependency category: in-process.

## 1. Verified diagnosis (current line refs)

- `src/beamtime/ops/registry.py:668-696` — `Op` carries `name, params, summary, impl, positional, user_only, stdin, listing, writes, drafts, local` (`tool` at 686-689, `function()` at 691-696, `BY_NAME`/`BY_TOOL` at 1171-1172). Deep for parameters, shallow for behaviour: confirmed.
- `src/beamtime/remote/via_serve.py:11` (not 12) — `LISTINGS = ("groups","runs","series","data","timeline","notes","keys")`, a hand copy of what `route.py:18` derives (`{op.tool for op in OPS if op.listing}`). Used at `via_serve.py:27`.
- `src/beamtime/remote/route.py:18-21` — derived `LISTINGS/DRAFTS/WRITES/AUTHORED`; `:20` `WRITES = {...} | {"view_text","save_view"}` hand-patches two page methods. `:60` `if method in ("cp","compare")`; `:93` per-op param names `("source","dest") if method == "cp" else ("targets",)`; `:104-115` `with_default` hard-codes `"group"` (`:112`). **Precedent**: `:21` `AUTHORED` is already derived from `op.params.__struct_fields__` — facts can be derived, the registry just doesn't carry enough of them.
- `src/beamtime/serve/api.py:25-26` — `PAGES`/`ROUTED` tuples; `:41-46` hidden `everywhere` param popped before validation (sent by `web/src/shell/calls.ts:9`); `:47-50` `draft_local` for `("view","code","file")`; `:91-94` `"note_rm" | "set"` by name; `:61-123` `dispatch_here`, a 15-arm match.
- `src/beamtime/cli/__init__.py:116-147` — `add_field`'s match on parameter names (`where, steps, step, depth, verdict, evidence`); `query` special-cased at `:197-202` and `:231-232`; `params_of` repeats `where`/`verdict` at `:236-239`.
- `src/beamtime/cli/format.py:174-256` — `render()`, ~25-arm `match kind` with the `"\n".join(answer.get("lines", [])) or str(answer)` fallback at `:256`. Many op kinds (`block list`, `block show`, `view new`, `view validate`, `note rm`, `copied`, `pull`, …) rely on the `lines` branch, and a deliberate fallback is indistinguishable from a missing case.
- `web/src/api.ts:239-255` — `ALL_KINDS`/`KINDS_BY_METHOD`, consumed at `:265` with `?? ALL_KINDS` fallback (safe default: unlisted methods stale on everything). Server knowledge hand-kept in TypeScript.
- `src/beamtime/mcp/server.py:18-28` — `INSTRUCTIONS` lists user-only commands by hand. **New finding — it has already drifted**: it names `serve, init, mv, rm, gc, settings, doctor, reindex` but the registry has 18 `user_only` ops; `demo, mcp install, set, pull, note rm, block export, block import, source add/list/rm` are missing. Direct evidence the hand list is a shallow copy of a registry fact.
- Second, unregistered operation set confirmed: `hello, files, meta, view, summary, save_view, view_text, figure, code, run_diff` in `dispatch_here`, plus `view_check|put|compile|files, block_check|put` (routed separately by `route.py:535-563 on_source`, called from `ops/views.py:206,439,453,516`). `serve/stdio.py:61,78` is a third transport over the same `dispatch` — the seam is already in the right place; the registry behind it is too shallow.
- Co-change verified (`git diff-tree` over registry.py's last 300 touching commits): `ops/reading.py` 21×, `cli/format.py` 17×, `cli/__init__.py` 11×, `mcp/server.py` 9×, `serve/api.py` 8×, `remote/route.py` 5×.
- Test gaps: `tests/ops/test_ops.py:301-313` covers only `render(series)` and `render(runs)`; no test for `render_digest/logs/wait/diagnose/compare/plan_missing/resume`; no test that every op's kind renders. **No test pins `via_serve.LISTINGS`, `PAGES`, `ROUTED` or `KINDS_BY_METHOD`** — they can be deleted without replacing tests.
- **New finding**: `route.py:360-361` hand-builds `{"kind": "groups", "columns": ["path"], ...}` — another place that knows an answer kind's shape by hand (C1 territory).

## 2. The descriptor interface, designed twice

### Design A — one flat `Op`, extended to every method (RECOMMENDED)

Keep the name `Op`, keep the module string-only (import budget), add fields; page methods become entries whose CLI/MCP facet is simply absent:

```python
@dataclass(frozen=True, kw_only=True)
class Op:
    name: str                      # CLI path ("note add"); API name for API-only methods ("view_text")
    impl: str                      # "module:function"; API-only methods take (ctx, body) -> answer
    summary: str = ""
    params: type[Params] | None = None   # None: API-only, body passed unvalidated; never an MCP tool
    positional: tuple[str, ...] = ()
    stdin: str | None = None
    user_only: bool = False
    ui: bool = False               # a user-only op the web UI's own user calls (note rm, set)
    # routing (remote/route.py, serve/api.py, remote/__init__.py)
    listing: bool = False          # merges across sources
    writes: bool = False           # refused by snapshots
    drafts: bool = False           # runs here; op pushes/fetches itself
    local: bool = False            # runs here even with an @remote target
    routed: bool = True            # False: hello, files, meta, figure answer where they arrive
    one_source: tuple[str, ...] = ()    # target params that must name one source
    draft_params: tuple[str, ...] = ()  # params that make a call local
    # answer (cli/format.py, web/src/api.ts; the hook C1 keys on)
    kind: str | None = None        # the answer's "kind"; None: bytes or transport-only
    render: str | None = None      # "beamtime.cli.format:render_digest"; None: the lines fallback, declared
    stale_on: tuple[str, ...] = ("metrics", "status", "authored")
```

`METHODS: list[Op]` = today's `OPS` + ~16 page/bundle entries. Derived maps: `BY_NAME`, `BY_TOOL = {op.tool: op for op in METHODS if op.params is not None and not op.user_only}` (unchanged semantics — the MCP pin survives), `BY_API = {op.tool: op for op in METHODS if not op.user_only or op.ui}`.

**Invariants** (checked by one registry test, not at runtime): unique `name` and `tool`; `params is None` ⇒ dead CLI fields empty; `drafts` ⇒ `"group"` or `"draft"` in the params fields (makes `with_default`'s hard-coded `"group"` a *checked convention*); `writes` ⇒ `kind` named; `stale_on ⊆ {"metrics","status","authored"}`; two ops sharing a `kind` share a `render`; every `render`/`impl` string imports. **A parameter name means the same thing in every struct** (`where` is always `Where`, …) — the invariant that keeps `add_field`'s name-switch a single deep adapter rather than a smell.

**Error modes**: unknown method ⇒ `BY_API` miss ⇒ `OpError(..., code=4)` in `dispatch_here` (unchanged); a bad `render`/`impl` reference fails the interface test, never a user; an op left out of `stale_on` defaults to all three kinds — never silently fresh.

### Design B — a method-descriptor protocol with per-frontend sections (rejected)

```python
@dataclass(frozen=True) class Routing: listing: bool = False; writes: bool = False; ...
@dataclass(frozen=True) class Cli:     positional: tuple = (); stdin: str | None = None; user_only: bool = False
@dataclass(frozen=True) class Text:    kind: str | None = None; render: str | None = None
@dataclass(frozen=True) class Web:     stale_on: tuple = ("metrics", "status", "authored")
@dataclass(frozen=True, kw_only=True)
class Method:
    name: str; impl: str; summary: str = ""
    params: type[Params] | None = None
    cli: Cli | None = None; routing: Routing = Routing(); text: Text | None = None; web: Web | None = None
```

Rejected: both put the same behaviour behind the registry, but B adds four types and nested access (`op.routing.writes`) — more interface for identical leverage, i.e. shallower. B's sections are *internal* structure promoted to the interface; one adapter per section = four hypothetical seams, nothing varies across them. 54+16 entries × 4 constructor calls makes the most-read file noisier. Import budget is identical, so not a discriminator. **Kept from B**: `params=None` as the single marker for "no CLI/MCP facet", which keeps `BY_TOOL` and the MCP pin untouched.

Lean check: the fields added are exactly the facts found hand-copied in ≥2 places. Deliberately **not** added: per-parameter CLI parse hints (would push frontend facts into param structs — bad for C5), a per-op `everywhere` flag (transport-level), a `merge` field (C1's per-*kind* table, referenced via `kind`).

## 3. Usage

- `remote/via_serve.py` — delete `LISTINGS`; `:27` becomes `return bool(ctx.settings.get("remotes")) and BY_TOOL[tool].listing and everything`.
- `remote/route.py` — `:18-21` over `METHODS`, and `WRITES = {m.tool for m in METHODS if m.writes}` (view_text/save_view now declare it; the `| {...}` patch dies). `:60/:93` become `if op.one_source: check_one_source(op, params, ctx)`. `with_default` unchanged, its `"group"` assumption now pinned by the registry invariant test.
- `serve/api.py` — `PAGES`/`ROUTED` deleted; `ROUTED = {m.tool for m in METHODS if m.routed and not m.local}`. `dispatch_here` collapses to:
  ```python
  if (op := BY_API.get(method)) is None: raise OpError(f"no API method {method!r}", code=4)
  return call(op.name, body, ctx) if op.params is not None else op.function()(ctx, body)
  ```
  The match's body-unpacking arms become small `(ctx, body)` adapters in `serve/api.py` (`view_check` etc. already have that signature in `ops/views.py`). `draft_local` becomes `any(body.get(p) is not None for p in op.draft_params)`; `"note_rm" | "set"` becomes `op.ui`.
- `cli/__init__.py` — `build_parser`/`params_of` unchanged (params side was already deep). `query`'s special case stays: one op whose CLI argument form differs; a descriptor field for one consumer fails the two-adapter rule.
- `cli/format.py` — `render()` table-driven: `BY_KIND = {m.kind: m.render for m in METHODS if m.render}` (built lazily, renderer imported on use like `Op.function()`); unknown kind keeps the `lines` fallback, but `render=None` now *declares* it. Shared renderers: `runs/groups/file/settings/doctor/source list` name the table renderer; `data/timeline/notes` the entries renderer.
- `web/src/api.ts` — `meta()` (`serve/api.py:212`) gains `"stale": {m.tool: list(m.stale_on) for m in METHODS if m.routed}`; the shell already fetches `meta` at startup, so `api.ts` replaces the literal with a `let kindsByMethod = {}` filled from `meta`; `:265`'s `?? ALL_KINDS` fallback covers calls made before `meta` lands and old bundles. **Over-the-wire beats a generated TS file**: no build step, and the existing `meta.outdated`/`bundle` skew handling applies.
- `mcp/server.py` — `INSTRUCTIONS` interpolates `", ".join(sorted(op.name for op in METHODS if op.user_only))`, fixing the drift. `tools()`/`schema()` untouched.
- `remote/__init__.py:55-60` — `answer()` keeps reading `op.local`/`op.user_only`, now one of many descriptor consumers.

## 4. What the implementation hides behind the seam

Interface: `METHODS`, `BY_NAME`, `BY_TOOL`, `BY_API`, the `Op` fields, the invariants. Behind it: which methods exist at all (page methods included), where each runs (listing/writes/drafts/local/routed/one-source/draft-params), what each answers (`kind`), how it prints (`render`), when its answer goes stale (`stale_on`), which user-only commands exist, and how a method binds to its implementation. **No frontend names a method in code anymore** — today's grep for `"cp"`, `"view_text"`, `"note_rm"`, `view:` across five files comes back empty. Deletion test: deleting the registry today regrows hand lists in six places — we have the fossils (`via_serve.LISTINGS`, `WRITES | {...}`, `PAGES`, `KINDS_BY_METHOD`, `INSTRUCTIONS`, `dispatch_here`'s match), **two already drifted**. Stays outside deliberately: `add_field`'s per-parameter-name switch (one deep adapter, single-sourced, protected by the "same name, same type" invariant) and the `everywhere` transport param.

## 5. Testing

- **Survive untouched**: `tests/mcp/test_server.py::test_tools_match_the_registry` (BY_TOOL semantics identical — page methods have `params=None`), all of `tests/serve/` and `tests/remote/` (they cross `dispatch`/`routed`/`answer`, whose signatures don't change), `tests/test_budgets.py` (registry stays string-only; verify in step 1), `tests/ops/test_ops.py::test_text_rendering`.
- **Die**: none — no test pins the deleted literals (verified). The match arms of `dispatch_here` were never a test surface.
- **New interface tests** (`tests/ops/test_registry.py`):
  1. *Invariants*: unique names/tools; `drafts` ⇒ group/draft param; `stale_on` values legal; shared kind ⇒ shared render; every `impl`/`render` reference imports; every param name maps to one type across structs.
  2. *Every op renders*: against the synth fixture, call every non-user-only read op with minimal params (`wait` with `timeout=0`; `compare`/`digest`/`logs`/`diagnose`/`plan_missing`/`resume` included — closing the listed gap) and assert `render(answer)` is text and never the raw `str(dict)` branch; for ops with `render=None`, assert the answer carries `lines`.
  3. *Every method routes*: `WRITES`/`LISTINGS`/`DRAFTS` derived sets match declarations; every `routed` method resolves through `BY_API`; every `listing` op's `kind` has a merge arm in `route.merge` (the bridge to C1 — becomes "has an entry in the per-kind table" once C1 lands).
  4. *Staleness*: `meta()["stale"]` covers every routed method.

## 6. Migration path (each step green)

1. **Derive `via_serve.LISTINGS`; registry invariant test.** Delete the tuple, read `BY_TOOL[tool].listing`; add `tests/ops/test_registry.py` with the invariants that already hold. Scope: XS (~40 lines).
2. **`one_source` field; derive MCP user-only list.** `route.check_one_source` iterates the field; `INSTRUCTIONS` interpolates user-only names (fixes the drift — note in `docs/design/08-cli-mcp.md` that the instruction list is generated). Scope: S.
3. **Register the page methods.** Add `params=None` entries with `routed/writes/draft_params/ui` (new fields: `routed`, `ui`, `draft_params`); normalize the match arms into `(ctx, body)` functions; collapse `dispatch_here` to the two-line lookup; derive `ROUTED`, absorb `WRITES`' hand patch, replace `draft_local` and `"note_rm" | "set"`. Scope: M (~150 lines moved, the biggest step; `serve`/`remote` suites are the safety net).
4. **Answer kinds and render dispatch.** Add `kind`/`render` to every op; `format.render()` table-driven with the declared `lines` fallback; add the every-op-renders test (new coverage for the seven untested renderers). Scope: M.
5. **`stale_on` over the wire.** Field + `meta()["stale"]` + `api.ts` consumes with the existing `ALL_KINDS` fallback; delete `KINDS_BY_METHOD`. TS last. Scope: S.

## 7. Interactions

- **C1** (remote answer seam, first slice): its facts are per-answer-*kind*; `Op.kind` is the join key — one registry, one per-kind table keyed by `kind`, and test 3 pins that every listing kind has an entry, so no second registry grows.
- **C5** (params from query structs): untouched and helped — `params: type[Params] | None` is a descriptor *slot*, so deriving the structs changes only their construction; keeping CLI/MCP facts (`positional`, `stdin`, metavars) on the descriptor is exactly what lets query structs be shared without dragging frontend knowledge into the query layer.

### Critical files
- src/beamtime/ops/registry.py
- src/beamtime/serve/api.py
- src/beamtime/remote/route.py
- src/beamtime/cli/format.py
- web/src/api.ts
