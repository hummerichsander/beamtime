# Candidate 7: a place is a value — one module for `@source/path`

(Design report from the C7 architect agent, 2026-11-10/12. Recommendation: Shape A.)

## 1. Verified diagnosis (re-counted against source)

**Parse sites.** `startswith("@"` / `startswith(f"@`: **24 occurrences in 11 Python files** (brief said ~28/11; 24 is the real count — `ops/copy.py:36` has two on one line):

| File | Lines |
|---|---|
| src/beamtime/ops/blocks.py | 99, 136, 163, 246, 280, 303, 304 (7, not 8) |
| src/beamtime/remote/route.py | 174, 178, 216 |
| src/beamtime/ops/views.py | 33, 205, 515 |
| src/beamtime/remote/__init__.py | 33, 37 |
| src/beamtime/serve/app.py | 77, 180 |
| src/beamtime/ops/copy.py | 36 (×2) |
| src/beamtime/serve/api.py | 265 |
| src/beamtime/query/select.py | 57 |
| src/beamtime/views/render.py | 35 |
| src/beamtime/remote/pull.py | 168 |
| src/beamtime/format/authored.py | 111 |

Plus **~11 adjacent @-aware sites**: slice/partition parses `route.py:175,179,218,551`, `app.py:181` (`s[len(name)+2:]`), `blocks.py:286,305`, `render.py:36`, `pull.py:169`; special-cases `route.py:192` (`@local`), `route.py:238` (`startswith(("@","/"))` in `prefix`). **~35 touchpoints total.** Web: 7 `startsWith("@")` in 4 files (`web/src/router.ts`, `shell/page.ts`, `shell/tree.ts`, `bt/md.ts`).

**Four resolvers, confirmed, one correction:**
- `query/select.py:50-100` `resolve_from`: base-relative normalization, `..`-escape refusal, **reserved-name refusal** (only here), moves via `format/moves.current`, `catch_up` budget 0, run-by-exact-id, unknown-group error = `closest()` over siblings **plus top-level-groups listing** (only here).
- `serve/api.py:275-308` `page_of`: same moves + closest-over-siblings, no top-groups listing, no reserved-name check, `..` as bare segment, budget 0, falls back to filesystem walk (`sdk.paths.find_run`).
- `ops/reading.py:844-863` `find_run`: budget **0.2 s** (only one), raw SQL `id LIKE ? OR name = ?` — the only resolver accepting unique id suffix or run name, own ambiguity error (code 2) and not-found text (code 4), no moves, no closest. Same walk fallback.
- `sdk/paths.py:127-133` `find_run`: exact-id walk returning `None`. Correction: not a competing resolver — the index-free fallback **adapter** the other two share.

**Diverging error behaviour to pin:** unknown group (siblings+top-groups vs siblings only); unknown run (three texts; suffix/name matching only in `reading.find_run`); reserved names (only `resolve_from` refuses); catch-up budget (0/0/0.2 s); unknown source (`query/select.py:57-61` vs `remote/sources.py:101-106` — only the latter lists known sources).

**`route.strip`/`strip_local`** (`route.py:183-227`): near-identical copies, differ only in prefix.

**Spec check:** docs/design/04-remotes.md holds; string stays the wire format, no deviation to write back; one clarifying line added (step 7).

## 2. Interface, designed twice

### Shape A — frozen value + one resolution function (RECOMMENDED)

`src/beamtime/format/place.py` (stdlib only; `format` imports only `beamtime.format`, so `tests/test_boundaries.py` holds by construction):

```python
@dataclass(frozen=True)
class Place:
    source: str | None   # None = this machine; "@local/…" parses to None
    path: str            # bare posix path, normalized, "." for the root

    @classmethod
    def parse(cls, text: str) -> "Place": ...
    @property
    def text(self) -> str: ...        # wire format back; "." / "@x" / "@x/a/b"
    @property
    def run_id(self) -> str | None: ...  # last segment if is_run_id, else None
    @property
    def reserved(self) -> bool: ...      # any segment is_reserved
    def on(self, source: str | None) -> "Place": ...  # same path, that source
```

`src/beamtime/query/resolve.py`:

```python
@dataclass(frozen=True)
class Resolved:
    path: str            # group relative to the log dir, after moves
    run_id: str | None

def resolve(index: Index, target: str | Place, *, base: str = ".",
            budget_s: float = 0.2, sources: Sequence[str] = ()) -> Resolved:
    """Raises QueryError (codes as today) for: unknown source (lists sources),
    unknown/ambiguous run, reserved or escaping path, unknown group (suggestions)."""
```

**Invariants:** `Place.parse(p.text) == p`; `Place.parse(s).text` is normalized form; `@local` normalizes to `source=None` at parse; `""`/trailing `/` → `"."`; parse is total — validity is `resolve`'s job.
**Error modes pinned to the richer variant:** unknown source → `client_for`'s text; unknown group → `resolve_from`'s text (closest siblings + top groups); moved group followed silently; run lookup → id/unique suffix/name with ambiguity error; one budget (0.2 s).
**Seam placement:** parsing in-process (`Place` is a value, no seam); resolution local-substitutable — `resolve` accepts `index: Index`; two real adapters exist (production log dir, synth temp log dir), no `IndexLike` protocol.

