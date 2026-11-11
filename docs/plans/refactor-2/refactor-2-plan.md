# Refactor 2: deepen the hot modules

Base commit `7268916`, branch `main`. Proposed 2026-11-10, based on the architecture review and the seven design
documents in `docs/plans/refactor-2-designs/` (each verified against source at this commit), and the interview of
2026-11-10. Behaviour changes are allowed and ship as 0.3.0; they are listed in [Breaking changes](#breaking-changes).

Run a ticket with `/run-ticket docs/plans/refactor-2/refactor-2-plan.md <ID>` in a fresh session; review tickets
marked `+ review` with `/review-ticket docs/plans/refactor-2/refactor-2-plan.md <ID>` on a stronger model.
`ticket.py status docs/plans/refactor-2/refactor-2-plan.md` shows what's done and what's next.

## Goal

The outcome this plan commits to, checked against at the end and in every review:

- **Done means:** remote answers carry their places per answer kind, so `wait`, `compare`, federated `runs --by`
  and federated paging answer correctly over remotes; every method (CLI ops and page methods) is one `Op` and no
  frontend keeps a hand list of methods; `@source/path` is parsed by one value and resolved by one function; a
  line chart's settings have one owner (`m.Line`); every curve carries `y`/`lo`/`hi`/`n`; the agent tools take run
  facts from the index, with one failure-signature rule; query-op params subclass their query structs. All six bugs
  in Findings have regression tests. Nothing on disk changes format; every file and old remote still reads.
- **Confirmed by:** the full checks and `uv run pytest -q -n0 tests/test_budgets.py`; `cd web && npm ci && npm test
  && npm run build` with a clean `git status`; `ticket.py status` shows every ticket done; `rg -n 'startswith\("@'
  src/beamtime` hits only `src/beamtime/format/place.py`; `rg -n 'PATH_KEYS|merge_runs|merge_keys'
  src/beamtime/remote` and `rg -n 'KINDS_BY_METHOD|^LISTINGS = \(|^PAGES' src web/src` are empty.
  `scripts/release.py` runs at release time, after the version bump (decision 15).
- **Out of scope:** a TypeScript `place.ts` mirror; dropping the legacy curve arrays (next protocol major);
  federating the agent tools across sources; folding `views/model.py` into the query structs; settings owners for
  scatter/bar/histogram; a `facts` query kind; publishing, tagging or pushing the release.

## Findings

Evidence: **code** (read and verified against source by the design pass, not run; the ticket starts with a failing
test). Every row is code; the six bugs are listed in `docs/plans/refactor-2-designs/README.md`.

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | `beamtime wait @box/g` answers `"from": "@box/running"` | `"from"` in `remote/route.py` `PATH_KEYS` (l. 24); `wait`'s `changed[].from` is a status | code | R2 |
| 2 | `compare` over a remote drops the `@box/` prefix | `"target"` not in `PATH_KEYS`; `reading.py` 282–290 | code | R2 |
| 3 | federated `runs --by` returns unlabelled rows in arbitrary order | `merge_runs` (route.py 429–452) forces `-run.created_at`, which `query/kinds.py:58` suppresses for `by`/`seeds` | code | R3 |
| 4 | a federated listing answers up to N× the token budget; `meta.next` is the local cursor | each source cuts; the merged answer is never cut; cursor fanned out (route.py 337) | code | R4 |
| 5 | MCP `INSTRUCTIONS` lists 8 user-only commands, the registry has 18 | hand list in `mcp/server.py` 18–28 | code | O1 |
| 6 | `{keys: {seeds: x}}` validates and is ignored | `seeds` on `query/models.py` `Selection`, read only by runs/series | code | K1 |
| 7 | answer shapes guessed by key name | `route.prefix`/`merge` walk untyped dicts (route.py 230–500) | code | R1–R6 |
| 8 | six hand lists of methods, two drifted | `Op` too shallow; page methods unregistered (`serve/api.py` 25–123) | code | O1–O4 |
| 9 | ~35 `@`-parse sites, four resolvers with diverging errors | no place value (c7 §1) | code | P1–P5 |
| 10 | Line defaults in six places in two languages | no owner (c3 §1) | code | S1–S5 |
| 11 | three untagged curve shapes, four probing consumers, two contradicting | no canonical envelope (c6 §1) | code | V1–V4 |
| 12 | agent tools re-read run files the index holds; two failure rules; `ops` imports `cli` | `members()` shallow (reading.py 214–237) | code | Q1–Q5 |
| 13 | 25 query fields declared twice | params structs parallel to query structs (c5 §1) | code | K1–K4 |
| 14 | `ops/admin.py:639` imports `beamtime.mcp.skills` (found in planning) | `skills.py` is guide data living in `mcp/` | code | Q1 |

## Brief

What the tickets build together, so a session doesn't rediscover the design:

- **Places** (P): `format/place.py` `Place(source, path)`, frozen; `parse`, `text`, `run_id`, `reserved`, `on`;
  `@local` parses to `source=None`; parse is total, validity is `resolve`'s job. `query/resolve.py`
  `resolve(index, target, *, base=".", budget_s=0.2, sources=()) -> Resolved(path, run_id)` is the one resolver,
  with the richest of today's errors. `sdk/paths.find_run` stays (the SDK never sees `@`).
- **Answers** (R): `ops/answers.py`, pure dicts in and out. One `Answer` subclass per answer kind with
  `placed(answer, at)` and, for listings, `merged(answers, params, caller)`; `DEFAULT` keeps today's walk for
  methods without a `kind`. Module interface: `placed(answer, source)`, `merged(method, answers, params, caller)`,
  `paged(answer, cursor)`. `route.py` keeps transport, fan-out, snapshots, source states, and names no answer key.
  Answers merge local first, then sources in configured order; sources answer whole (R4b), and a merged listing
  is cut once, locally.
- **Descriptors** (O): one flat `Op` (fields as in c2 §2 Design A). `METHODS` lists every method, page methods
  with `params=None`; `OPS` stays, derived (`params is not None`), so CLI, MCP and `docs/site/reference.py` are
  untouched; `BY_NAME`, `BY_TOOL`, `BY_API`. `Op.kind` joins a method to its `answers.ANSWERS` entry.
- **Chart settings** (S): `views/settings.py` owns Line settings (`SEEDS_FIELD`, `line_defaults`, `settle`,
  `wire_props`, `generated_ts`); `scripts/build-chart-defaults` writes `web/src/bt/chart-defaults.ts`;
  `web/src/bt/chart-settings.ts` exports `effective`, `seriesCall`, `normalizeSeries`; `bt/prefs.ts` keeps
  `cascade`. The wire omits a setting at its default, except `scale`, which is always resolved.
- **Curves** (V): every series curve carries `x`, `y` and, unless raw, `lo`, `hi`, `n`; the old fields keep flowing
  (kit v1, older hubs). `upgrade_curve` in `SeriesAnswer.placed` lifts old remotes' curves. No consumer branches
  on `raw` or `by` to find values.
- **Run facts** (Q): `query/conditions.py` (moved from `cli/`); fields `run.attempts`, `run.last_logged` (column
  `metrics_mtime`, index schema 3); `query/facts.py` `RunFacts`, `run_facts`, `failure_key`;
  `reading.run_members` is the group tools' only path to runs. Only output text is still read from files.
- **Params** (K): query-op params subclass `query/models.py` structs; their only extras are `cursor`, `to`,
  `draft` and the flat `smooth`; `reading.body(p)` builds the query; `query/__init__.py` imports lazily.

Done, for every ticket: its Done line holds; its Check passes; `docs/design/` says what the code does; its heading
is marked done in the ticket's own commit.

## How to execute

1. Checks: the ticket's **Check** while working; before committing, `uv run ruff check . && uv run ruff format
   --check . && uv run pytest -q` (4 workers). Where a Check names it, `uv run pytest -q -n0
   tests/test_budgets.py` on an idle machine (never right after the full suite). Tickets touching
   `src/beamtime/format/` also run the SDK 3.10 command in `CLAUDE.md`.
2. Generated files: after any `web/` change, `cd web && npm ci && npm test && npm run build` and commit
   `src/beamtime/serve/static/` (shell under 120 KB compressed; never print a bundle file).
   `uv run python docs/site/reference.py` after changing an op's params or summary (`tests/test_docs.py`). From S2
   on, `uv run python scripts/build-chart-defaults` after changing `m.Line`.
3. Rules: `CLAUDE.md` style; no PyYAML, NumPy or `importlib.metadata` on the `beamtime runs` import path; `sdk/`,
   `format/`, `synth/` stay 3.10 + stdlib + PyYAML; never touch `tests/golden/schema1/`; readers accept every
   version ever written.
4. Spec: `docs/design/` is the spec; each ticket writes its deviation back in its own commit. The design documents
   in `docs/plans/refactor-2-designs/` are background (read the section a ticket names); where they differ from a
   ticket or a Decision, the ticket wins.
5. Ticket budget: 140k tokens per session; split a ticket that would exceed it, and say so in the report.
6. Recording: one commit per ticket, subject `<ID>: <what changed>`, appending ` — **done**` to the heading in the
   same commit. A visible change adds a line under `## 0.3.0 (unreleased)` in `CHANGELOG.md` (the first such
   ticket creates the heading). One session at a time in the main checkout; no worktrees.
