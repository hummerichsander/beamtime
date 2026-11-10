# C1: answers own their places — deepening the remote answer seam

Recommendation: **Shape B** (a protocol per answer kind). Dependency category: in-process.

## 1. Verified diagnosis

All claims confirmed (`src/beamtime/remote/route.py` unless noted):

- `PATH_KEYS = ("group", "from", "scope", "folder")` at :24, `USER_CONTENT` (14 names) at :26-41, `PATH_COLUMNS` at :42. `prefix()` at :230-275 walks untyped answer dicts and guesses places from key names; all five call sites are inside route.py (:77, :162, :318, :339, :563), so the seam move is contained.
- **Bug 1 confirmed**: `wait` answers `changed: [{"run","name","from": <old status>,"to"}]` at `src/beamtime/ops/reading.py:611-620` (the `"from"` key at :615). `"from"` is in PATH_KEYS, so `prefix()` rewrites an old status `"running"` to `"@box/running"`.
- **Bug 2 confirmed**: `compare` answers `targets: [{"target": ..., "runs", "status", "code"}]` at `reading.py:282-290` (`"target"` at :284). Not in PATH_KEYS, so remote targets come back without `@box/`.
- `merge()` at :370-426, `merge_runs` at :429-452, `merge_keys` at :455-500. `merge_runs` hard-codes `["-run.created_at"]` (:446), copied from `query/kinds.py:58` — but kinds.py:58 **suppresses** that default when `seeds` or `by` is set; merge_runs doesn't, and aggregated rows have no `run.id` column, so the `run.created_at → run.id` rewrite (:448-450) sorts on a column that doesn't exist (`sort_rows`, `query/aggregate.py:75-92`, puts all-missing rows in arbitrary stable order). **Federated `runs --by` returns one unlabelled row per source per by-value, in effectively concatenation order.** Series merge adds `by.source` (:394-403); only `tests/remote/test_federation.py:48-52` covers it. `merge` reaches into `query.select.DEFAULTS` (route.py:380-384, defined `query/select.py:24-28`) and `ops.record.NOTES_PAGE` (route.py:411-413, defined `record.py:35`).
- Paging confirmed: each source runs the op with the laptop's `caller`, so each cuts at the 32k budget (`ops/budget.py:26-54`, applied in `reading.py:81-89` / `record.py:74`); `federate()` forwards `cursor` unchanged to every source (:337-338), the merged answer is never cut again (`routed` returns `federate(...)` at :65; `serve/api.py:51-54` returns `routed(...)` directly), and merged meta starts from `answers[0]`'s meta (merge :382 `first = dict(answers[0][1])`, :425, federate :366) — so `meta.next` is the local source's cursor applied to all sources.
- Test gaps confirmed: `tests/remote/test_route.py` (52 lines) unit-tests `prefix` on card/data/proposal/table shapes only; no remote test touches digest, compare, logs, wait, diagnose, plan missing, or `runs --by`; no federated-paging test.

**New findings:** (a) digest/plan-missing answer a top-level `"group"` that happens to be in PATH_KEYS, so they prefix correctly today *by accident* — the implicit coupling, not just the two bugs, is the problem. (b) Of the seven G4 ops, only `runs` is a listing; digest, compare, logs, wait, diagnose, plan missing route to one source (prefix only, no merge). (c) `prefix` is also applied to page-method answers (`view`, `summary`, `code`, …, `serve/api.py:25-26`) and bundle answers (`on_source`, route.py:563), which carry **no `kind`** — any design must keep a generic path for those.

Deletion test passes: deleting `prefix`/`merge`/`merge_keys` makes every op's answer shape reappear as scattered knowledge — the complexity belongs on the answer-producing side.

## 2. The deepened module, designed twice

New module: `src/beamtime/ops/answers.py` — in-process, pure (dicts in, dicts out; no Context, no I/O), keyed by the `"kind"` field every op answer already carries. It sits beside the ops, so each op and the module that knows its answer's places live in the same package.

Shared type: `Place = Callable[[str], str]` — turns a bare remote path into `@source/path` (`"."`/`""` → `@source`; a string with a source, or starting `/`, or containing `://`, unchanged; one without a source, `@local/...` included, is placed on the remote — the idempotence rule, so snapshot re-prefixing stays safe).

### Shape A — declarative metadata per kind (rejected)

```python
@dataclass(frozen=True)
class AnswerKind:
    kind: str
    places: tuple[str, ...] = ()      # dotted paths: "group", "targets[].target",
                                      #  "rows{path,run.group,run.path}" for table columns
    items: str | None = None          # the one item list: "rows" | "entries" | "curves"
    order: str | None = None          # merged item sort key, "-" for descending
    limit: str | None = None          # which default caps merged items
    label: str | None = None          # dict field that gets source labels ("by")
    counters: tuple[str, ...] = ()    # top-level numbers summed across sources
    merge_fn: Callable | None = None  # escape hatch
KINDS: dict[str, AnswerKind]          # one generic engine interprets the table
```