### Shape B — plain functions, no value (REJECTED)

`split/join/source_of/bare_of/is_run/run_name` string functions + same `resolve()`. Rejected: interface nearly as large as implementation (shallow); callers still thread `(source, bare)` pairs and re-join by hand; `@local` rule re-decided at call sites (today's bug surface — strip vs strip_local).

**Why A:** depth (one fact behind one name), locality (round-trip and `@local` invariants tested once on the value), seam placement (`Place` importable by SDK side; `resolve` stays out), lean (frozen dataclass + one function; deletion test: ~35 parse sites + three resolvers reappear).

**SDK decision:** `sdk/paths.find_run` stays separate and unchanged (SDK never sees `@source/...`; `resolve` needs `Index`, forbidden in sdk). CLI budgets hold: `format/place.py` stdlib-only; `query/resolve.py` adds no new import on the CLI path.

**TypeScript:** out of scope; a mirrored `web/src/bt/place.ts` is a separate optional ticket.

## 3. Usage sketches

- `route.py` `source_of`/`strip` via `Place.parse`; `strip_local` deleted (callers pass `None`).
- `serve/api.page_of`: 34 lines → ~6 (resolve + QueryError→OpError mapping).
- `query/select.resolve_from`: becomes a delegate to `resolve` (name kept, callers untouched).
- `ops/blocks.save_target`: comparison of two `Place.source`s instead of four slice expressions.
- `route.py:551 on_source`: `place = Place.parse(target); client = client_for(ctx, place.source); client.request(method, {"group": place.path, **body}, ...)`.

## 4. Hidden behind the seam

Behind `Place.parse`/`.text`: @-lexing, `@local` normalization, trailing-slash/empty normalization, run-id recognition. Behind `resolve`: posix normalization + escape refusal; reserved-name rule; moves; run lookup in full (index `run_path`, catch_up with one budget, SQL suffix/name match, ambiguity, walk fallback); suggestion building (difflib closest, siblings, top-level groups); exact error texts and codes.

## 5. Testing

**Survive:** `tests/remote/test_route.py` (strip tests gain a `source=None` case); `tests/ops/test_ops.py` page_of tests `:333-444` (suggestion assertion gains top-groups tail); `tests/sdk/test_paths_env.py`; boundaries/budgets hold by construction.
**Die:** only exact-string assertions on the three diverging messages (pinned texts in ~11 test files: tests/cli/test_commands.py, tests/mcp/test_server.py, tests/query/test_queries.py, tests/serve/test_app.py, …), updated in the step that pins each message.
**New:** `tests/format/test_place.py` — table-driven parse/format round-trip. `tests/query/test_resolve.py` on a synth temp log dir: run by id/suffix/name/ambiguous; moved group; unknown-group message; reserved refusal; escape refusal; unknown source lists known ones. These become the single home of the message strings.
**Behaviour changes (welcome, CHANGELOG'd):** run-suffix/name lookup works everywhere (CLI `from <suffix>`, web URLs by suffix); page_of gains reserved-name refusal; web pages gain top-groups tail in suggestions.

## 6. Migration path (each step green; ticket list)

1. `format/place.py` + `tests/format/test_place.py`. Value only, no call sites. ~120 lines + tests. (~0.5 d)
2. `query/resolve.py` + `tests/query/test_resolve.py`; `resolve_from` becomes delegate. Pins messages batch 1; update affected CLI/MCP test strings. (~0.5 d)
3. Convert `serve/api.page_of` and `ops/reading.find_run` to `resolve` (find_run keeps `Path`-returning signature as thin delegate for C4). Pins run-suffix behaviour and budget; CHANGELOG. (~0.5 d)
4. Convert `remote/route.py`: `source_of`, `strip`, delete `strip_local`, `on_source`, `prefix` guard via `Place`. (~0.5 d)
5. Convert ops/views/serve batch: `ops/blocks.py` (incl. save_target), `ops/views.py`, `ops/copy.py`, `remote/pull.split_target`, `serve/app.py` (run_file, subscribe_remotes), `views/render.page_url`, `format/authored.link_kind`, `serve/api.py:265`, `remote/__init__.targets`. Mechanical, per-file commits. (~1 d)
6. Fence: extend `tests/test_design.py` with a grep-style check that `startswith("@` and partition-style parses appear only in `format/place.py`; delete dead helpers. (~0.25 d)
7. Doc write-back: one line in docs/design/04-remotes.md under "Routing and merging": place parsing/resolution are one module; `@local` normalizes at parse. (~0.25 d)

## 7. Interactions

- **C1 (remote answer seam):** consumes `Place` for prefixing/stripping; `strip`/`strip_local` dies in step 4 here — land steps 1+4 before (or inside) C1 so its seam builds on the value.
- **C4:** `ops/reading.find_run` becomes a one-line delegate in step 3; C4 should target `query/resolve.py`, not the raw-SQL site.

### Critical files
- src/beamtime/format/place.py (new — the Place value)
- src/beamtime/query/resolve.py (new — resolve(); subsumes query/select.py:50-100)
- src/beamtime/remote/route.py (source_of/strip/strip_local/prefix/on_source)
- src/beamtime/serve/api.py (page_of)
- src/beamtime/ops/reading.py (find_run)