7. Line ranges are at `7268916`; earlier tickets move code, so search the symbol when a range is off.

## Order

```
P1 ─ P2 ─ R1 ─ R2 ─ R3 ─ R4 ─ R5 ─ R4b ─ R6      place value + routing, then the answer seam
                                         └─ P3 ─ P4 ─ P5          one resolver, every call site
                                                      └─ O1 ─ O2 ─ O3 ─ O4      descriptors (O4: web)
                                                                         └─ S1 ─ S2 ─ S3 ─ S4 ─ S5   (S2, S3: web)
                                                                                               └─ V1 ─ V2 ─ V3 ─ V4 (V4: web)
                                                                                                               └─ Q1 … Q5 ─ K1 … K4 ─ X1
```

Why this order: R builds on `Place` and on P2's `route.py` (c1 §7); R4b comes after R5, whose flag for a source
that cut itself it narrows, and before R6, which states the paging rule in the spec; P5 edits `serve/api.py` before
O2 reshapes it; O3's conformance test needs every kind registered (R6); S3 and V4 both edit `line.ts`'s data path;
Q deletes `members()` and shrinks `reading.py` before K collapses its adapters, and K3 reshapes `registry.py` after
O.

Everything runs in this order, one session at a time in the main checkout, each `+ review` ticket followed by its
review: P1 P2 R1 R2 R3 R4 R5 R4b R6 P3 P4 P5 O1 O2 O3 O4 S1 S2 S3 S4 S5 V1 V2 V3 V4 Q1 Q2 Q3 Q4 Q5 K1 K2 K3 K4 X1.

## Decisions taken; say if you want otherwise

1. **All seven designs ship, in their recommended shapes** (your decision): C7 Shape A, C1 Shape B, C2 Design A,
   C3 Shape A, C6 Design A, C4 Shape B, C5 Design A scoped to the registry. Rejected: each design's alternative,
   for the reason in its §2.
2. **Bugs 1–2 are fixed in R2**, not as a hotfix ahead of the refactor (your decision).
3. **0.3.0, behaviour changes allowed** (your decision), each listed in Breaking changes and CHANGELOG'd by its
   ticket.
4. **Sequential, main checkout** (your decision); ticket budget 140k (your decision).
5. **Ticket letters P R O S V Q K X**: `ticket.py` finds a ticket's commit by subject across all history, and
   refactor 1 and the milestones already used A–H, M and Z.
6. **`answers.py` takes a source name, not a `Place`**: `placed(answer, source)` builds
   `at: Callable[[str], str]` from `format.place.Place` and hands `at` to each `Answer.placed(answer, at)`. In `at`,
   a string with a source stays as it is; a string without one, including `@local/...`, is placed on the remote
   (`Place.parse(v).on(source).text`; a string starting with `/` or containing `://` is left alone), so re-placing
   is idempotent.
   Rejected: c1's `Place` callable alias, because the name belongs to C7's value.
7. **`OPS` stays as a derived list** (`[m for m in METHODS if m.params is not None]`), so the CLI parser, MCP
   tools and `docs/site/reference.py` keep their input. Rejected: renaming every consumer to `METHODS`.
8. **C1's conformance test lands in O3**, once `Op.kind` exists. Rejected: a hand list of kinds in R6, a second
   registry for one week.
9. **`upgrade_curve` runs in `SeriesAnswer.placed`**: every remote series answer, single-source or federated,
   passes there; local and snapshot answers are computed by current code and already carry the envelope.
10. **The `@`-parse fence lives in `tests/test_boundaries.py`**, not `tests/test_design.py` (the design system's).
11. **`mcp/skills.py` moves to `guide/skills.py`** (proposed, finding 14): it is guide data, and the moved module
    lets Q1's boundary test ban `ops → mcp` without an exemption. Rejected: an allow-list entry.
12. **Spec write-backs land with the ticket that changes the behaviour**, not batched in X1.
13. **C1 paging**: the cursor is not fanned out; each source answers from offset 0; `paged` cuts the merged
    answer; a source that cut its own answer shows `meta.sources[i].cut: true` and the hint
    `narrow from or where to see all of @<name>`. Rejected: distributed cursors.
    **Amended after the R4 review** (your decision: fix it in this refactor, not accept it for 0.3.0): a source
    that cuts at its own 8k-token budget hides its later items from paging, the local listing included, so a
    federating serve asks every source, itself too, for its whole answer (R4b): the request line carries
    `whole: true`, and the answer is bounded only by the query's `limit` and a hard cap of about 2 MB
    (`budget.WHOLE_MAX_CHARS`). The merged answer is then complete up to the limit and one paging walk reaches
    every item once. `meta.sources[i].cut` remains for what is still incomplete: an old remote that ignores
    `whole` and cuts at its budget, or an answer over the cap. A cut at the `limit` is not a source's flag, since
    the merge applies the limit again across sources. Rejected: caching the merged answer on the serve between
    pages (state to invalidate as runs change, and cursors tied to one serve process) and a `whole` param on the
    ops (params forbid unknown fields, so old remotes would refuse the call).
14. **Errors pin to the richest variant** (C7): unknown source lists the known ones; unknown group suggests
    siblings and top-level groups; a run is found by id, unique id suffix or name; one catch-up budget, 0.2 s.
15. **The version bump waits for the release** (your decision): tickets write under `## 0.3.0 (unreleased)`;
    `pyproject.toml`, `uv.lock` and `scripts/release.py` belong to the release, not to X1.
16. **A run id suffix needs at least four characters** (P3 review; say if you want otherwise): with ids in
    base36, a one- to three-character suffix matches a run by chance, so a mistyped or not yet created group
    (`from: a`, `view save a`) named a random run and writes landed on it. `resolve` reads a shorter word as a
    group (`resolve.MIN_SUFFIX`); a run name still matches at any length. P4's `find_run` inherits it, so
    `card`, `output`, `mv` and `rm` stop accepting 1–3 character suffixes. Rejected: suffix lookup only for run
    arguments (the design wants it everywhere) and no minimum (the failure above).

## P. Places

### P1. The place value (sonnet) — code — **done**

- **Touches:** new `src/beamtime/format/place.py`, new `tests/format/test_place.py`.
- **Read:** `docs/design/04-remotes.md` § Naming remote groups (l. 139); `docs/plans/refactor-2-designs/c7-place-value.md` §2 Shape A.
- **Check:** `uv run pytest -q tests/format tests/test_boundaries.py`; the SDK 3.10 command in `CLAUDE.md`.
- **Done:** a table-driven test shows `Place.parse(p.text) == p` for every case; `"@local/a"` parses to
  `Place(None, "a")`; `""` and `"a/"` normalize to `"."` and `"a"`; `test_boundaries.py` stays green.
- **Risks:** `"@box"` and `"@box/"` → `Place("box", ".")`, text `"@box"` (`test_bare_source`); `"a/../.."` keeps
  its leading `..` for `resolve` to refuse (`test_parse_keeps_escape`); `"@local"` → `Place(None, ".")`
  (`test_local_is_here`).
- **Stop if:** `format.ids.is_run_id` or `format.tree.is_reserved` don't mean what `run_id`/`reserved` need.

A value only; no call site changes yet.

1. `@dataclass(frozen=True) class Place` with `source: str | None`, `path: str`. `parse(cls, text: str) -> Place`:
   a leading `@` splits at the first `/`, the name `"local"` becomes `None`; the path loses trailing `/`, goes
   through `posixpath.normpath`, and `""` becomes `"."`. Never raises.
2. `text` (property): `path` when `source is None`; `@source` when `path == "."`; else `@source/path`.
3. `run_id` (property): the last segment if `format.ids.is_run_id`, else `None`. `reserved` (property): any segment
   `format.tree.is_reserved`. `on(source: str | None) -> Place`: the same path on that source.
4. Docstrings per `CLAUDE.md`; stdlib and `beamtime.format` imports only.

### P2. Routing reads places (sonnet) — code — **done**

- **Touches:** `src/beamtime/remote/route.py` (`source_of` 168, `strip_local` 183 removed, `strip` 206,
  `prefix` 230–275 guard at 238, `on_source` 535–563), `src/beamtime/remote/__init__.py` (callers of
  `strip_local`), `tests/remote/test_route.py`.
- **Read:** `docs/design/04-remotes.md` § Routing and merging (l. 114); c7 §3.
- **Check:** `uv run pytest -q tests/remote`.
- **Done:** `strip_local` is gone; `source_of`, `strip`, `on_source` and `prefix`'s guard use `Place`;
  `tests/remote` green with `test_strip_and_source` gaining a `source=None` case.
- **Risks:** `@local/g` must strip to `g` exactly as `strip_local` did (`test_strip_and_source`); a target of
  `@box` alone becomes group `"."` in `on_source` (`test_views.py` remote view tests).
- **Stop if:** a caller depends on `strip_local` and `strip` differing beyond the prefix.

1. `source_of(params)`: `Place.parse(target).source` for the targets it inspects today.
2. `strip(params, source: str | None)`: rewrite each target to `Place.parse(v).path` when its source is `source`;
   `source=None` replaces `strip_local`; delete `strip_local` and point its callers at `strip(..., None)`.
3. `on_source`: `place = Place.parse(target)`, `client_for(ctx, place.source)`, body `{"group": place.path, ...}`.
4. `prefix`'s `startswith(("@", "/"))` guard (238) asks `Place.parse(v).source is not None` or `v.startswith("/")`.

## R. Answers own their places

### R1. Carve the answer seam (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/ops/answers.py`, `src/beamtime/remote/route.py` (`prefix` 230–275 and
  `merge`/`merge_runs`/`merge_keys` 370–500 moved out; call sites 77, 162, 318, 339, 563),
  `tests/remote/test_route.py`, new `tests/remote/test_answers.py`.