Honest assessment: `runs` (column union, sort rewrite, by/seeds labelling) and `keys` (per-column add/max/union/and, varying/aliases) don't fit the vocabulary; both immediately take `merge_fn`. The interface a maintainer must learn is then a path mini-DSL **plus** the engine's semantics **plus** the escape hatch — nearly as wide as the implementation. Shallow.

### Shape B — a protocol per kind, two methods (RECOMMENDED)

```python
class Answer:                                   # base; one subclass per answer kind
    kind: ClassVar[str]
    def placed(self, answer: dict, place: Place) -> dict:
        """Return a copy with every place in this kind's shape rewritten by `place`.
        Run ids, statuses, metric keys and user content are never places. Total: must
        handle every field the op can answer, across all schema versions ever emitted
        (answer readers accept every version forever — unknown fields pass through)."""
    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Combine per-source answers (already placed) into one answer of the same kind.
        `answers` arrive local-first, then sources in configured order — a stated
        invariant, so item order (and therefore cursors) is deterministic. Output is
        UNCUT (paging happens after), meta.matched summed, meta.source ".".
        Raises NoMerge for kinds that don't federate (only listings do)."""

ANSWERS: dict[str, Answer]                      # kind -> adapter; DEFAULT = today's generic walk

# module interface route.py calls (the whole surface):
def placed(answer: Any, source: str) -> Any     # dispatch on answer.get("kind"), DEFAULT otherwise
def merged(method: str, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict
def paged(answer: dict, cursor: str | None) -> dict   # thin wrapper over budget.offset_of + cut
```

