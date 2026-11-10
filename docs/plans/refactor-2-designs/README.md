# Refactor 2: architecture deepening designs

Input material for a ticketed implementation plan (`/plan-tickets`). Produced 2026-11-10 at base commit
`7268916` ("0.2.2: steady the browser tests and harden the live hub") by an architecture review of the
codebase's hot spots (most-changed files over the last 300 commits), followed by one design pass per
candidate. Every design verified its diagnosis against source and corrected the review's line refs.

Vocabulary throughout: **module** (interface + implementation), **interface** (everything a caller must
know), **depth/shallow** (behaviour per unit of interface), **seam** (where an interface lives),
**adapter** (one = hypothetical seam, two = real), **leverage**, **locality**, **deletion test**.

Each design states: verified diagnosis with line refs, the interface designed twice with the rejected
alternative and why, what the implementation hides, the testing story (survive / die / new), and a
migration path of green steps with rough scope. These are the designs, not the plan — scope, ticket
cuts and ordering are the plan's job.

| # | Design | Recommendation | Strength |
|---|---|---|---|
| C1 | [answers own their places](c1-answer-seam.md) — the remote answer seam | `ops/answers.py`: a protocol per answer kind (`placed`/`merged`/`paged`) | Strong |
| C2 | [one descriptor per method](c2-operation-descriptors.md) — deepen the registry | one flat extended `Op`, page methods registered too | Strong |
| C3 | [one owner for a line chart's settings](c3-chart-settings.md) | `views/settings.py` as source + build-time generated TS constants | Strong |
| C4 | [run facts belong to the query layer](c4-run-facts.md) | two new run fields + internal `query/facts.py` (**not** a new query kind) | Worth exploring |
| C5 | [query params declared once](c5-params-once.md) | **go, scoped**: params structs inherit the query structs; views stay separate | Speculative → go |
| C6 | [one curve shape](c6-curve-shape.md) | additive canonical envelope (`y`/`lo`/`hi`/`n`), not a variant tag | Worth exploring |
| C7 | [a place is a value](c7-place-value.md) — `@source/path` | frozen `Place` in `format/` + `resolve()` in `query/` | Worth exploring |

## Bugs found while designing (not yet fixed)

1. **`wait` over a remote turns a status into a path.** `"from"` is in `route.PATH_KEYS`, and `wait`'s
   `changed[].from` is an old *status*, so `beamtime wait @box/g` answers `"from": "@box/running"`.
   (C1 §1; `remote/route.py:24` + `ops/reading.py:611-620`.)
2. **`compare` over a remote returns targets without their `@box/` prefix.** `"target"` is not in
   `PATH_KEYS`. (C1 §1; `ops/reading.py:282-290`.)
3. **Federated `runs --by` returns unlabelled rows in arbitrary order.** `merge_runs` hard-codes the
   `-run.created_at` default that `query/kinds.py:58` suppresses when `by`/`seeds` is set, then sorts on
   a `run.id` column aggregated rows don't have. (C1 §1.)
4. **A federated listing can answer N× the token budget.** Each source cuts at the budget; the merged
   answer is never cut again, and `meta.next` is the local source's cursor applied to every source.
   (C1 §1.)
5. **The MCP `INSTRUCTIONS` user-only list has already drifted** — it names 8 commands; the registry has
   18 `user_only` ops. (C2 §1; `mcp/server.py:18-28`.)
6. **`{keys: {seeds: x}}` validates and is silently ignored** — `seeds` sits on `models.Selection` but is
   read only by `runs` and `series`. (C5 §1.)

## Cross-candidate ordering the designs agreed on

- **C7 steps 1+4 before C1** — C1's `Place` should be built on the place value, and `route.strip`/
  `strip_local` die in C7 step 4 rather than being carried into the new seam.
- **C1 before C2's kind/render step** — `Op.kind` is the join key between the descriptor and the
  per-answer-kind classes; C2's conformance test ("every listing kind has an entry") is what stops a
  second registry from growing.
- **C3 before C6's web step** — both edit `line.ts`'s call-building; C6 is cleaner on a stable
  `effective`/`seriesCall` seam.
- **C4 before C5** — C4 deletes `members()` and shrinks `reading.py`'s plumbing; C5 then collapses the
  remaining query adapters. (Alternatively scope C4 away from `keys/groups/runs/series/data/timeline`.)
- **C2 before C5** — both edit `registry.py` on different axes; re-parenting 15 param structs should not
  rebase over the `Op` reshaping.
- **Shared generated outputs serialize**: anything touching `src/beamtime/serve/static/` (C3 step 3,
  C6 steps 4-5) rebuilds the committed bundle, so those steps cannot run in parallel. Same for
  `docs/reference/cli.md` (C5 step 4).

Derived sequence satisfying all of the above: **C7(1,4) → C1 → C2 → C3 → C6 → C4 → C5**, with C7's
remaining call-site conversions and C2's early steps parallelizable against the Python-only work.

## Project rules these designs already account for

- Files are the source of truth; every file has one writer; readers accept every schema version forever,
  no migrations. Deviations from `docs/design/` are decided and written back into the design doc before
  the code lands (each design names its write-back).
- The CLI path stays light (`tests/test_budgets.py`, 150 ms); `sdk/`, `format/`, `synth/` stay Python 3.10
  + stdlib + PyYAML (`tests/test_boundaries.py`).
- After any `web/` change: `cd web && npm ci && npm test && npm run build`, commit the rebuilt
  `src/beamtime/serve/static/`; the shell stays under 120 KB compressed.
- Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`; budgets need an idle
  machine (`uv run pytest -q -n0 tests/test_budgets.py`).