- **Read:** `docs/plans/refactor-2-designs/c1-answer-seam.md` §2 Shape B, §4; `docs/design/04-remotes.md` §
  Federation (l. 71), § Routing and merging (l. 114).
- **Check:** `uv run pytest -q tests/remote tests/serve/test_app.py tests/ops`; `uv run pytest -q -n0
  tests/test_budgets.py`.
- **Done:** `route.py` contains no `PATH_KEYS`, `USER_CONTENT`, `PATH_COLUMNS`, `merge*` or `prefix`; all of
  `tests/remote/test_federation.py` passes unchanged; the two prefix tests now call `answers.placed`.
- **Risks:** a behaviour change sneaking into the move (`test_federation.py` unchanged is the guard); importing
  `query.select.DEFAULTS` or `ops.record.NOTES_PAGE` at module level onto the CLI path (budget test); page and
  bundle answers without `kind` must still go through `DEFAULT` (`test_a_blocks_proposal_call_gets_the_source`).
- **Stop if:** keeping behaviour identical needs `answers.py` to know about `Context` or clients.

Behaviour-preserving: the code moves, nothing is fixed yet (R2–R4 fix).

1. `answers.py`: `class Answer` with `kind: ClassVar[str]`, `placed(self, answer: dict, at: Callable[[str], str])
   -> dict`, `merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict` raising
   `ValueError` for kinds that don't federate. `ANSWERS: dict[str, Answer]`; `DEFAULT` is today's `prefix` walk,
   moved verbatim with `PATH_KEYS`/`USER_CONTENT`/`PATH_COLUMNS` as its private constants.
2. One subclass per listing kind (`groups`, `runs`, `series`, `data`, `timeline`, `notes`, `keys`) whose `merged`
   is the moved arm of `merge`/`merge_runs`/`merge_keys`; their `placed` delegates to `DEFAULT` for now.
3. Module functions `placed(answer: Any, source: str) -> Any` (dispatch on `answer.get("kind")`, else `DEFAULT`;
   builds `at` per decision 6) and `merged(method: str, answers, params, caller) -> dict`.
4. `route.py`: the five `prefix(...)` calls become `answers.placed(...)`; `federate` calls `answers.merged`.
   Move `test_prefix_leaves_what_users_wrote_alone` and `test_a_blocks_proposal_call_gets_the_source` to
   `tests/remote/test_answers.py`, assertions unchanged.

### R2. `wait` and `compare` over a remote (sonnet) — code — **done**

- **Touches:** `src/beamtime/ops/answers.py` (new `WaitAnswer`, `CompareAnswer`), `tests/remote/test_answers.py`,
  `CHANGELOG.md`.
- **Read:** c1 §1 (bugs 1–2), §5; `src/beamtime/ops/reading.py` 282–290 (`compare` answer), 611–620 (`wait`).
- **Check:** `uv run pytest -q tests/remote`.
- **Done:** `placed(wait_answer, "box")["changed"][0]["from"] == "running"`; `placed(compare_answer,
  "box")["targets"][0]["target"] == "@box/scaling"` and the rest of the compare shape is unprefixed; both tests
  fail before the change.
- **Risks:** `wait`'s `changed[].run` is a run id, never a place (`test_wait_keeps_statuses`); a compare target
  already `@other/...` stays as it is (`test_compare_target_idempotent`).

1. `WaitAnswer.placed`: places only `group` (if present); `changed` passes through untouched.
2. `CompareAnswer.placed`: `targets[].target` through `at`; nothing else in the shape.
3. Write the regression tests first; register both kinds in `ANSWERS`; one CHANGELOG line (Fixed).

### R3. Federated `runs --by` and `--seeds` (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/ops/answers.py` (`RunsAnswer.merged`), `tests/remote/test_answers.py`,
  `tests/remote/test_federation.py`, `docs/design/04-remotes.md`, `CHANGELOG.md`.
- **Read:** c1 §1 (bug 3), §4; `src/beamtime/query/kinds.py` 55–84 (`runs_kind` defaults and aggregate columns);
  `docs/design/04-remotes.md` § Federation (l. 71).
- **Check:** `uv run pytest -q tests/remote tests/query/test_queries.py`.
- **Done:** `merged("runs", ..., {"by": ["config.lr"]})` over two sources gives a `source` column and keeps each
  source's own row order, local first; end to end, `call("runs", {"from": ".", "by": ["config.lr"]}, ctx)` against
  the `box` fixture answers both source names in that column; plain `runs` merges exactly as before.
- **Risks:** one source only → no `source` column (`test_single_source_no_label`); a user `sort` with `by` still
  applies, on aggregated columns (`test_by_with_sort`); `seeds` behaves like `by` (`test_seeds_federated`).

1. In `RunsAnswer.merged`, when `by` or `seeds` is set: no default sort (mirror `kinds.py:58`), insert a `source`
   column after `runs` holding `"."` for local and `@name` for each source, rows concatenated in answer order.
2. Without `by`/`seeds`: today's behaviour, unchanged.
3. One sentence in `04-remotes.md` § Federation: aggregated listings are labelled by source and keep each
   source's order. CHANGELOG (Fixed).

### R4. Federated listings are paged once (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/remote/route.py` (`federate` 324–368), `src/beamtime/ops/answers.py` (new `paged`),
  `tests/remote/test_federation.py`, `docs/design/04-remotes.md`, `CHANGELOG.md`.
- **Read:** c1 §1 (bug 4), §4 Paging; `src/beamtime/ops/budget.py` (`offset_of` 13, `cut` 26); decision 13.
- **Check:** `uv run pytest -q tests/remote tests/ops`.
- **Done:** with a small `max_chars`, following `meta.next` until it is absent yields every item from both sources
  exactly once, local first; a source whose own answer was cut appears as `meta.sources[i].cut: true` with the
  hint; `meta.matched` is the sum.
- **Risks:** a bad cursor raises `OpError` code 2 as today (`test_bad_cursor`); a source that is down still shows
  its state and does not shift the others' items (`test_down_source_paging`); a single local source (no remotes)
  pages exactly as before (`tests/ops` unchanged).
- **Stop if:** sources cutting at their own budget makes the walk lose items silently in a way the `cut` flag
  can't show.

1. `federate`: drop `cursor` from the params sent to every source; collect answers uncut, call
   `answers.merged`, set `meta.sources`, then `answers.paged(merged, params.get("cursor"))`.
2. `paged(answer: dict, cursor: str | None) -> dict`: `budget.cut(answer, budget.offset_of(cursor))`.
3. Mark `cut: true` and the hint on a source whose answer carried `meta.next`.
4. `04-remotes.md` § Routing and merging: the cursor-and-cut rule and `meta.sources[].cut`. CHANGELOG (Fixed).

### R5. Every reading kind places its own fields (sonnet) — code — **done**

- **Touches:** `src/beamtime/ops/answers.py`, `tests/remote/test_answers.py`.
- **Read:** c1 §4 (prefixing rules); the answer builders in `src/beamtime/ops/reading.py` and
  `src/beamtime/ops/record.py` for each kind below.
- **Check:** `uv run pytest -q tests/remote`.
- **Done:** `card`, `output`, `resume`, `status`, `data`, `series`, `keys`, `groups`, `timeline`, `notes`, `note`,
  `memory`, `proposal`, `check`, `file`, `digest`, `logs`, `diagnose`, `plan missing` each have an `Answer` whose
  `placed` names its places explicitly, with a table-driven test of a hand-built answer per kind: places prefixed,
  run ids, statuses, metric keys and user content untouched.
- **Risks:** digest and plan-missing's top-level `group` (prefixed today only by accident, c1 §1 a) stays
  prefixed (`test_digest_group`); table columns `path`/`run.group`/`run.path` in `runs`/`groups`
  (`test_table_columns`); notes' text and proposal bodies never rewritten (`test_user_content`).
- **Stop if:** a kind's answer has a field that is a place in some answers and not in others.

1. A private helper per recurring shape (`place_table(columns, rows, at)`, `place_keys(d, keys, at)`), then each
   class a one-to-three-liner. Unknown fields pass through unchanged.
2. Each class registered in `ANSWERS`; `DEFAULT` untouched.

### R4b. Federated paging reaches every item (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/ops/budget.py` (new `WHOLE_MAX_CHARS`, new `page`), `src/beamtime/ops/context.py`
  (`Context` 29, new field `whole`), `src/beamtime/ops/reading.py` (`page` 81–89),
  `src/beamtime/ops/record.py` (`notes` 48–74), `src/beamtime/serve/stdio.py` (`answer` 57–88, `caller` 71),
  `src/beamtime/remote/client.py` (`request` 133, `send` 152, request line 167), `src/beamtime/remote/route.py`
  (`Local` 27, `routed` 30–66, `federate` 229–283, `drop_own_cut` 294–304), `src/beamtime/serve/api.py`
  (`dispatch` 54), `src/beamtime/remote/__init__.py` (`answer` 67), `tests/remote/test_federation.py`,
  `tests/serve/test_stdio.py`, `tests/ops/test_tools.py` (55), `docs/design/04-remotes.md`, `CHANGELOG.md`.
  Lines at `d492da9`; R5 edits only `answers.py`.