Error modes: `merged` on an unregistered/unmergeable kind → `ValueError` (a programming error; the registry's `listing` flag guards which methods federate). `paged` re-raises budget's bad-cursor `OpError` (code 2). `placed` never raises on shape surprises — unknown fields are walked by the kind's own fallback (pass through unchanged), honoring the accept-every-schema-forever rule.

Internally, subclasses are one-to-three-liners over shared private helpers (`concat(key)`, `sorted_entries(key, limit)`, `label_rows(source)`, `place_table(columns, rows)`); the helpers are implementation, **not** interface — this is where Shape A's DSL goes to live without being learned by callers.

### Why Shape B

- **Depth**: route.py learns three functions; behind them sit prefixing rules for ~15 answer kinds, merge order, source labelling, limit defaults, and paging. Shape A's interface grows with every kind that doesn't fit its vocabulary; Shape B's doesn't.
- **Locality**: adding an op means writing its `Answer` subclass next to it — one class, one test file, and a conformance test that fails until it exists. In Shape A a bad path string fails at runtime, far from the op.
- **Seam placement**: the interface lives at `ops/answers.py`, on the answer-producing side; route.py keeps only transport, fan-out, snapshots and source states. Two real adapters per kind-slot from day one (the per-kind classes and DEFAULT), and the fakes for tests are plain dicts — the seam is real.
- `merged(..., caller)` deliberately replaces route.py reaching into `query.select.DEFAULTS` and `ops.record.NOTES_PAGE`: answers.py may import those (same side of the seam); route.py no longer knows they exist.

## 3. Usage

```python
# route.py, single-source path (routed, from_snapshot, elsewhere, on_source):
answer = client_for(ctx, source).request(method, stripped, caller=ctx.caller)
return answers.placed(answer, source)

# route.py, federate path:
def ask(name, client):
    scoped = {k: v for k, v in params.items() if k != "cursor"} | {"from": client.spec.scope}
    return answers.placed(client.request(method, scoped, ...), name), state
...
merged = answers.merged(method, collected, params, ctx.caller)   # collected: local first, uncut
merged["meta"] = {**merged.get("meta", {}), "sources": states}
return answers.paged(merged, params.get("cursor"))               # one cut, after merging
```

route.py no longer contains a single answer-shape key name.

## 4. What the implementation hides behind the seam

- **Prefixing rules**: which fields of each kind are places (compare's `targets[].target`, digest's `group`, table columns `path`/`run.group`/`run.path`), that run ids/statuses/metric keys/user content never are, idempotence on strings that carry a source, `/` or `://`, the `source: "local" → "@name"` rewrite, and the `wrote <path>` line rewrite. PATH_KEYS/USER_CONTENT guessing survives only inside DEFAULT, which ends up serving page/bundle methods (no `kind`) alone.
- **Merge order and semantics**: local-first-then-configured-order as a stated invariant; per-kind item ordering (timeline by `t`, notes by `id` desc, runs re-sorted by the query's sort with the `run.created_at → run.id` trick); runs with `by`/`seeds` get a `source` column and **no** phantom default sort (mirroring kinds.py:58) — fixing the unlabelled-rows bug; `keys`' column algebra; `matched` summing.
- **Paging**: cursor is *not* fanned out; each source answers from offset 0 at its own budget; one cut on the merged answer gives a correct `meta.next` over the deterministic merged order. A source that itself cut is surfaced as `meta.sources[i].cut: true` plus a hint ("narrow `from` or `where` to see all of @box") — honest about the N×budget boundary without inventing distributed cursors.
- **Source labelling**: series `by.source` and the new runs `source` column live in SeriesAnswer/RunsAnswer, the only places that know when labelling applies.

## 5. Testing

- **Survive unchanged**: all of `tests/remote/test_federation.py` (tests through `remote.answer()`, including `test_aggregates_are_labelled_by_source`, `test_listings_of_everything_merge`), `test_no_local.py`, `test_cp.py`, `test_pull.py`, `test_views.py`, `test_docker.py`; `test_route.py`'s `test_strip_and_source` and `test_only_targets_name_a_remote`.
- **Replaced**: `test_route.py`'s `test_prefix_leaves_what_users_wrote_alone` and `test_a_blocks_proposal_call_gets_the_source` move to `tests/remote/test_answers.py`, calling `answers.placed` with the same assertions. Nothing unit-tested `merge`/`merge_runs`/`merge_keys` directly, so nothing else dies.
- **New, at the interface (pure dicts, no remote process)**:
  - *Bug 1 regression*: `placed(wait_answer, "box")` leaves `changed[0]["from"] == "running"` untouched.
  - *Bug 2 regression*: `placed(compare_answer, "box")["targets"][0]["target"] == "@box/scaling"` (and the rest of the compare shape unprefixed).
  - Per kind: one `placed` test and (listings) one `merged` test on hand-built two-source answers — order, labelling, counters, `NoMerge` for non-listings.
  - *Federated `by`*: `merged("runs", ..., params with by)` labels rows per source and keeps per-source order; end-to-end `call("runs", {"from": ".", "by": ["config.lr"]}, ctx)` against the box fixture asserts a `source` column with both values.
  - *Federated paging*: `merged` + `paged` with a small `max_chars`; walking `meta.next` until exhaustion yields every item across both sources exactly once, in the stated order; a source answer marked `meta.cut` surfaces in `meta.sources`.
  - *Conformance* (in the spirit of `tests/test_design.py`): every `kind` an op in `OPS` answers has a registered `Answer` — forcing the new-op workflow.
  - End-to-end smoke for the G4 gap: digest/logs/wait/diagnose/plan-missing against `@box/...` asserting their places carry the prefix and nothing else does.

## 6. Migration path (each step green)

1. **Carve the seam** — create `ops/answers.py` with `Place`, `Answer`, `placed/merged/paged`, DEFAULT (the moved `prefix` walk verbatim) and per-kind classes whose bodies are the moved `merge`/`merge_runs`/`merge_keys` arms (mechanical, behaviour-preserving). route.py's five `prefix(...)` call sites become `answers.placed(...)`; `merge*` deleted from route.py. Move the two prefix tests. *Files: route.py (−~270), ops/answers.py (+~300), tests/remote/test_route.py → +test_answers.py. Size: M.*
2. **Fix the two bugs** — `WaitAnswer.placed` and `CompareAnswer.placed` (prefix `targets[].target`), registered so they bypass DEFAULT; the two regression tests. *Files: answers.py (+~25), test_answers.py. Size: S.*
3. **Federated `by`/`seeds`** — `RunsAnswer.merged`: source column when several sources and `by`/`seeds`; no default sort in that case; tests (unit + box fixture). *Files: answers.py (+~25), tests. Size: S.*
4. **Federated paging** — federate drops `cursor` from fan-out, calls `answers.paged` after merge, marks cut sources in `meta.sources`; tests with small `max_chars`. *Files: route.py (+~15), answers.py (+~15), tests. Size: S.*
5. **Every op kind explicit** — per-kind `placed` for the remaining kinds (card, data, series, keys, groups, timeline, notes, digest, logs, diagnose, plan missing, write answers with `path`/`lines`, …), each a few lines over helpers; conformance test; DEFAULT narrowed to page/bundle methods. Splittable into 2-3 tickets by op family. *Files: answers.py (+~120), tests. Size: M.*
6. **Spec write-back** — `docs/design/04-remotes.md` "Routing and merging": *answers own their places — per answer kind, a module beside the ops says which fields are places, how a listing merges, and in what order; routing only forwards, and the merged listing is paged once, locally.* Also the cursor-and-cut rule and the `meta.sources[].cut` mark. *Size: XS.*

## 7. Interactions

- **C2 (per-op descriptors)**: each `Answer` is keyed by the `kind` string the op already emits; a descriptor gains one field (`answer: "runs"` or a direct reference) and `ANSWERS` is then derived from `OPS` — the kind classes become part of the descriptor, never a second registry of record.
- **C6 (normalized curve shape)**: only `SeriesAnswer` changes — its source label moves to the normalized label field and the "several sources answered" check becomes shape-independent; route.py and every other kind untouched.
- **C7 (place value module)**: assumed **not** to exist yet (`places()` in `remote/__init__.py:13-25` is plain strings); `Place` stays a `Callable[[str], str]` route.py builds from the source name, so if C7 lands, route.py builds `Place` from its value type and `strip`/`source_of` move there — the `Answer` interface doesn't change.

### Critical files
- src/beamtime/remote/route.py
- src/beamtime/ops/answers.py (new)
- src/beamtime/ops/reading.py
- tests/remote/test_route.py (+ new tests/remote/test_answers.py)
- docs/design/04-remotes.md