- **Read:** decision 13 and its amendment; ticket R4; `docs/design/04-remotes.md` § Routing and merging (l. 116,
  the paging bullet l. 136–140), § Protocol (l. 211).
- **Check:** `uv run pytest -q tests/remote tests/ops tests/serve/test_stdio.py`; `uv run pytest -q -n0
  tests/test_budgets.py`.
- **Done:** new `test_paging_reaches_beyond_a_source_budget`: local and two sources (`s0`, `s1`), 30 rows each,
  every one of the three answers larger than the budget (`small_pages`); following `meta.next` until it is absent
  yields every row exactly once, local first, and no `meta.sources[i]` has `cut`; it fails before the change.
  New `test_federated_runs_page_through_local` against the `box` fixture with `small_pages`: `runs` over `.` with
  `limit: 1000` followed by cursor gives every run id of local and `@box` exactly once (reference: each source's
  own listing with `caller="view"`). New `test_whole_request_is_not_cut` (stdio): a listing that a plain request
  cuts carries no `meta.next` when the request line has `"whole": true`; without it, the answer is as before.
  New `test_whole_answer_is_capped`: with `budget.WHOLE_MAX_CHARS` lowered, a whole answer carries `meta.next`
  and `federate` flags that source `cut: true` with the hint. New `test_view_federation_is_whole`: with
  `caller="view"`, `federate` returns every row of every source and no `meta.next`, with `small_pages` and
  `WHOLE_MAX_CHARS` lowered. `test_a_source_that_cut_itself_says_so` passes with its `FakeClient(cut=True)`
  standing for an old remote that ignores `whole`.
  `test_federated_pages_give_every_item_once`, `test_down_source_paging` and `test_bad_cursor` pass, adapted only
  to `local(params, ctx)` and the client's `whole` keyword, and assert every source was asked `whole=True`;
  `test_limit_cut_is_flagged` passes unchanged; `tests/ops` passes with only the `routed` lambda adapted.
- **Risks:** remote payload and ssh time: every page asks every source again for its whole answer, up to the
  `limit` and about 2 MB each, within `LISTING_S` (20 s) (`test_whole_answer_is_capped`); an old remote ignores
  the request line's `whole`, still answers, and is flagged cut, never refused
  (`test_a_source_that_cut_itself_says_so`, and `test_whole_request_is_not_cut` for a line without it); the
  `view` caller isn't paged and keeps whole, uncapped answers with no `meta.next`
  (`test_view_federation_is_whole`); a single source with no remotes pages exactly as before (`tests/ops`).
- **Stop if:** an answer kind has no `limit` and no natural bound, so whole answers routinely reach the cap; or
  passing `whole` needs a field in the ops' params (they forbid unknown fields, so old remotes would refuse).

Under R4 each source cuts its answer at its own 8k-token budget before the merge, so items beyond that cut,
the local listing of `.` included, can't be reached by paging once any remote is configured (decision 13).

1. `budget.py`: `WHOLE_MAX_CHARS = 64 * MAX_CHARS` (about 2 MB, one comment line: what a federating serve takes
   from one source); `page(answer: dict, cursor: str | None, *, caller: str, whole: bool) -> dict`: `view` →
   the answer as it is; `whole` → `cut(answer, offset_of(cursor), max_chars=WHOLE_MAX_CHARS)`, reading the
   module constant at call time so a test can lower it; else `cut(answer, offset_of(cursor))`.
   `reading.page` and the last line of `record.notes` call it with `ctx.caller`, `ctx.whole`.
2. `Context.whole: bool = False`, after `merge`, one comment line: a federating serve asks for answers bounded
   only by their limit and `WHOLE_MAX_CHARS`.
3. Request line: `client.request`/`send` take `whole: bool = False` and add `"whole": true` to the line only when
   set (other requests are byte-identical); `Stdio.answer` sets `whole=request.get("whole") is True` on its
   `dataclasses.replace`. An old remote reads only `id`, `method`, `params`, `caller` and ignores it.
4. `route.py`: `Local = Callable[[dict[str, Any], Context], Any]`; `routed` calls `local(params, ctx)`; the
   lambdas in `src/beamtime/serve/api.py` and `src/beamtime/remote/__init__.py` take `(given, c)` and use `c`.
   `federate` makes `whole = dataclasses.replace(ctx, whole=True)` and uses it for `local`, `from_snapshot` and
   `client.request(..., whole=True)`; the `view` early return stays.
5. `drop_own_cut` keeps keying on `meta.next`, which now means only an old remote or an answer over the cap; its
   docstring says so. A source cut at its `limit` (`meta.cut` without `next`) is not flagged: the merge applies
   the limit again. R5's top-level cut flag, if present, keys on the same per-source flag.
6. Tests as in Done; `FakeClient` takes `whole` and cuts itself at the budget unless asked whole, like a current
   remote, unless `cut=True` (an old remote). The `serve --stdio` subprocess cuts at the real 32k characters, so
   `test_whole_request_is_not_cut` picks a listing over that (`runs`, `limit: 1000`, wide `select`) or answers
   in-process with `small_pages`, whichever is shorter.
7. `04-remotes.md`: the paging bullet says sources answer whole (bounded by `limit` and about 2 MB) and only an
   old remote or an answer over the cap shows `meta.sources[i].cut`, drop "items beyond its cut are not
   reachable"; § Protocol: a request may carry `whole: true`, which older remotes ignore. Amend R4's CHANGELOG
   line to match; no new line.

### R6. Write, view and block answers; the spec (sonnet) — code — **done**

- **Touches:** `src/beamtime/ops/answers.py`, `tests/remote/test_answers.py`, `docs/design/04-remotes.md`.
- **Read:** c1 §4, §6 step 6; the builders of the remaining kinds (`view *`, `block *`, `copied`, `pull`,
  `export`, `settings`, `doctor`, `source list`, `note rm`) in `src/beamtime/ops/`.
- **Check:** `uv run pytest -q tests/remote tests/serve`.
- **Done:** every `kind` emitted by `src/beamtime/ops/`, `src/beamtime/query/` and `src/beamtime/record/`
  (`rg -o '"kind": "[a-z ]+"'`) has an entry in `ANSWERS`; `DEFAULT` serves only answers without `kind`; write
  answers' `path` and `lines` (`wrote <path>`) are placed; `04-remotes.md` says answers own their places.
- **Risks:** `kind` values that are not answer kinds (`auto`, `manual`, `local`, `remote`, `event`,
  `checkpoint` name note or source types) must not be registered (`test_answer_kinds_only`); the `wrote <path>`
  line rewrite (`test_wrote_line`).

1. Classes for the remaining kinds, as in R5.
2. `docs/design/04-remotes.md` § Routing and merging: *answers own their places — per answer kind, a module beside
   the ops says which fields are places, how a listing merges, and in what order; routing only forwards, and the
   merged listing is paged once, locally.*

## P. Places (continued)

### P3. One resolver (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/query/resolve.py`, `src/beamtime/query/select.py` (`resolve_from` 50–100 becomes a
  delegate), new `tests/query/test_resolve.py`, tests pinning the messages in `tests/cli/test_commands.py`,
  `tests/mcp/test_server.py`, `tests/query/test_queries.py`, `tests/serve/test_app.py`, `CHANGELOG.md`.
- **Read:** c7 §1 (four resolvers, diverging errors), §2 `resolve`; decision 14; `docs/design/03-index.md` §
  Selecting runs (l. 251).
- **Check:** `uv run pytest -q tests/query tests/cli tests/mcp tests/serve/test_app.py`.
- **Done:** `tests/query/test_resolve.py` on a synth log dir: run by id, unique suffix, name, ambiguous (code 2);
  moved group followed; unknown group lists siblings and top-level groups; reserved and escaping paths refused;
  unknown source lists the known ones. `resolve_from`'s callers are unchanged.
- **Risks:** an id suffix that is also a group name (`test_group_wins_over_suffix` — decide: exact group first);
  `catch_up` with budget 0.2 s on a large tree (budget test); a test elsewhere pinning an old message text
  (`rg` the old strings, update in this commit).
- **Stop if:** unifying the unknown-source message needs `query/` to import `remote/`; pass `sources` in instead.

1. `@dataclass(frozen=True) class Resolved: path: str; run_id: str | None`.
2. `resolve(index: Index, target: str | Place, *, base: str = ".", budget_s: float = 0.2, sources:
   Sequence[str] = ()) -> Resolved`, behaviour per c7 §4 and decision 14; `QueryError` codes as today.
3. `resolve_from(index, base, target)` returns `(r.path, r.run_id)` from `resolve`.
4. These tests become the single home of the message strings. CHANGELOG (Changed: suffix/name lookup everywhere).

### P4. Pages and run lookup resolve once (sonnet) — code — **done**

- **Touches:** `src/beamtime/serve/api.py` (`page_of` 275–308), `src/beamtime/ops/reading.py` (`find_run`
  844–863 becomes a delegate), `tests/ops/test_ops.py` (page_of tests 333–444), `CHANGELOG.md`.
- **Read:** c7 §3; `src/beamtime/query/resolve.py`.
- **Check:** `uv run pytest -q tests/ops tests/serve tests/cli`.
- **Done:** `page_of` is about six lines over `resolve` mapping `QueryError` to `OpError`; `find_run` keeps its
  `Path`-returning signature over `resolve`; a run page opens by unique id suffix; a reserved name is refused.
- **Risks:** the web's unknown-group message gains the top-groups tail (update the assertion, don't layer);
  `find_run`'s walk fallback when the index misses (`test_find_run_without_index`).

1. `page_of(ctx, path)`: `resolve(index, path, sources=...)`; `QueryError` → `OpError` with the same code.
2. `find_run(ctx, run_id) -> Path`: `ctx.logdir / resolve(index, run_id).path` (`Resolved.path` of a run is
   the run's own directory).
3. CHANGELOG (Changed: pages refuse reserved names; run arguments need a suffix of four characters or more,
   decision 16; update `docs/design/08-cli-mcp.md` l. 252 to say so).

### P5. Every call site parses through `Place` (sonnet) — code — **done**

- **Touches:** `src/beamtime/ops/blocks.py` (99, 136, 163, 246, 280–305 incl. `save_target`),
  `src/beamtime/ops/views.py` (33, 205, 515), `src/beamtime/ops/copy.py` (36), `src/beamtime/remote/pull.py`
  (`split_target` 168), `src/beamtime/serve/app.py` (77, 180), `src/beamtime/serve/api.py` (265),
  `src/beamtime/views/render.py` (`page_url` 35), `src/beamtime/format/authored.py` (`link_kind` 111),
  `src/beamtime/remote/__init__.py` (`targets` 33–37), `src/beamtime/query/select.py` (57),
  `tests/test_boundaries.py`, `docs/design/04-remotes.md`.
- **Read:** c7 §1 table (every site), §6 steps 5–7.
- **Check:** `uv run pytest -q tests/ops tests/remote tests/serve tests/views tests/format tests/test_boundaries.py`;
  the SDK 3.10 command in `CLAUDE.md`.
- **Done:** `rg -n 'startswith\("@|startswith\(f"@' src/beamtime` hits only `format/place.py`, and a new test in
  `tests/test_boundaries.py` asserts it; dead helpers deleted; one line in `04-remotes.md`.
- **Risks:** slice parses `s[len(name)+2:]` (`app.py:181`) off by one (`tests/serve/test_app.py` remote file
  tests); `src/beamtime/format/authored.py` must import only `beamtime.format` (`test_boundaries.py`).

Mechanical; behaviour unchanged.

1. Replace each parse and slice with `Place.parse(...)`, `.source`, `.path`, `.text`. `save_target` compares two
   `Place.source`s.
2. The fence test: scan `src/beamtime/**/*.py` except `format/place.py` for `startswith("@` / `startswith(f"@`.
3. `04-remotes.md` § Routing and merging: place parsing and resolution are one module each; `@local` normalizes
   at parse.

## O. One descriptor per method

### O1. Derived listings, one-source params, the MCP user-only list (sonnet) — code — **done**

- **Touches:** `src/beamtime/ops/registry.py` (`Op` 668–696: new field `one_source`), `src/beamtime/remote/via_serve.py`
  (`LISTINGS` 11 removed, 27), `src/beamtime/remote/route.py` (`check_one_source` 86–102, `routed` 60),
  `src/beamtime/mcp/server.py` (`INSTRUCTIONS` 18–28), new `tests/ops/test_registry.py`,
  `docs/design/08-cli-mcp.md`, `CHANGELOG.md`.
- **Read:** `docs/plans/refactor-2-designs/c2-operation-descriptors.md` §1, §2 (invariants), §6 steps 1–2;
  `docs/design/08-cli-mcp.md` § MCP (l. 154).
- **Check:** `uv run pytest -q tests/ops tests/remote tests/mcp`; `uv run pytest -q -n0 tests/test_budgets.py`.
- **Done:** `via_serve.LISTINGS` gone; `INSTRUCTIONS` names all 18 user-only ops, generated from the registry (a
  test compares); `route.py` names neither `"cp"` nor `"compare"`; `tests/ops/test_registry.py` checks unique
  names and tools and that every `impl` imports.
- **Risks:** `INSTRUCTIONS` grows past the MCP token budget (`tests/mcp/test_server.py` size test); `cp`'s
  `source`/`dest` and compare's `targets` (`tests/remote/test_cp.py`, `test_only_targets_name_a_remote`).

1. `Op.one_source: tuple[str, ...] = ()`; set `("source", "dest")` on `cp`, `("targets",)` on `compare`.
   `check_one_source(op, params, ctx)` iterates it; `routed`'s `if method in (...)` becomes `if op.one_source`.
2. `via_serve`: `BY_TOOL[tool].listing`.
3. `INSTRUCTIONS` interpolates `", ".join(sorted(op.name for op in OPS if op.user_only))`. Note in
   `08-cli-mcp.md` that the list is generated. CHANGELOG (Fixed).

### O2. Page methods are registered (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/ops/registry.py` (`Op` fields `routed`, `ui`, `draft_params`; `METHODS`, `OPS`
  derived, `BY_API`; `BY_NAME`/`BY_TOOL` 1171–1172), `src/beamtime/serve/api.py` (`PAGES`/`ROUTED` 25–26,
  `draft_local` 47–50, `note_rm`/`set` 91–94, `dispatch_here` 61–123), `src/beamtime/remote/route.py` (`WRITES`
  20), `src/beamtime/ops/views.py` (`(ctx, body)` adapters), `tests/ops/test_registry.py`.
- **Read:** c2 §2 Design A, §3 (the `src/beamtime/serve/api.py` part); decision 7.
- **Check:** `uv run pytest -q tests/serve tests/remote tests/ops tests/mcp tests/test_docs.py`;
  `uv run pytest -q -n0 tests/test_budgets.py`.
- **Done:** `dispatch_here` is the two-line lookup; `PAGES`, `ROUTED`'s literal, `WRITES`' `| {...}` patch and
  `"note_rm" | "set"` are gone; `METHODS` holds the 16 page methods with `params=None`;
  `test_tools_match_the_registry` and `tests/test_docs.py` pass unchanged.
- **Risks:** the hidden `everywhere` param still popped before validation (`tests/serve/test_app.py`); drafts
  for `view`/`code`/`file` still run locally (`tests/remote/test_views.py`); registry imports stay string-only
  (budget test).
- **Stop if:** a page method's body needs validation that `params=None` loses.

Page methods: `hello`, `files`, `meta`, `view`, `summary`, `save_view`, `view_text`, `figure`, `code`,
`run_diff`, `view_check`, `view_put`, `view_compile`, `view_files`, `block_check`, `block_put`.

1. `Op` gains `routed: bool = True`, `ui: bool = False`, `draft_params: tuple[str, ...] = ()`; `params` may be
   `None`. `METHODS` = today's list + the page entries; `OPS = [m for m in METHODS if m.params is not None]`;
   `BY_API = {m.tool: m for m in METHODS if not m.user_only or m.ui}`.
2. Normalize each match arm into a `(ctx, body)` function (in `src/beamtime/serve/api.py` or beside it in `src/beamtime/ops/views.py`).
3. `dispatch_here`: unknown → `OpError(f"no API method {method!r}", code=4)`; `call(op.name, body, ctx)` if
   `op.params is not None` else `op.function()(ctx, body)`. `draft_local` = `any(body.get(p) is not None for p in
   op.draft_params)`; `ROUTED`, `WRITES` derived from `METHODS`.
4. Registry test: `drafts` ⇒ `group` or `draft` among params; `params is None` ⇒ no `positional`/`stdin`.

### O3. Answer kinds and table-driven rendering (sonnet) — code — **done**

- **Touches:** `src/beamtime/ops/registry.py` (`Op.kind`, `Op.render`), `src/beamtime/cli/format.py` (`render`
  174–256), `tests/ops/test_registry.py`, `tests/ops/test_ops.py` (301–313).
- **Read:** c2 §3 `src/beamtime/cli/format.py`, §5 tests 2–3; decision 8.
- **Check:** `uv run pytest -q tests/ops tests/cli tests/remote`; `uv run pytest -q -n0 tests/test_budgets.py`.
- **Done:** every op declares `kind` (or `None` for bytes); `render()` looks up `Op.render`, with `render=None`
  the declared `lines` fallback; a test calls every non-user-only read op on the synth fixture (`wait` with
  `timeout=0`) and asserts its text is never the raw `str(dict)`; a test asserts every declared `kind` has an
  entry in `answers.ANSWERS` and every listing's kind a `merged`.
- **Risks:** renderer imports at module level onto the CLI path (budget test; import on use like
  `Op.function()`); two ops sharing a kind with different renderers (invariant test).

1. `Op.kind: str | None = None`, `Op.render: str | None = None` (`"beamtime.cli.format:render_digest"`).
2. `render(answer)`: `BY_KIND = {m.kind: m.render for m in METHODS if m.render}` built lazily; unknown kind keeps
   the `lines` fallback.
3. The two tests above in `tests/ops/test_registry.py`.

### O4. Staleness comes from the server (sonnet) — code — **done**

- **Touches:** `src/beamtime/ops/registry.py` (`Op.stale_on`), `src/beamtime/serve/api.py` (`meta` 212),
  `web/src/api.ts` (`ALL_KINDS`/`KINDS_BY_METHOD` 239–255, 265), `tests/ops/test_registry.py`, `web/test/`,
  `src/beamtime/serve/static/`.
- **Read:** c2 §3 `web/src/api.ts`, §6 step 5.
- **Check:** `uv run pytest -q tests/ops tests/serve`; `cd web && npm ci && npm test && npm run build`.
- **Done:** `meta()["stale"]` covers every routed method; `KINDS_BY_METHOD` is gone, `api.ts` fills its map from
  `meta` and falls back to `ALL_KINDS` before `meta` lands; bundle rebuilt and committed.
- **Risks:** a call before `meta` arrives (fallback: stale on everything); an old bundle against a new server.

1. `Op.stale_on: tuple[str, ...] = ("metrics", "status", "authored")`; set narrower values exactly as
   `KINDS_BY_METHOD` has them today; invariant: values ⊆ those three.
2. `meta()` adds `"stale": {m.tool: list(m.stale_on) for m in METHODS if m.routed}`.
3. `api.ts`: `let kindsByMethod: Record<string, Kind[]> = {}`, set where the shell reads `meta`.

## S. One owner for a line chart's settings

### S1. `views/settings.py` and `settle` by round-trip (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/views/settings.py`, `src/beamtime/views/prefs.py` (`settle` 124–174 moved),
  new `tests/views/test_settings.py`.
- **Read:** `docs/plans/refactor-2-designs/c3-chart-settings.md` §2 Shape A (invariants 1–5);
  `docs/design/05-views.md` § Charts (l. 434).
- **Check:** `uv run pytest -q tests/views tests/serve/test_app.py`.
- **Done:** `prefs.settle` delegates to `settings.settle`; the defaults table (prefs.py 158–172) and the by/seeds
  inverse (139–144) are gone; `SEEDS_FIELD = "config.seed"` is the only literal; existing view-saving tests pass
  unchanged; new tests: settle is idempotent, default settings leave props clean, unknown keys dropped.
- **Risks:** `scale` must stay written explicitly (prefs.py 146–147; `test_scale_always_written`); `by: "seeds"`
  ⇔ `seeds: config.seed` and `by: k` ⇔ `by: [k]` fold both ways (`test_seeds_fold`); invalid values raise
  `SchemaError` (`test_bad_setting`).
- **Stop if:** the round-trip writes different YAML than today for any existing test view.

`settle` writes view YAML, i.e. users' files: identical output is the bar.

1. `SEEDS_FIELD`, `SETTINGS` (settable Line fields, web names), `line_defaults() -> dict[str, Any]` from
   `msgspec.structs.fields(m.Line)`.
2. `settle(props: dict, settings: dict) -> None`: merge web-named settings (folding by/seeds), decode as `m.Line`,
   dump with `omit_defaults`, write back; `scale` kept explicit.
3. `prefs.settle` calls it; `apply_prefs` signature unchanged.

### S2. Generated chart defaults (haiku) — code

- **Touches:** `src/beamtime/views/settings.py` (`generated_ts`), new `scripts/build-chart-defaults`, new
  `web/src/bt/chart-defaults.ts`, `web/package.json`, `tests/views/test_settings.py`,
  `src/beamtime/serve/static/`.
- **Read:** `scripts/build-tokens` (the pattern to clone); `tests/test_design.py` 20–30 (`script()`, the `--check`
  test).
- **Check:** `uv run pytest -q tests/views/test_settings.py`; `cd web && npm ci && npm test && npm run build`.
- **Done:** `scripts/build-chart-defaults --check` exits 0 on the committed file and 1 after editing a default in
  `m.Line`; a pytest runs it; npm script `defaults` runs it; the file is unimported, so the built bundle is
  unchanged.

1. `generated_ts() -> str`: `export const SEEDS_FIELD = "config.seed";` and `export const DEFAULTS = { line:
   {...} } as const;`, keys sorted, a header saying it is generated.
2. The script writes `web/src/bt/chart-defaults.ts`, or with `--check` compares and exits 1 when stale.
3. `"defaults": "cd .. && uv run python scripts/build-chart-defaults"` in `web/package.json`.

### S3. `chart-settings.ts` owns the web side (sonnet) — code

- **Touches:** new `web/src/bt/chart-settings.ts`, `web/src/blocks/line.ts` (`seriesCall` 37–53, `defaultsOf`
  67–85), `web/src/bt/prefs.ts` (`effective` 97–103 → `cascade`), `web/src/api.ts` (`frozenKey` 73–82),
  `web/src/kit/figure.ts`, `web/test/prefs.test.ts`, `web/test/snapshot.test.ts`, `src/beamtime/serve/static/`.
- **Read:** c3 §2 TS side, §3.
- **Check:** `cd web && npm ci && npm test && npm run build`; `uv run pytest -q tests/serve/test_chart_settings.py
  tests/serve/test_browser.py`.
- **Done:** `line.ts` has no `defaultsOf`, no `"config.seed"`, no param surgery; `prefs.ts` has no base table;
  `frozenKey` calls `normalizeSeries`; `web/src/kit/figure.ts` uses `cascade`; shell under 120 KB compressed.
- **Risks:** both bundle entries (`main.ts`, `web/src/kit/frame.ts`) still import the cascade (`npm run build`); an export
  snapshot's frozen key still matches its lookup (`snapshot.test.ts`); Playwright chart-settings tests.

1. `effective(node, prefs): Effective`, `seriesCall(node, prefs, {zoom, width}): Call`,
   `normalizeSeries(params)`: moved from `line.ts`/`prefs.ts`/`api.ts`, reading `DEFAULTS` and `SEEDS_FIELD`.
2. `prefs.ts` keeps stores, `setChart`, `setView`, `changed`, and `cascade(defaults, prefs, id)`.

### S4. The cross-wire fixture (sonnet) — code

- **Touches:** new `web/test/fixtures/chart-settings.json`, `tests/views/test_settings.py`, new
  `web/test/chart-settings.test.ts`.
- **Read:** c3 §5 (the fixture as wire contract).
- **Check:** `uv run pytest -q tests/views/test_settings.py`; `cd web && npm test`.
- **Done:** about ten cases `{settings, node, effective, series_params, frozen_key}` (defaults, log scale, smooth,
  by a key, seeds, band none, steps, raw off, x a metric, legend off); pytest asserts settle+compile produce each
  `node`; the TS test asserts `effective`/`seriesCall`/`normalizeSeries` produce the rest from the same `node`.
- **Risks:** a case where the round-trip law (c3 invariant 3) fails — record it in the report, don't bend the
  fixture.

1. Write the cases by hand from today's behaviour; Python generates nothing into the fixture.

### S5. `compile.line` uses `wire_props` (sonnet) — code

- **Touches:** `src/beamtime/views/settings.py` (`wire_props`), `src/beamtime/views/compile.py` (`line` 280–327),
  `docs/design/05-views.md`.
- **Read:** c3 §3; `docs/design/05-views.md` § Charts (l. 434), § Schema and compilation (l. 264).
- **Check:** `uv run pytest -q tests/views tests/serve/test_render.py tests/serve/test_export.py`.
- **Done:** `compile.line` has no per-prop `!= default` comparisons; the S4 fixture passes unchanged; `05-views.md`
  § Charts says chart settings have one owner, defaults reach the frontend as generated constants, the wire omits
  defaults and `scale` is always resolved.
- **Risks:** `band` is always explicit in `data.main.params` today (compile.py 291–297; fixture `band none`);
  the added-chart `template` (82–88) still built from the first line's call.

1. `wire_props(n: m.Line) -> dict[str, Any]`: `msgspec.to_builtins(n)` restricted to `SETTINGS`.
2. `compile.line` passes `**settings.wire_props(n)`; `scale`, `data`, `y`, `note` as today.

## V. One curve shape

### V1. Emit the envelope (sonnet + review) — code

- **Touches:** `src/beamtime/query/read.py` (`downsample` 102–151, `from_preview` 153–199),
  `src/beamtime/query/kinds.py` (`band_stats` 448–473, the grouped out-dicts 331–445), `tests/query/test_queries.py`,
  `docs/design/03-index.md`.
- **Read:** `docs/plans/refactor-2-designs/c6-curve-shape.md` §1, §2 Design A; `docs/design/03-index.md` § Query
  kinds (l. 284, `series`).
- **Check:** `uv run pytest -q tests/query`.
- **Done:** tests through the `ask` fixture, one per variant: raw has `y` and no band; downsampled has `y == last`,
  `lo == min`, `hi == max`, `n == count`, `lo <= y <= hi` pointwise; grouped has `y == mean`; `band: none` gives
  null `lo`/`hi`. Every existing assertion on `raw`/`min`/`max`/`mean`/`n` passes unchanged; `03-index.md`
  documents the envelope.
- **Risks:** `from_preview`'s `first: [None]*n` must not leak into `y` (`test_preview_envelope`); a single-point
  run (`test_single_point_envelope`); the 30k-point chart budget with ~1.7× JSON (`test_budget_envelope`).

1. `downsample`/`from_preview` non-raw: add `y = last`, `lo = min`, `hi = max`, `n = count` (same lists, not
   copies).
2. Grouped curves: add `y = mean`.
3. `03-index.md` series spec (~329–331, 452–458): the envelope, and that the old fields stay.

### V2. Python consumers read the envelope (sonnet) — code

- **Touches:** `src/beamtime/cli/format.py` (`curve_line` 118–146), `src/beamtime/ops/reading.py` (`table_of`
  800–841), `src/beamtime/query/kinds.py` (319), `tests/ops/test_ops.py`, `tests/cli/test_commands.py`.
- **Read:** c6 §3.
- **Check:** `uv run pytest -q tests/ops tests/cli tests/query`.
- **Done:** `curve_line` reads `y`/`lo`/`hi`, labels from `by` or `name`, and probes neither `raw` nor `"by" in`
  for values; `table_of` collapses identical arrays into one column, preferring envelope names, so a downsampled
  CSV has no duplicate columns.
- **Risks:** `runs --to x.csv` and `series --to` column names (`tests/ops/test_tools.py` export tests);
  `kinds.py:319` reads `first` for metric-x deliberately: change it only if `x` is equivalent there, else leave it
  and say why.

1. `curve_line`: one path over `y`, band from `lo`/`hi` else `y`.
2. `table_of`: after flattening, drop a column whose values equal an earlier column's, keeping the envelope name.

### V3. Old remotes' curves are upgraded (sonnet + review) — code

- **Touches:** `src/beamtime/ops/answers.py` (`SeriesAnswer.placed`, new `upgrade_curve`), new
  `tests/remote/fixtures/series-0.2.json`, `tests/remote/test_answers.py`, `docs/design/04-remotes.md`.
- **Read:** c6 §2 (the forever-compat surface), decision 9; `docs/design/04-remotes.md` § Protocol (l. 201).
- **Check:** `uv run pytest -q tests/remote`.
- **Done:** the pinned old-shape answer (raw, downsampled and grouped curves, hand-written once, never
  regenerated) comes out of `answers.placed(..., "box")` with the envelope; an already-enveloped curve is
  returned unchanged.
- **Risks:** a curve with `y` already present must not be overwritten (`test_upgrade_idempotent`); grouped curves
  carry `lo`/`hi` already, only `y` is added (`test_upgrade_grouped`).

1. `upgrade_curve(c: dict) -> dict`: if `"y" not in c`: grouped (`"mean" in c`) gains `y`; downsampled gains
   `y`, `lo`, `hi`, `n` from `last`, `min`, `max`, `count`.
2. `SeriesAnswer.placed` maps it over `curves` before placing.
3. One line in `04-remotes.md` § Protocol: a newer hub upgrades older remotes' curves.

### V4. Web and kit read the envelope (sonnet + review) — code

- **Touches:** `web/src/bt/curves.ts` (`reshape` 28–68), `web/src/blocks/table.ts` (`sparks` 120),
  `web/src/kit/shape.ts` (`curve` 40–52), `web/test/curves.test.ts`, `web/test/kit.test.ts`,
  `src/beamtime/guide/parts/kit-api.md`, `docs/design/05-views.md`, `src/beamtime/serve/static/`.
- **Read:** c6 §1 (the kit is a public interface), §3; `docs/design/05-views.md` § The `bt` kit API (l. 335).
- **Check:** `cd web && npm ci && npm test && npm run build`; `uv run pytest -q tests/serve/test_browser.py
  tests/views/test_custom.py tests/guide`.
- **Done:** `reshape` reads `y`/`lo`/`hi`/`n` and uses `"by" in c` only for labels; `sparks` reads `c.y`;
  `shape.ts` passes the answer's fields through and `KitCurve` gains `y`, `lo`, `hi`, `n`; `min`, `max`, `last`,
  `mean`, `count` still reach kit blocks; `kit-api.md` and `05-views.md` document the addition.
- **Risks:** a custom block reading `c.min` (`kit.test.ts`); the bt/kit naming disagreement (c6 §1) must end
  with both vocabularies present, not one renamed; shell size.

1. `curves.test.ts` fixtures rewritten to enveloped answers in this commit.
2. `kit-api.md`: curves are `{run, key, group, x, y, lo?, hi?, n?}` plus the version 1 fields.

## Q. Run facts from the index

### Q1. Conditions belong to the query language (sonnet) — code

- **Touches:** `src/beamtime/cli/conditions.py` → new `src/beamtime/query/conditions.py`, `src/beamtime/cli/__init__.py`
  (227), `src/beamtime/ops/reading.py` (589), `src/beamtime/mcp/skills.py` → new `src/beamtime/guide/skills.py`,
  `src/beamtime/ops/admin.py` (639), `scripts/build-plugin` (21), `tests/mcp/test_skills.py`,
  `tests/test_boundaries.py`, `docs/design/03-index.md`.
- **Read:** `docs/plans/refactor-2-designs/c4-run-facts.md` §1 (inverted layering), §3; decision 11;
  `docs/design/03-index.md` § CLI and MCP (l. 409).
- **Check:** `uv run pytest -q tests/test_boundaries.py tests/cli tests/mcp tests/ops`;
  `uv run pytest -q -n0 tests/test_budgets.py`.
- **Done:** a new boundary test walks every import (function bodies too) in `query/`, `index/`, `ops/`,
  `record/`, `remote/`, `format/`, `sdk/` and finds none naming `beamtime.cli` or `beamtime.mcp`; it fails on
  the base commit; `03-index.md` names `src/beamtime/query/conditions.py` as the condition string's home.
- **Risks:** `parse_where` messages name `--where`; `wait` passes `flag="until"` (`tests/ops/test_tools.py` wait
  tests); `beamtime mcp install` still writes skills (`tests/mcp/test_skills.py`).

1. `git mv` both modules; update importers; `parse_where(..., flag: str = "--where")`.
2. The boundary test with `ast.walk` over `Import`/`ImportFrom`.

### Q2. `run.attempts` and `run.last_logged` (sonnet + review) — code

- **Touches:** `src/beamtime/index/store.py` (`SCHEMA_VERSION` 9, `SCHEMA` 11), `src/beamtime/index/ingest.py`
  (97, 203), `src/beamtime/query/fields.py` (36–49), `tests/index/`, `tests/query/test_queries.py`,
  `docs/design/03-index.md`, `CHANGELOG.md`.
- **Read:** c4 §2 Shape B item 1; `docs/design/03-index.md` § Fields (l. 211), § Implementation notes (l. 428).
- **Check:** `uv run pytest -q tests/index tests/query`.
- **Done:** `SCHEMA_VERSION = 3`, a v2 cache rebuilds on open; `runs --where 'run.attempts>1'` and `sort:
  -run.last_logged` work on synth runs; `last_logged` equals `_metrics.jsonl`'s mtime after ingest; the fields
  table in `03-index.md` lists both.
- **Risks:** a run without metrics → `last_logged` null (`test_last_logged_no_metrics`); incremental ingest
  updates `metrics_mtime` when only metrics grew (`test_last_logged_tracks_appends`); a resumed run's attempts
  (`test_attempts_after_requeue`).

1. Column `metrics_mtime REAL` beside `metrics_size`; ingest writes it where it writes the size.
2. `run.attempts` → `json_array_length(info, '$.attempts')` (0 when absent); `run.last_logged` →
   `metrics_mtime`. CHANGELOG (Added; the cache rebuilds once).

### Q3. `query/facts.py` (sonnet) — code

- **Touches:** new `src/beamtime/query/facts.py`, new `tests/query/test_facts.py`, `src/beamtime/ops/reading.py`
  (new `run_members`).
- **Read:** c4 §2 `RunFacts`/`run_facts` (invariants), §5 `failure_key`; `src/beamtime/query/resolve.py`.
- **Check:** `uv run pytest -q tests/query/test_facts.py tests/ops`.
- **Done:** tests on the synth log dir: statuses derived at `now`; `where` filters; `config`/`metrics` `None`
  unless asked; `attempts`; `last_logged`; a bad target raises `QueryError`; one index open and one `catch_up` per
  call. Nothing consumes it yet.
- **Risks:** `run_facts` reading any run file (assert with a log dir whose cards are deleted after ingest —
  `test_facts_from_index_only`); flattened config matches `read_config`'s (`test_config_flattened`).

1. `RunFacts` and `run_facts(index, *, scope, run_id, now, where=None, depth="all", config=False, metrics=False)`
   as in c4 §2, on `select_runs`.
2. `failure_key(error: str | None, traceback: list[str] | None) -> str`: today's `failure_signature` of `error`
   if set, else of the traceback's exception line.
3. `reading.run_members(ctx, target, where=None, depth="all", *, config=False, metrics=False) ->
   list[RunFacts]`: resolves `target` with `resolve`, maps `QueryError` to `OpError`, passes `ctx.now`.

### Q4. `wait`, `diagnose` and `logs` on run facts (sonnet + review) — code

- **Touches:** `src/beamtime/ops/reading.py` (`wait` 581–643, `diagnose` 645–700, `logs` 511–579),
  `tests/ops/test_tools.py`, `docs/design/03-index.md`, `CHANGELOG.md`.
- **Read:** c4 §1 table, §3, §5 (one failure-signature rule).
- **Check:** `uv run pytest -q tests/ops/test_tools.py tests/remote`.
- **Done:** the three ops call `run_members` and read no `read_card`, `read_run_info` or `mtime`; `logs` keys
  signatures with `failure_key(f.error, trace)`; `diagnose`'s `stalled` uses `last_logged` at `ctx.now`; answers'
  shapes unchanged; `03-index.md` says signatures are grouping labels, not identifiers.
- **Risks:** `test_logs_group_tracebacks_by_signature` (84) — if it changes, the card-led value is the new truth:
  replace the assertion, don't layer; `wait`'s poll loop opens the index once per tick.

1. Per c4 §3 usage: `wait` (no config/metrics), `diagnose` (metrics), `logs` (`read_output(f.dir, rank)` stays).
2. CHANGELOG (Changed: `logs` signatures follow the card's error when there is one).

### Q5. `compare` and `digest` on run facts; `members()` deleted (sonnet) — code

- **Touches:** `src/beamtime/ops/reading.py` (`members` 214–237 removed, `compare` 240–347, `entity_config` 309,
  `last_values` 323, `digest` 349–509, `best_per_setting` 419–427, `failures` 447–461), `tests/ops/test_tools.py`,
  new `tests/remote/test_snapshot_tools.py`, `docs/design/03-index.md`.
- **Read:** c4 §3, §6 (snapshot test).
- **Check:** `uv run pytest -q tests/ops tests/remote`.
- **Done:** `members` is gone; `rg -n 'read_card|read_config|read_run_info' src/beamtime/ops/reading.py` hits only
  `card`, `resume` and `output`; a snapshot-shaped folder (synth group copied with mtimes, `_snapshot.json`) runs
  `digest` and `diagnose` through `from_snapshot`, with `stalled` judged at the snapshot's time.
- **Risks:** compare's config diff over flattened config (`tests/ops/test_tools.py` compare tests); digest's best
  per setting with a metric missing from some runs.

1. Rewrite the helpers over `RunFacts`; `failures` uses `failure_key(f.error, None)`.
2. `03-index.md` § Implementation notes: run facts come from the index.

## K. Query params declared once

### K1. `seeds` where it is read; a lazy `query` package (sonnet) — code

- **Touches:** `src/beamtime/query/models.py` (`Selection` 39–45, `Runs` 52–58, `Series` 67–76),
  `src/beamtime/query/__init__.py`, `tests/query/test_queries.py`, `docs/design/03-index.md`, `CHANGELOG.md`.
- **Read:** `docs/plans/refactor-2-designs/c5-params-once.md` §1 (drift 2), §3 hard constraints.
- **Check:** `uv run pytest -q tests/query tests/ops`; `uv run pytest -q -n0 tests/test_budgets.py`.
- **Done:** `{keys: {seeds: "config.seed"}}` raises `QueryError` (a test fails before); `import
  beamtime.query.models` imports no `Index`, `kinds` or `select` (a test checks `sys.modules` in a subprocess).
- **Risks:** an importer relying on `from beamtime.query import Index` or similar (`rg` it); budgets measured
  serially on an idle machine.

1. Move `seeds` to `Runs` and `Series`.
2. `src/beamtime/query/__init__.py`: `QueryError` eager from `models`; `Index`, `KIND_FUNCTIONS`, `select` imported inside
   `run()`. CHANGELOG (Changed: `seeds` on other kinds is an error).

### K2. Descriptions live with the query structs (haiku) — code

- **Touches:** `src/beamtime/query/models.py`, `src/beamtime/ops/registry.py` (`Where`/`Fields` 14–26, field
  `Meta`s 42–209).
- **Read:** c5 §3, §6 step 3.
- **Check:** `uv run pytest -q tests/mcp tests/test_docs.py tests/ops`; `uv run pytest -q -n0
  tests/test_budgets.py`.
- **Done:** `Where`, `Fields` and the per-field descriptions are defined in `models.py` and imported by the
  registry; every MCP tool schema is byte-identical before and after (dump `mcp.server` tools to a scratch file
  first, compare after).
- **Stop if:** any schema differs.

1. Move the `Annotated` aliases and `Meta(description=...)` into `models.py`; the registry imports them.

### K3. Params subclass their query structs (sonnet + review) — code

- **Touches:** `src/beamtime/ops/registry.py` (`Selection` 42–50, `KeysParams` 52, `GroupsParams` 56,
  `RunsParams` 60–81, `SeriesParams` 90–114, `DataParams` 117–122, `TimelineParams` 183–189, `QueryParams`
  203–209), `src/beamtime/views/code.py` (11), new `tests/ops/test_params.py`, `docs/reference/cli.md`,
  `CHANGELOG.md`.
- **Read:** c5 §3 Design A (msgspec limits), §5.
- **Check:** `uv run pytest -q tests/ops tests/mcp tests/cli tests/test_docs.py`; `uv run python
  docs/site/reference.py`; `uv run pytest -q -n0 tests/test_budgets.py`.
- **Done:** each of the six params structs subclasses its query struct; tests pin that the extras are a subset
  of `{cursor, to, draft, smooth}` and `code.KINDS == tuple(k for k in models.KINDS if k != "importance")`;
  `QueryParams`'s kind list derives from `models.KINDS`; `cli.md` regenerated; the MCP size test passes.
- **Risks:** multiple inheritance of field-bearing structs fails (`Cursor`/`To` per struct, not mixed in);
  `SeriesParams.smooth: float | None` overriding `Smooth` (`test_smooth_flat`); CLI positionals by name.

1. `Cursor`, `To` aliases; `class RunsParams(q.Runs, kw_only=True)` etc.; `Selection(q.Selection)` + `cursor`
   for logs/wait/diagnose. `FileParams` stays as it is. CHANGELOG (Changed: MCP property order).

### K4. The reading adapters collapse to `body()` (sonnet) — code

- **Touches:** `src/beamtime/ops/reading.py` (`selection` 92–97 removed, `keys`, `groups`, `runs`, `series`,
  `data`, `timeline` 100–202).
- **Read:** c5 §4.
- **Check:** `uv run pytest -q tests/ops tests/cli tests/mcp tests/remote`.
- **Done:** `selection` is gone; `body(p)` = `msgspec.to_builtins(p)` without `cursor`/`to`; what remains in
  `runs`/`series` is paging, export and smooth flattening; every existing test passes unchanged.
- **Risks:** `to_builtins` emits `from`, not `from_` (`test_from_encoded`); `None` fields omitted vs sent
  explicitly as today.

## X. Close

### X1. Close (sonnet) — code

- **Touches:** `CHANGELOG.md`, `CLAUDE.md`, `docs/design/`, `todo`.
- **Read:** Breaking changes, Decisions and Not verified in this plan.
- **Check:** `cd web && npm ci && npm test && npm run build` with a clean `git status`; the full checks;
  `uv run pytest -q -n0 tests/test_budgets.py`; the Goal's greps.
- **Done:** `## 0.3.0 (unreleased)` lists every row of Breaking changes; `CLAUDE.md` names the new modules
  (`format/place.py`, `query/resolve.py`, `query/facts.py`, `query/conditions.py`, `ops/answers.py`,
  `views/settings.py`, `guide/skills.py`, `scripts/build-chart-defaults`, `web/src/bt/chart-settings.ts`); the
  version in `pyproject.toml` stays 0.2.2 (decision 15); nothing published, tagged or pushed.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| `seeds` on `keys`/`groups`/`data`/`timeline` queries (K1) | accepted, ignored | `QueryError` | drop it |
| Run lookup (P3, P4) | suffix and name only in `card`-style CLI lookups | id, unique suffix or name everywhere, web URLs too | none |
| Unknown group on a web page (P4) | sibling suggestions | siblings and top-level groups | none |
| Reserved names in page URLs (P4) | served | refused | none |
| Index cache (Q2) | schema 2 | schema 3; rebuilds once on first use | none, it's a cache |
| `logs` failure signatures (Q4) | from the output's last traceback | from the card's error when present | signatures are labels |
| Federated `runs --by`/`--seeds` (R3) | unlabelled rows, arbitrary order | a `source` column, per-source order | none |
| Federated listing paging (R4, R4b) | each source cut, local cursor reused | sources answer whole, merged answer cut once; `meta.sources[].cut` only for old remotes and answers over 2 MB | follow `meta.next` |
| Series curves (V1) | three shapes | plus `y`/`lo`/`hi`/`n` on all; old fields stay | none |
| MCP tool schemas (K3) | `cursor` first | `cursor` last | none |
| MCP instructions (O1) | 8 user-only commands named | all 18 | none |

## Not verified

Dry-run at `7268916` (2026-11-10): ruff clean; `uv run pytest -q` 752 passed, 5 skipped (venv rebuilt with `uv sync --all-extras`); every test path
the Checks name collects (tests named as new don't exist yet); `npm ci && npm test` 73 passed, `npm run build`
leaves `src/beamtime/serve/static/` unchanged; browser tests run here; `tests/test_budgets.py -n0` failed once
right after the full suite and passed on rerun. Assumed, not run:

- msgspec subclass overrides and the 0.6 ms `query.models` import were measured by the design pass, not in this
  planning session (K1, K3 check them).
- K2's MCP schemas byte-identical after moving descriptions (K2 compares; stop if not).
- `docs/site/reference.py` produces an unchanged `cli.md` after O2, because `OPS` stays derived (O2 runs
  `tests/test_docs.py`).
- Every remote series answer passes `answers.placed` after R1 (V3 assumes it, decision 9).
- `test_logs_group_tracebacks_by_signature` stays green under `failure_key` (Q4 checks).
- The `box` fixture serves a second source for end-to-end federation tests (R3 checks).
- All line ranges are at `7268916`; P, R and O move code that later tickets name.
