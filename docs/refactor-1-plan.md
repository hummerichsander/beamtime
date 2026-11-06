# Refactor 1: plan after the first human end-to-end tests

Status: **in progress.** Done on branch `refactor-1`: F1 `88fc5b5`, A1 `e2a5cb6`, A2 `dada516`, A3 `6899788`, A4 `3942900`, A5 `0297ea2`, A6 `c0aa283`, A7 `9c286ec`, A8 `bd71c5b`, A9 `4d03f19`, D1 `b7244e1`, D2 `f9f1f40`, D3 `3761001`, D4 `18adc31` (D1 to D3 reviewed in `dc72616` and `33c4fff`), E1 `d9130b0`, E2 `6583a26`, E3 `2ae9cf5`, E4 `c46417e` (E1 to E3 reviewed in `a513e2b` and `5d7a83a`), B1 `0d11c23`.
Proposed 2026-11-04, based on the findings in `todo`, the code at `8165346`, the real log
dir at `au002a:/remote/gpu04/hummerich/projects/split-flows-public/beamtime` (78 runs, 12 groups, 10
custom code files) and 65 agent sessions on that project. Breaking changes are allowed where they make
the code leaner; they are listed in [Breaking changes](#breaking-changes).

Every chunk below is written to be executed on its own by a cheaper model. Read
[Brief](#brief), [How to execute](#how-to-execute) and your chunk's [manifest](#manifests) first.

## The findings, in one table

Evidence tags: **reproduced** (run in a browser or on real data), **real data** (seen on the remote),
**code** (read in the code, not run; the chunk starts by reproducing it).

| # | Finding | Root cause | Evidence | Chunk |
|---|---|---|---|---|
| 1 | Custom charts don't update live | The bridge effect in `blocks/custom.ts` depends on `code.data`, a new object after every refetch. Each live tick unsubscribes all the frame's queries; the frame never subscribes again because it is already `started`. In the run: built-in series refetched 18 times, custom series 2 times. **Worse:** when runs stop, the restarted timer turns the block into "no first render within 15 s". | reproduced | A1 |
| 2 | Wall-clock x shows nonsense for means | Not a sum: `grouped_curve` never reads `q.x`. It returns step buckets, and the frontend formats those steps as times. | code | B2 |
| 3 | `best energy/CMMotionRemover_w1 0 · … (hparam…` | Two bugs. `essential()` only knows `val`/`train`, so `validation/*` and `training/*` fall through to the alphabetically first metric, here a constant 0. `varying_config` returns 22 keys, nearly all nested aliases of `arm` and `seed`. | real data | A5 |
| 4 | `[object Object]` hyperparameters | `fmt.value` ends in `String(v)`. Used by the drawer, table cells and tooltips. Real configs have 193 flattened keys. | code | A2 |
| 5 | A single point draws nothing | `points: { show: false }` on every series; a one-point path is empty. `Spark` also returns blank below 2 points. | code | A3 |
| 6 | Bands broken in log mode | `reshape` nulls non-positive `lo`/`hi` (mean − std is often ≤ 0), which leaves holes in the band polygon; the transparent band series also stretch the auto range. | code | A4 |
| 7 | No axis labels | The chart has none. An agent wrote a whole d3 block for it: `curves.js` opens with "axis titles the built-in line chart cannot draw". Captions carry the rest ("x: training step (1407 per epoch). y: …"). | real data | B3 |
| 8 | Agents can't get built-in chart features | All 7 custom code files on the remote that read data (block versions included) hand-roll d3; 0 use `bt.chart.Line`. They lose hover, settings, downloads. `predictions.js` says the kit exposes "neither the app's status pill nor the check, so … the rows are typed in". | real data | C1, C2, C3, G1 |
| 9 | Epoch chart is tedious | Lightning logs `epoch` 8502 times as a step function. It is a clock, not a measurement. `curves.js` converts x by hand (`x / 1407`). | real data | B6 |
| 10 | Unclear which charts are default | Two kinds of chart (essential grid, addable extras) with different controls, plus a "More metrics" section. | code | B7 |
| 11 | Local agent can't do remote views | First call failed on the real setup: "view new works on drafts in this project; for a group on @au002a, run it there (ssh)". Notes, proposals and memory already route. | real data | D2 |
| 12 | A local log dir is required | `serve` raises without one and always starts the daemon; `beamtime-serve/` exists only to hold an empty `beamtime/`. | code | D1 |
| 13 | Requeued job starts a new run | Designed that way (`02-sdk.md`, "Later: auto resume"). All 78 real runs have one attempt. | code, real data | E1 |
| 14 | No copy | `mv` exists; a copy needs a new id and a decision about proposal membership. | code | E2 |
| 15 | Code versioning | Mostly **already there**: `_run.json.git`, `_env/git.diff`, `run.commit`. Gaps: not visible in tables or groups, untracked files are missed, and two dirty runs can't be compared. A real run carries a 376 KB diff with only `dirty: true` to identify it. | real data | E3 |
| 16 | Tools for agents | 85 raw `python`/`grep` calls over `beamtime/`, 90 `tail`, 8 sleep loops. `runs` was tried with `by`, which it lacks. | real data | G4 |
| 17 | `view_render` dominates MCP output | `screenshots()` is full-page PNG with no height limit, and `mcp/server.py:content()` embeds every shot. In the sandbox project, 3 calls were 90.7 % of Beamtime's MCP output by characters, about 255 KB per image. In the 65 cluster sessions it was never called, for a reason not checked. | real data | A9 |
| 18 | The proposal block fails on a remote page: "no group '…' below the log dir" | `remote/route.py:prefix()` skips every key in `USER_CONTENT`, which includes `proposal` (a proposal's text). The proposal block keeps its `proposal_show` call under `data.proposal` (`views/compile.py`), so that call keeps a bare group and the serving machine looks it up in its own log dir. The block's `check` call gets its prefix. | reproduced | D4 |

Also found, not in the findings:

- **Sweeps with more than 10 values never count as varying**: `summarize` returns a dict above 10
  distinct values and `varying_config` only accepts lists. Fixed in A5.
- **Seed means break on real configs**: `seed_groups` pops only the top-level `seed`, but `hydrantic.seed`
  and timestamped `default_root_dir` also vary, so every run becomes its own group. Fixed in A5.
- **Hover on float x axes is wrong**: the union x axis leaves each curve null almost everywhere, so the
  tooltip shows one curve. The tooltip also says "step" whatever the axis is. Fixed in B3.
- **Every live tick refetches `view`, `code`, `notes`, `memory_show`, `summary`, `status`, `groups` and
  `runs`** (about every 2 s in the repro), over ssh on a remote. Fixed in A1 and A6.

## Brief

What the remaining chunks build, so a session doesn't rediscover the design:

- **Charts** (B): every chart sits in one `ChartFrame` (`web/src/bt/frame.ts`: head, settings, legend, downloads);
  blocks keep only their data and spec. x values come from the server (`query/read.py:x_values`), never from
  formatting steps. Every axis has a label. All chart choices (x, scale, colormap, color by) are per-chart prefs,
  applied page-wide through `prefs.view`; Beamtime's settings hold no colormap.
- **Default view** (B6, B7): one kind of chart, in sections by metric prefix; no essential grid. Clocks (`epoch`) are
  an x axis and a progress fact, not charts.
- **Run lifecycle UI** (E5): attempts, time limits, checkpoints, copies and code versions shown from data E1 to E3
  already answer.
- **Kit v2** (C): three tiers (YAML block, `bt.chart.*`, `bt.chart.Figure`); the app's vocabulary (`Sym`, `Tag`,
  `Icon`, `Predictions`, `theme.tone`) is exported, so custom blocks never retype it. The validator's lints point
  to the guide.
- **Agents** (G): the guide by topic (`beamtime guide <topic>`), skills generated from it, a harness in
  `bench/agents/` with scores, and new tools through `ops/registry.py`.

Done, for every chunk: its **Done** line holds; the checks in How to execute pass; `docs/design/` says what the
code does; its heading in this plan and the status line carry the commit hash.

## How to execute

For the agent running a chunk:

1. Read `CLAUDE.md`, this section and your chunk. Read the design sections it names. Don't read the rest.
2. Where the evidence tag is **code**, reproduce first with a failing test. If the cause turns out to be
   different, stop and report instead of patching around it.
3. Follow the style in `CLAUDE.md`: lean, flat, no private dict-bundling helpers, docstrings with
   `:param:`, comments only for a non-obvious why.
4. Write deviations and new behaviour back into `docs/design/` in the same commit, including the
   "Later" entries a chunk completes.
5. Checks before every commit:
   `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`.
   After any change in `web/`: `cd web && npm ci && npm test && npm run build`, and commit the rebuilt
   `src/beamtime/serve/static/` (the shell stays under 120 KB compressed). SDK changes also run the 3.10
   command in `CLAUDE.md`.
6. UI rules: values only in `design/tokens.json`, type sizes only from type classes, new components get
   rules in `design/components/` and a place in `gallery.html`.
7. Keep NumPy, PyYAML and `importlib.metadata` off the `beamtime runs` import path
   (`tests/test_budgets.py`). `sdk/`, `format/`, `synth/` stay on Python 3.10, stdlib and PyYAML.
8. Never touch `tests/golden/schema1/`. Readers keep accepting every file already on disk; new fields in
   `_run.json` and notes are optional and need no schema bump.
9. One commit per chunk (G4: one per tool). Then record its hash in the chunk's heading
   (`— **done `abc1234`**`) and in the status line at the top, as a separate commit. Ask before making a worktree. **Web chunks run one at a time**, since the
   committed bundle conflicts otherwise; A-web, B and C are therefore sequential. D and E backend parts
   can run in parallel.

Model tiers: **haiku** for mechanical chunks, **sonnet** for the default, **sonnet + review** where a
mistake is expensive: have a stronger model read the diff afterwards.

### Running a chunk cheaply

- A fresh session per chunk, started with the chunk's prompt from [Manifests](#manifests). Read what the manifest
  names, at the line ranges it gives (they are from `e476dbf`; search the symbol if a range has moved).
- Mechanical changes with tools: `git mv` for moves, `ruff check --fix` for imports, `sed` for renames. Then let
  the tests find what's left instead of reading every caller.
- Small output: `pytest -q` (or `-q -x` on a subset while working, the full run before the commit),
  `git diff --stat`, `grep -n` with a path. Never print a bundle file or `src/beamtime/serve/static/`.
- A subagent only for a search that would flood the context (every caller across `web/src`, say), asked for
  the conclusion, not the hits.
- Questions go at the end of the session, not along the way.

## Order

```
F1 ─┬─ A1 A2 A3 A4 A5 A6 A7 A8 A9     bugs, independent (all done)
    ├─ B1 ─ B2 ─ B3 ─ B4 ─ B5 ─ B6 ─ B7    charts, in this order
    │              └─ C1 ─ C2 ─ C3         agent chart parity
    ├─ D1 ─ D2 ─ D3 ─ D4                   sources and remote writes (done)
    ├─ E1   E2   E3 ─ E4 ··· E5           run lifecycle (E1 to E4 done); E5, its UI, after B7
    └─ G1 ─ G2 ─ G3 ─ G4                   guides, harness, tools (G1 after C3; G3 after D2)
                              Z            docs, changelog, release
```

If time is short: B1 to B3 remove most of the remaining daily friction. What's left runs in this order, one
session at a time in the main checkout (every chunk touches `web/` or the guide): B1 B2 B3 B4 B5 B6 B7 E5 C1 C2 C3
G1 G2 G3 G4 Z.

## Manifests

Per remaining chunk: what it touches (line ranges at `e476dbf`), what to read, the done check, and the prompt that
starts a fresh session. Chunks tagged **+ review** get a review session afterwards, on a stronger model:

- **Review prompt** (replace `<X>`): `Review chunk <X> of docs/refactor-1-plan.md (its commit is in the chunk heading). Read the plan's Brief, How to execute, <X>'s manifest and chunk, Breaking changes and Decisions. Report bugs, departures from the plan and CLAUDE.md or design/ violations, ranked, with file:line and a failure case. Run the done check. Fix confirmed defects in one commit "Review fixes for <X>"; list departures that need a decision for me. Don't push.`

### B1

- **Touches:** `web/src/blocks/line.ts` (`Chart` 83–249, `Settings` 250–326, `LEGEND_MAX` 25), `web/src/blocks/plots.ts` (`PlotFrame` 280–339, `ValueLegend` 340–352); new `web/src/bt/frame.ts`, `web/src/blocks/line-settings.ts`; `design/gallery.html` and `design/components/Note.md` for `NoteType` (`web/src/blocks/context.ts:230`).
- **Read:** `docs/design/07-web-ui.md` § Charts (l. 350); `design/components/Chart.md`.
- **Done check:** `cd web && npm ci && npm test && npm run build`, then the Python checks; bundle committed; `uv run pytest -q tests/serve/test_browser.py tests/test_design.py`; `bench/web/timing.py` within budget.
- **Note:** No behaviour change. + review.
- **Prompt:** `Implement chunk B1 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, B1's manifest and chunk B1; read other files only as the manifest or the code leads you. Commit when B1's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### B2

- **Touches:** `src/beamtime/query/read.py` (new `x_values`; `elapsed_values` 226, `bucket_means` 263), `src/beamtime/query/kinds.py` (`run_curve` 272–315, `map_x` 316 removed, `grouped_curve` 332); tests in `tests/query/test_read.py` and `tests/query/test_queries.py` (the plan's `test_series.py` doesn't exist).
- **Read:** `docs/design/03-index.md` § Query kinds (l. 272), § Answers (l. 373).
- **Done check:** `uv run pytest -q tests/query` while working, then `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`.
- **Note:** Tagged code: failing test first. + review.
- **Prompt:** `Implement chunk B2 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, B2's manifest and chunk B2; read other files only as the manifest or the code leads you. Commit when B2's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### B3

- **Touches:** `web/src/bt/uplot.ts` (`lineChart` 46, axes 121–124, `plotChart` 383, axes 406–407), `web/src/bt/curves.ts` (`align` 104), `web/src/bt/plot.ts`, `web/src/blocks/line.ts` (`X_AXES` 26, `formatterFor` 327), `web/src/blocks/plots.ts`, `web/src/bt/shapes.ts` (time ticks), `src/beamtime/views/model.py` (`Line` 40, `Scatter` 67, `Bar` 79, `Histogram` 91), `views/compile.py`, `views/prefs.py` (`settle` 68).
- **Read:** `docs/design/07-web-ui.md` § Charts; `docs/design/05-views.md` § Catalog (l. 168), § Charts (l. 381).
- **Done check:** `cd web && npm ci && npm test && npm run build`, then the Python checks; bundle committed; `uv run pytest -q tests/serve/test_browser.py tests/views`.
- **Prompt:** `Implement chunk B3 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, B3's manifest and chunk B3; read other files only as the manifest or the code leads you. Commit when B3's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### B4

- **Touches:** `web/src/ui/primitives.ts` (`Popover` 71), `web/src/blocks/line-settings.ts` (from B1), `web/src/ui/multiselect.ts`, `web/src/styles/blocks.css`, `web/src/bt/prefs.ts` (`ChartPrefs` 8, `effective` 83), `views/prefs.py` (`settle` 68), `design/components/Chart.md`.
- **Read:** `docs/design/07-web-ui.md` § Charts; `design/components/Chart.md`.
- **Done check:** `cd web && npm ci && npm test && npm run build`, then the Python checks; bundle committed; `uv run pytest -q tests/serve/test_browser.py`.
- **Prompt:** `Implement chunk B4 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, B4's manifest and chunk B4; read other files only as the manifest or the code leads you. Commit when B4's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### B5

- **Touches:** `src/beamtime/settings.py` (`DEFAULTS` 10–22, `SETTABLE` 23, unknown keys 91, `load` 162), `ops/registry.py` (`SetParams` 447), `ops/admin.py` (`set_setting` 95), `serve/api.py` (meta 209–238), `web/src/shell/settings.ts` (17, 80–81), `web/src/bt/writes.ts`, `views/theme.py` (`DEFAULT_COLORMAPS` 16, `colormaps` 40), `web/src/bt/theme.ts` (`groupColors` 75), `web/src/kit/protocol.ts` (`Init` 9), `web/src/bt/prefs.ts`, `views/model.py`, `views/prefs.py`, `line-settings.ts`; tests `tests/ops/test_ops.py`, `tests/views/test_theme.py`; docs `guide/parts/kit.md`, `guide/examples/code/phase-map.js`, `docs/guides/settings.md`, `design/README.md`, `design/components/Chart.md`.
- **Read:** `docs/design/05-views.md` § Theme (l. 400), § Colors for runs and groups (l. 443); `07-web-ui.md` § Theme in the UI (l. 229).
- **Done check:** `cd web && npm ci && npm test && npm run build`, then the Python checks; bundle committed; `grep -rn colormap_diverging src web/src` finds only the migration line.
- **Prompt:** `Implement chunk B5 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, B5's manifest and chunk B5; read other files only as the manifest or the code leads you. Commit when B5's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### B6

- **Touches:** `views/defaults.py` (new `CLOCKS`; `curves` 182, `ordered_metrics` 218), new `src/beamtime/query/progress.py`, `ops/reading.py` (`card` 193), `query/fields.py` (`run.epoch`), `web/src/shell/header.ts`, `web/src/blocks/table.ts`.
- **Read:** `docs/design/03-index.md` § Fields (l. 211); `07-web-ui.md` § Pages and URLs (l. 152).
- **Done check:** `cd web && npm ci && npm test && npm run build`, then the Python checks; bundle committed; `uv run pytest -q tests/query tests/views tests/serve/test_browser.py`.
- **Prompt:** `Implement chunk B6 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, B6's manifest and chunk B6; read other files only as the manifest or the code leads you. Commit when B6's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### B7

- **Touches:** `views/defaults.py` (`ESSENTIAL` 11, `group_body` 37, `curves` 182, `line` 208, `essential` 228 removed), `web/src/blocks/layout.ts` (`Section` 15, `Grid` 40), `web/src/bt/prefs.ts` (`ViewPrefs` 25), `views/prefs.py` (`apply_prefs` 10), `views/compile.py`, `web/src/bt/index.ts` (`ViewCtx`: `charted`), `guide/examples/*.yaml`.
- **Read:** `docs/design/07-web-ui.md` § Charts; `design/components/Section.md`.
- **Done check:** `cd web && npm ci && npm test && npm run build`, then the Python checks; bundle committed; `uv run pytest -q tests/views tests/serve/test_browser.py`.
- **Note:** + review.
- **Prompt:** `Implement chunk B7 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, B7's manifest and chunk B7; read other files only as the manifest or the code leads you. Commit when B7's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### E5

- **Touches:** `web/src/bt/uplot.ts` (`LineSpec.marks`), `web/src/ui/symbols.ts` (time limit), `web/src/shell/header.ts` (code versions fact), the run page's details (`web/src/shell/page.ts`, `drawer.ts`), `web/src/blocks/table.ts` (column picker); `design/components/` and `design/gallery.html` for new components.
- **Read:** `docs/design/07-web-ui.md` § Pages and URLs, § Charts; `docs/design/01-storage.md` on `attempts`, `copied_from`, `origin`.
- **Done check:** `cd web && npm ci && npm test && npm run build`, then the Python checks; bundle committed; `uv run pytest -q tests/serve/test_browser.py tests/test_design.py`.
- **Prompt:** `Implement chunk E5 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, E5's manifest and chunk E5; read other files only as the manifest or the code leads you. Commit when E5's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### C1

- **Touches:** `web/src/kit/index.ts` (`makeKit` 46, `version` 78, `ui` 88–100, `theme` 152–175), `web/src/kit/protocol.ts`, `web/src/blocks/custom.ts`, `web/src/bt/frame.ts` (B1), `web/src/ui/symbols.ts` (`symbolFor` 53), `web/src/ui/icons.ts` (`Sym` 36), `web/src/ui/primitives.ts` (`Tag` 24), `guide/parts/kit.md`.
- **Read:** `docs/design/05-views.md` § The `bt` kit API (l. 315), § Sandbox (l. 362), § Charts (l. 381).
- **Done check:** `cd web && npm ci && npm test && npm run build`, then the Python checks; bundle committed; `uv run pytest -q tests/views/test_custom.py tests/serve/test_browser.py`.
- **Note:** + review.
- **Prompt:** `Implement chunk C1 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, C1's manifest and chunk C1; read other files only as the manifest or the code leads you. Commit when C1's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### C2

- **Touches:** `views/model.py` (new `Scorecard`), `views/compile.py`, new `web/src/blocks/scorecard.ts`, `web/src/blocks/index.ts`, `guide/examples/sweep.yaml`.
- **Read:** `docs/design/05-views.md` § Catalog (l. 168).
- **Done check:** `cd web && npm ci && npm test && npm run build`, then the Python checks; bundle committed; `uv run pytest -q tests/views`.
- **Prompt:** `Implement chunk C2 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, C2's manifest and chunk C2; read other files only as the manifest or the code leads you. Commit when C2's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### C3

- **Touches:** `views/validate.py` (`structure` 87, `custom_checks` 169), `views/code.py` (`problems` 32), `tests/views/test_views.py`.
- **Read:** `docs/design/05-views.md` § Validation (l. 577).
- **Done check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`.
- **Note:** Run the lints on the real views only through a read-only `pull`.
- **Prompt:** `Implement chunk C3 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, C3's manifest and chunk C3; read other files only as the manifest or the code leads you. Commit when C3's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### G1

- **Touches:** `src/beamtime/guide/parts/` (new topic files), `src/beamtime/guide/__init__.py` (`guide` 35, `read` 57), `guide/examples/*.yaml`, new `tests/guide/`.
- **Read:** `docs/design/05-views.md` § The agent guide (l. 603), § Agent instructions (l. 710).
- **Done check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`.
- **Prompt:** `Implement chunk G1 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, G1's manifest and chunk G1; read other files only as the manifest or the code leads you. Commit when G1's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### G2

- **Touches:** `src/beamtime/mcp/server.py` (`prompts` 182), the `mcp install` op, new `scripts/build-plugin`.
- **Read:** `docs/design/08-cli-mcp.md` § Prompts (l. 163); Claude Code's current plugin docs before step 2.
- **Done check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`.
- **Prompt:** `Implement chunk G2 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, G2's manifest and chunk G2; read other files only as the manifest or the code leads you. Commit when G2's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### G3

- **Touches:** `git mv bench/views bench/agents`; `run.py`, `score.py`, `report.py`, `tasks/`, new `mine.py`, `README.md`, `MISTAKES.md`.
- **Read:** `bench/views/README.md`; G3's chunk.
- **Done check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`; one smoke task with one rep.
- **Note:** Ask before any harness run beyond the smoke test; they cost tokens. + review.
- **Prompt:** `Implement chunk G3 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, G3's manifest and chunk G3; read other files only as the manifest or the code leads you. Commit when G3's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### G4

- **Touches:** `ops/registry.py`, `ops/reading.py`, `ops/budget.py`, `query/distinguish.py` (for `compare`), `mcp/server.py` (JSON-string tolerance), `guide/parts/analysis.md`; one test per tool on `synth`.
- **Read:** `docs/design/08-cli-mcp.md` § Operations (l. 24), § Token budgets (l. 178).
- **Done check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` per tool; `docs/reference/cli.md` regenerated (its test checks it).
- **Note:** One commit per tool.
- **Prompt:** `Implement chunk G4 of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, G4's manifest and chunk G4; read other files only as the manifest or the code leads you. Commit when G4's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

### Z

- **Touches:** `CHANGELOG.md`, `docs/`, `CLAUDE.md`, `todo`, `scripts/build-tokens`, `design/favicon.svg`, `web/src/shell/favicon.ts`, `tests/test_design.py`.
- **Read:** Breaking changes, Decisions and Not verified in this plan.
- **Done check:** `cd web && npm ci && npm test && npm run build`, then the Python checks; bundle committed; `scripts/release.py` passes.
- **Note:** Don't publish, tag or push; hand over the publish command. The cluster pull, the upgrade and porting the remote's blocks are the user's; prepare the steps.
- **Prompt:** `Implement chunk Z of docs/refactor-1-plan.md on branch refactor-1, in the main checkout (no worktree). Read CLAUDE.md, the plan's Brief and How to execute, Z's manifest and chunk Z; read other files only as the manifest or the code leads you. Commit when Z's done check passes, then record the hash in the plan as How to execute says. Don't push. Questions at the end.`

---

## F. Foundation

### F1. Fixtures shaped like real experiments (sonnet) — **done `88fc5b5`**

The synthetic data uses `val/`, `train/`, flat configs and smooth metrics, which is why none of these bugs
showed up in tests.

- `src/beamtime/synth/generate.py`: add a generated group `realistic/egnn-bench`, keeping the existing
  groups byte-stable:
  - metrics `validation/w1_energy`, `validation/loss`, `training/loss`, `energy/B_w1`, `energy/C_w1`;
    `energy/Aconst_w1` constant 0 and alphabetically first (`A_w1` would sort before it); `lr-AdamW`; `sys/*`;
  - `epoch` logged every 50 steps as a step function, 100 steps per epoch;
  - `validation/first_eval` with exactly one point; `validation/signed` crossing zero;
  - nested config: `arm`, `seed`, `hparams.egnn.vector_channels` determined by `arm`,
    `hydrantic.model.egnn.vector_channels` as its alias, `hydrantic.seed` as an alias of `seed`,
    `hydrantic.trainer.max_epochs`, `hydrantic.trainer.default_root_dir` with a per-run timestamp;
  - a sweep group with 12 distinct `config.lr` values;
  - a dirty git record on some runs, `killed` runs with `scheduler` set.
- `tests/serve/conftest.py`: a `live_page` fixture: a project, a subprocess writing metrics through the SDK
  every 0.2 s, `serve` on a free port, and a Playwright page. Reuse `views/render.py:launch` to find the
  browser. Use `page.wait_for_timeout`, never `time.sleep`, which blocks Playwright's event dispatch.

Done: `tests/synth` pass, and old groups are byte-identical (assert it with a hash).

---

## A. Bugs

### A1. Custom blocks follow live data (sonnet) — reproduced — **done `e2a5cb6`**

Files: `web/src/blocks/custom.ts`, `web/src/api.ts`, `tests/serve/test_browser.py`.

1. Write the failing test first with `live_page`: a custom block on `bt.useData`, showing the last step.
   Assert that the step advances over 10 s, and that 20 s after the writer stops there is no
   `.custom-error`.
2. In `Custom`, change the bridge effect's deps from `[code.status, code.data, frame]` to
   `[code.status, code.data?.code, frame]`. New code already gets a new frame through `key`.
3. Move the first-render timer out of that effect's re-runs: it starts once per frame and only until the
   first `ready`.
4. Stop refetching code at all: `code/<sha8>-name.js` is content-addressed and immutable. Allow
   `Call.scope: string | null`, and skip `scope === null` in `watchChanged` and `invalidate`. Library blocks
   are pinned by version, so they are immutable too. Give the `code` call `scope: null`.

Done: the test passes, and a request log shows one `code` call per block per page load.
Also verify over `tests/remote/test_docker.py` when Docker is on: the user's real setup is remote, and only
the local path was reproduced.

### A2. Nested values and a config viewer (sonnet) — **done `dada516`**

Files: `web/src/bt/fmt.ts`, new `web/src/ui/config.ts`, `web/src/shell/drawer.ts`, `web/src/blocks/table.ts`,
new block `config` (`views/model.py`, `views/compile.py`, `web/src/blocks/index.ts`), `views/defaults.py`.

1. `fmt.value`: objects become `{3 keys}`, arrays `[1, 2, 3]`, or `[22 items]` beyond 5. Add
   `fmt.full(v)` (indented JSON) and use it for every `data-tip` currently built with `String(v)`.
   After this, `[object` must be impossible: add a test over nested values in every table column kind.
2. `ConfigTree({ config, varying, filter })`: nested and collapsible; chains with a single child collapse
   to `a.b.c`; a search field; an "only what varies" toggle; varying keys marked; long strings cut with a
   copy button.
3. Use it in the drawer, and as a new built-in `config` block: on the run page in a collapsed "Config"
   section, on group pages as "Hyperparameters" (the varying keys with their values, from `keys`). Add it
   to the kit as `bt.ui.Config`.
4. `table.ts`: long config columns show the shortest unique suffix (`beads.edge_frame`); the tip has the
   full key. Put it in `fmt.shortLabels(fields)`.

Done: the `realistic` fixture's config renders in all four places in a browser test, with no `[object`
in the page text.

### A3. Sparse data is visible (haiku) — code — **done `6899788`**

Files: `web/src/bt/uplot.ts`, `web/src/blocks/table.ts`, `web/test/`.

1. Series use `points: { show: true, filter }`, where `filter` returns the data indices to mark: every
   finite point when the curve has at most `SPARSE = 30` finite points, else none. Compute the count per
   curve in `lineChart`; read it through `current` so that a live update adds points to the same chart.
2. Pad the x scale when there is only one x value (`min === max`), since uPlot's auto range collapses.
3. `Spark`: one value draws the end dot, no line.
4. Check that band series never get markers.

Done: a browser test on `validation/first_eval` finds non-background pixels at the point. A unit test
covers 0, 1, 2 and 31 points.

### A4. Bands on log axes (sonnet) — code — **done `3942900`**

Files: `web/src/bt/curves.ts`, `web/src/bt/uplot.ts`, `web/test/curves.test.ts`.

Bands clip at the axis floor instead of leaving holes, as matplotlib's `nonpositive="clip"` does.

1. In `reshape`, drop `positive()` for `lo`/`hi`; only `y` goes null for non-positive values. New function
   `clipBands(curves)`: floor = smallest positive `y` over all curves ÷ `10^0.5`; `lo` below the floor
   becomes the floor; `lo`/`hi` go null exactly where `y` is null, so the polygon stays consistent.
2. Compute the auto range from the centre curves and the positive band values above the floor, and hand it
   to the scale explicitly. Band series can then no longer stretch the axis.
3. `hi` ≤ 0 with `y` > 0 can't occur with `minmax`; for `std` clamp to `y`.
4. `symlog` needs no clipping; test it too, since the real views use it most.

Done: unit tests for `std` with mean − std < 0, for `minmax` with a zero minimum, and for all-zero
curves. A browser test with `band: std`, `scale: log` on `validation/signed` shows a filled band to the
bottom of the plot.

### A5. Which config matters, which metric leads (sonnet + review) — real data — **done `0297ea2`**, `constant` revised in `474c488`

The header bug, the 22-column run tables, broken seed means and sweeps above 10 values share one cause:
no notion of *which config keys distinguish runs*.

1. New `src/beamtime/query/distinguish.py`, pure Python:
   ```python
   def distinguishing(per_run: list[dict[str, Any]]) -> Distinct: ...
   ```
   Given flattened configs:
   1. keep keys with more than one distinct value (any type, any count);
   2. drop string keys unique to every run when there are more than two runs **and the values look like paths or
      timestamps** (contain `/` or `\`, or start with a date such as `2026-10-20`). A categorical sweep with one run per
      value (`optimizer = adam, sgd, rmsprop`) stays;
   3. group keys by the partition of runs they induce; keep the shortest per group (fewest dots, then
      alphabetical), and record the others as aliases;
   4. drop key K when another kept key A determines K (A's partition refines K's) **and** A has fewer
      distinct values than runs. Without that last condition a unique random `lr` would swallow everything.
      **The seed key and its aliases never act as A:** with seeds disjoint per arm, the seed refines the arm, and
      dropping the arm would leave `varying = [config.seed]` and average the arms into one curve. Test it.

   Returns `varying` (e.g. `["config.arm", "config.seed"]`) and `aliases`.
2. `keys_kind`: add `config.varying` and `config.aliases`. `merge_keys`: union per source. The metrics
   table gets `constant` and `points` columns (`key, runs, last_step, constant, points`). `constant` means one
   value in every run (`and` across sources in the merge), except a single point in a single run, which is a
   result. "min = max in each run" was the first rule; it flagged one-shot metrics such as a final
   `test/acc` and kept them from ever leading. `points` is the most points one run has (max in the merge).
3. `views/defaults.py`:
   - `varying_config` reads `config.varying`;
   - new `main_metric(ctx, path, keys)`: the first metric in the group's proposal predictions (reuse
     `guide.proposed`), then eval prefixes, then training losses, then the first non-constant metric;
   - `EVAL_PREFIXES` gains `validation`; a training prefix tuple `("train", "training")`; constant
     metrics never lead, and single-point metrics (`points == 1`) come after those with a curve within
     their rank: a final eval still beats a training loss, but on `realistic/egnn-bench`
     `validation/loss` leads over `validation/first_eval`. The ranks in `ordered_metrics` follow.
4. `seed_groups`: group by `varying` minus the seed key and its aliases, instead of "config minus
   top-level seed". The answer's `by` shows those keys.
5. Header (`shell/header.ts:Best`, `defaults.summary`): remove the parenthesis.
   Show `best <b>Total energy W1 0.93</b> · <a>run name</a>`, using the view's metric label. The tip
   lists the distinguishing values. `summary.config` holds only `varying` without the seed, at most 3.
6. Chart settings' "mean by" (`line.ts:Settings`) uses `config.varying`.

Tests in `tests/query/test_distinguish.py` with the `realistic` fixture must give exactly
`[config.arm, config.seed]`; plus: a grid of lr and depth keeps both; a random search with unique lr keeps
all; 12 lr values count as varying; seed means over `realistic` give one curve per arm.

### A6. Refetch only what changed (sonnet + review) — reproduced — **done `c0aa283`**

Authored answers don't change when a metric line arrives.

1. Read `index/daemon.py` to see what `on_change` knows. Extend it to `changed: dict[path, set[kind]]`
   with kinds `metrics`, `status`, `authored` (notes, proposal, memory, view, blocks). Keep it simple: the
   daemon knows which file changed.
2. `serve/live.py`: `Hub.watch` takes `{id: [scope, kinds]}`, and `dispatch` filters by kind.
   `serve/stdio.py` and `start_sources` pass kinds along.
3. `api.ts`: a table from method to kinds: `view`, `notes`, `memory_show`, `proposal_show`: `authored`;
   `series`, `runs`, `keys`, `summary`: `metrics`, `status`; `groups`, `status`, `check`: all. An unknown
   method gets all, so nothing goes stale silently.

Done: with `live_page`, a metric tick refetches `series` and not `view`, `notes` or `memory_show`. A note
written by the CLI still appears within 3 s, also through the `transport` test source.

### A7. Notes: a `theory` label, editable in the UI (haiku) — **done `9c286ec`**

1. Move `TYPES` to `format/authored.py` as `NOTE_TYPES`, adding `"theory"`. `record/notes.py` imports it;
   `ops/registry.py` uses `Literal[NOTE_TYPES]`; `/meta` returns `note_types`.
2. `blocks/context.ts`: `NEW_TYPES` comes from meta minus `verdict`. `ui/symbols.ts`: theory gets a lucide
   icon (`atom`; add it to `ui/icons.ts`). A theory note is an explanation not yet measured: say so in the
   guide and in `design/components/Note.md`.
3. `NoteItem`: the type symbol becomes a small menu of the types minus `verdict` (as `NEW_TYPES`); choosing one calls
   `editNote(n, { type })`, which supersedes like any edit. On a verdict note the menu is disabled, with the tip
   "a verdict's type can't change; write a new note". Add `type` to `editNote`'s change.
4. `record/notes.py`: refuse to supersede across the `verdict` boundary, since verdicts carry per-prediction
   judgements: "a verdict's type can't change; write a new note".
5. Old readers are fine: an unknown type already falls back to a neutral symbol.

Done: tests for the new type over CLI, MCP and API; the browser test edits a label and sees a new version
with the same body and evidence.

### A8. Favicon and small visual touches (haiku) — **done `bd71c5b`**

Design change, so it lands through `design/`.

1. `design/favicon.svg`: a simple beam mark in the accent color, with a `prefers-color-scheme` block inside
   the SVG. `web/build.mjs` copies it to `static/`; `web/src/index.html` links it, replacing the empty
   `data:,` icon. `views/export.py` inlines it as a data URI, so exports have it too. Check that `/static`
   stays public in `serve/auth.py`.
2. New `shell/favicon.ts`: while runs are live in the current scope, the icon gets a status dot (a data URI
   is allowed by the CSP's `img-src data:`), and the title reads `(3) ala5-egnn-bench · Beamtime`.
3. `document.title` on every page. Group, run and timeline pages currently differ.

Done: `tests/test_design.py` covers the icon; a browser test asserts the link and the title with a running
run. Don't add further decoration without asking.

### A9. Bound what `view_render` returns (sonnet) — **done `4d03f19`**

Added after the first sessions started. Files: `views/render.py`, `mcp/server.py`, `tests/serve/test_render.py`,
`docs/design/05-views.md`, `docs/design/08-cli-mcp.md`, `guide/parts/overview.md`. No web change, so no bundle.

What costs what, from Claude's vision docs: an image costs `ceil(width / 28) x ceil(height / 28)` visual tokens, whatever
its format. Above a model's limit it is downscaled: on Claude 4.7 and later 2,576 px long edge and 4,784 tokens, on older
models 1,568 px and 1,568 tokens. So:

- **Height is what matters.** A 1280 x 6000 page is shrunk to about 550 px wide, where axis text is unreadable.
- **JPEG saves bytes and latency, not model tokens**, and the docs warn that heavy compression can make text hard to read.

Check first: in render mode, confirm that `document.documentElement.scrollHeight` exceeds the viewport on a long view. On
demo pages it stayed at 900 px in a quick try, unresolved. If the page really scrolls an inner container, `full_page` isn't
unbounded and the cause is a different one: stop and report it.

1. `screenshots()`: page and block shots use `type="jpeg", quality=75`, with the files named `.jpg`. Tune the quality against
   a real page: chart tick labels must stay readable at full size. A quick measure on short pages gave 18 to 33 % fewer bytes
   at 75, and almost nothing at 90. If a realistic page saves less than about 25 %, keep PNG and say so in the commit;
   the height cap is the part that matters.
2. Cap the page shot: `SHOT_HEIGHT = 2520` (90 patches, so 46 x 90 = 4,140 visual tokens at the default width of 1280, inside
   the newer limits). Use `page.screenshot(full_page=True, clip={...})` with `min(page height, SHOT_HEIGHT)`, and test the
   resulting dimensions, since combining the two wasn't tried on a tall page.
3. **Say what was cut.** The guide asks for a checklist answer on every block, so a silent cap would make agents judge
   blocks they never saw. When cut, the answer gets `cut: {page_height, shown_height, blocks_below: [ids]}`, from
   `[data-block-id]` positions, counting **every block whose bottom is below the cap**, including those lying entirely
   below it (on a 6200 px page with a 2520 px cap, the blocks at 3000 and 4500 px too). `lines` adds: "the page is 6200
   px; the shot shows the top 2520; below it: a, b, c; `view render <draft> --block <id>` shows one".
4. `mcp/server.py:content()`: the `mime_type` follows the file's suffix instead of the fixed `image/png`.
5. **Leave `render_page` as it is.** It isn't on the MCP path: its only caller is `bench/views/score.py`, whose judge answers the
   checklist from `page.png`. A cap would hide blocks from the judge and lower scores for the wrong reason.
6. Docs: `05-views.md` ("the CLI writes PNGs"), `08-cli-mcp.md` ("`view_render` returns images"), and in `overview.md`: use
   `view_validate` for checking, which already renders once and returns the same findings without an image; use `view_render`
   to look.

Not part of this chunk: query defaults (rows 50, points 100, entries 30), the output tail default (50) and the 8k-token answer
cap stay as they are.

Done: a tall draft gives an image of exactly 1280 x 2520 with `cut` naming the blocks below; `--block` on one of them returns
it; a short page has no `cut`; `content()` sends the right `mime_type`; `render_page` still writes a full-page PNG.

---

## B. Charts

### B1. Separate the chart's frame from its drawing (sonnet + review) — **done `0d11c23`**

No behaviour change; every later chunk depends on it. `blocks/line.ts` mixes data, head, settings, legend,
exports and uPlot; `blocks/plots.ts` repeats part of it.

Split into:

- `web/src/bt/frame.ts`: `ChartFrame({ id, title, notes, tools, downloads, legend, caption, expanded, children })`,
  plus the shared `Legend`.
- `web/src/blocks/line-settings.ts`: the settings panel, with fields declared per chart kind.
- `web/src/blocks/line.ts`: only the data and the spec.
- `web/src/blocks/plots.ts`: scatter, bar and histogram move onto `ChartFrame`.

Also, left over from A7 (review of A5–A9): give the note-type menu (`NoteType` in `blocks/context.ts`) a
place in `design/gallery.html`, per rule 6: the menu open, and a verdict's fixed symbol.

Done: all existing tests pass, and the design gallery is unchanged apart from that entry; `bench/web/timing.py` within budget; the shell
still under 120 KB.

### B2. A truthful x axis on the server (sonnet + review) — code

Files: `query/kinds.py`, `query/read.py`, `tests/query/test_series.py`, `docs/design/03-index.md`.

1. `read.x_values(cols, x, steps) -> list[float | None]`, replacing `map_x`:
   - `_t` and `_elapsed` as today (E1 later removes attempt gaps from `_elapsed`);
   - a metric: if non-decreasing, **interpolate linearly between its change points**, so `epoch` at step
     1750 of a 100-step epoch from 1700 is `17.5` rather than a stair; if it isn't monotone, the raw value
     at or before the step. **After the last change point**, extend with the slope of the last segment (the final
     epoch of a stair-logged run is not a stair either); with fewer than two change points, hold the value. Before
     the first logged point x is `None`. A constant metric is monotone (non-decreasing), with one x value;
     the monotone check runs on the resulting x values.
2. `run_curve`: drop points with `x is None` (today `align` gets `null` in its sorted x). Add
   `monotone: bool` to the curve.
3. `grouped_curve`: for `x != "_step"`, get `x_values` per run, drop `None`, and raise a `QueryError` for
   non-monotone x ("aggregating needs a monotone x; show each run instead"). Take lo and hi over the runs,
   `width = (hi - lo) / points`, bucket by `min(floor((x - lo) / width), points - 1)` (so `x == hi` falls in the
   last bucket), with `hi == lo` (single-point runs, a constant x) as one bucket and no division; mean per run per bucket, then the same
   mean and band code as now. `x` in the answer is the bucket centre. For `_step` the code path stays
   exactly as it is (power-of-two widths, no jitter).
4. Pure Python, `math.fsum` through `spread`, as `read.py` promises.

Tests: two runs with known times: `_elapsed` means equal hand-computed values and x stays in seconds; the
`epoch` axis gives fractions, also after the last change point; non-monotone x raises for groups and returns
`monotone: false` per run; a constant x and single-point runs give one bucket; `x == hi` gives `points` buckets, not one more.

### B3. Axis labels, x-axis choices, hover (sonnet)

Files: `web/src/bt/uplot.ts`, `web/src/bt/curves.ts`, `web/src/bt/plot.ts`, `web/src/blocks/line.ts`,
`web/src/blocks/plots.ts`, `views/model.py`, `views/compile.py`, `views/prefs.py`.

1. `LineSpec` and `PlotAxis` get `label: string`. uPlot axes get `label`, `labelFont` and `labelSize`, with
   the font from `ChartStyle` (never a CSS size). Default chart `HEIGHT` goes to 240 to keep the plot area.
2. `m.Line`, `m.Scatter`, `m.Bar` and `m.Histogram` get optional `xlabel` and `ylabel`. Defaults, in order:
   - **x**: `step`, `epoch`, `wall time`, `elapsed`, else the metric's label;
   - **y**: one metric: `label (unit)` from the view's `metrics` map; several: their shared prefix, or none.
3. y axis `size` as a function measuring the tick labels instead of the fixed 52, so `1.2e-05` isn't cut.
4. Line charts pick the renderer by the answer: all curves monotone → `lineChart`; otherwise a new
   `trajectoryChart` on `plotChart` (about 40 lines: polylines in step order, arrow at the end, tooltip
   with step, x, y), without bands.
5. Hover in `lineChart`: find each curve's nearest point by binary search on the curve's own `x`, instead
   of reading the aligned row. The tip's first row uses the x label, not "step".
6. `_t` ticks use the timeline's time ticks from `bt/shapes.ts` (dates when the range exceeds a day).
7. `exportPdf` passes the same labels.

Done: browser test: every chart kind on the `realistic` fixture has both axis labels, with labels in both
themes; hover over `_elapsed` lists all runs.

### B4. Chart settings panel (sonnet)

Files: `web/src/ui/primitives.ts`, `web/src/blocks/line-settings.ts`, `web/src/ui/multiselect.ts`,
`web/src/styles/blocks.css`, `web/src/bt/prefs.ts`, `design/components/Chart.md`.

1. **Beside the chart.** `Popover` gets `beside?: string` (a selector for the rectangle to avoid). Placement:
   to the right of `.chart-frame` if the panel fits, else to the left, else docked to the viewport's right
   edge. Top is clamped so the panel stays on screen; it re-places on scroll and resize. The chart stays
   visible, so a change can be seen as it happens.
2. **No horizontal scroll.** `.chart-settings` gets `overflow-inline: clip`. Fix the real overflow too:
   `.ms-chip { max-inline-size: 100%; overflow-wrap: anywhere }`, selects `inline-size: 100%`, `.pair` inputs
   `flex: 1 1 0; min-inline-size: 0`. Test: `scrollWidth <= clientWidth` with the longest real metric name.
3. **x axis for anything.** `ChartPrefs.x` becomes `string`. `MultiSelect` gets `single` and `groups`.
   First group "Progress": step, epoch (if a clock metric is logged), wall time, elapsed. Second group
   "Metrics": all other logged metrics, searchable. Also `views/prefs.py` and the `settle` defaults.
4. **Apply to all.** "Use this x axis on all charts on this page" writes to `prefs.view`, which
   `views/prefs.py` already folds but `effective()` ignores. Make `effective` merge
   base < node < `prefs.view` < `prefs.charts[id]`.
5. Below a chart with aggregated curves, a non-monotone x shows the server's error as a `Notice`, not an
   empty chart.

Done: browser tests for placement in the first and last grid column and at 600 px width.

### B5. Colormaps belong to the chart, and only there (sonnet)

Decided by the user: every colormap choice lives in a chart's settings, none in Beamtime's settings. Today
`colormap` and `colormap_diverging` are project settings, applied through one sampled ramp in the theme. No built-in
chart uses the diverging one; only the kit's `bt.theme.scale("diverging")` does. So two project settings become
**one `colormap` per chart**, picked from one list with both families.

Remove the settings:

1. `settings.py`: remove both keys from `DEFAULTS` and `SETTABLE`. `load` ignores them in existing files with one
   problem line: "colormap moved to the chart settings; this key no longer does anything". It is not an "unknown
   setting" error.
2. Remove them from `ops/registry.py` (`SetParams.key`), `ops/admin.py` (`set_setting`'s case), `serve/api.py`
   (`meta.settings`, and the `pair` arguments), `shell/settings.ts`, `bt/writes.ts`. Rewrite `tests/ops/test_ops.py`
   and `tests/views/test_theme.py` accordingly.
3. `views/theme.py`: `ramps` always uses `DEFAULT_COLORMAPS` (viridis, coolwarm), which stay built-in defaults and
   aren't configurable anywhere else.

Add the chart settings:

4. `meta.colormaps` returns the samples rather than only the names: `colormaps.json` is 3.7 KB, so it needs no API of
   its own. The custom-block frame gets them through `Init`.
5. `ChartPrefs.colormap?: string`, `ChartPrefs.color?: string`. `m.Line`, `m.Scatter`, `m.Bar`, `m.Histogram` get
   `colormap`; `views/prefs.py` folds it and `color`. In `line-settings.ts`, a "Colors" group:
   - **Color by**: none, or a field from `config.varying` (A5). `Line` has this in YAML but not in the panel. Compile
     or build the `colors` call when it is chosen in the panel.
   - **Colormap**: "Default", then sequential and diverging as groups, with a swatch per entry.
6. `groupColors(values, theme, stops | null)`. **A chosen colormap always applies**: to numeric groups by value, to
   categorical groups at evenly spaced positions. Unset, today's rule holds: theme palette for categories, viridis for
   more numeric values than the palette has. So the control is never a dead end.
7. Charts with one curve per run and no grouping keep their page-wide run colors, because the same run must match
   its swatch in the table and in other charts. There the Colormap row is disabled with the tip "each run keeps its
   color on this page; choose Color by or a grouping".
8. Same map in light and dark. Exports keep the chosen colors: `recolor` passes colors outside the palette through;
   test it.
9. "Apply to all charts on this page" (B4) covers `colormap` too. This replaces the project-wide default: the choice is
   kept per viewer through `prefs.view`, and "Save as view" writes it into each block.
10. Kit: `bt.theme.scale(kind, name?)`, defaulting to the built-in defaults. `Figure` (C1) offers `"colormap"` in
    `settings` and passes `prefs.colormap`. Update `kit.md`, `guide/examples/code/phase-map.js`, `docs/guides/settings.md`
    (remove both keys and `beamtime set colormap`), `design/README.md` ("Themes and colormaps"),
    `design/components/Chart.md`.

Done: `colormap` appears in no settings file, settings page or `beamtime set`; `grep -rn colormap_diverging src web/src`
finds only the migration line. Changing a chart's colormap changes only that chart, also for `config.arm` groups, and
survives "Save as view" and reload. An old `beamtime.yaml` with the keys loads with the one line.

### B6. Epochs are a clock (sonnet) — real data

1. `views/defaults.py`: `CLOCKS = ("epoch", "global_step", "trainer/global_step")`. These metrics get no
   chart in the default view.
2. `query/progress.py`, pure Python: `progress(cols, config) -> {epoch, in_epoch, steps_per_epoch, total, fraction}`
   from the epoch column's change points (exact), with `total` from a flat config key whose leaf is
   `max_epochs`, if any.
3. `card` adds `progress`. For tables, a cheap form from the card alone: `run.epoch` is `metric.epoch.last`
   plus 1 of `total`.
4. UI:
   - run header fact: `epoch 123 of 500 · 42 % through · about 2 h left` (ETA from `steps_per_s`);
   - a thin determinate bar in the run row of tables, for running runs only;
   - a `progress` column kind.
5. Charts keep `step` as default. `epoch` is the second option in the x picker (B4) and, with B2, gives a
   continuous axis.
6. Runs without an `epoch` metric show nothing new.

Done: the `realistic` fixture has no epoch chart, shows the right fraction, and `x: epoch` draws continuous
curves. Views that chart `epoch` explicitly still work.

### B7. One kind of chart, grouped by prefix (sonnet + review)

Files: `views/defaults.py`, `web/src/blocks/layout.ts`, `web/src/bt/prefs.ts`, `views/prefs.py`, `views/compile.py`.

Decision: **no "essential" section at all.** Each metric appears exactly once, in the section of its prefix.
So there are no two kinds of chart to tell apart.

1. `defaults.curves(metrics, seeds, own)`:
   - group by prefix; prefixes with one metric and unprefixed metrics go to "Other";
   - order: proposal metrics' prefix, eval prefixes, training prefixes, the rest alphabetically, Other, `sys`;
   - sections open: the first two; closed: the rest and `sys`;
   - with only one group, a plain grid without a section;
   - titles: `validation (5)`. Ids stay `line-<slug>`, so stored settings survive.
2. Remove `essential()` from chart building; `main_metric` (A5) replaces it for the header and table.
3. `layout.ts:Section` remembers open and closed per viewer, like `Collapsible` (`stored`/`store`).
4. Every chart gets the same × ("Hide this chart"), adding to `prefs.removed`. `Grid` filters them out; a
   section shows "2 hidden · show". Remove `node.props.added` from the tools. `views/prefs.py`: "Save as
   view" drops removed nodes.
5. "Add a chart" is offered when a metric has no chart anywhere on the page (authored views, removed
   charts). The list must look at the **whole page**, not the one grid; give `ViewCtx` a `charted` set, and
   move the control out of `Grid` to the end of the charts.
6. Section titles with shared prefixes are ordinary sections. Show them in the guide's examples, so agents
   copy the pattern.

Done: `realistic` shows `validation`, `training`, `energy`, `Other`, `System`; a hidden chart comes back;
"Save as view" keeps the choice; a browser test covers it.

---

## C. Agent chart parity

Why agents hand-roll d3 (real data): no axis labels, no epoch axis, no scorecard, no status pills. B3 and B6
remove the first two. C makes the built-in route the easy one, and gives real custom drawing the same frame.

### C1. Three tiers, one frame (sonnet + review)

The tiers, documented in this order in the guide:

1. **YAML blocks** (`line`, `scatter`, `scorecard`, ...): everything included.
2. **`bt.chart.Line`, `Scatter`, `Bar`, `Histogram`** in custom layouts: same props as YAML, same features,
   data from a declared query. Already works; make sure all of B applies.
3. **`bt.chart.Figure`**, new, for drawings no block can make:
   ```js
   html`<${bt.chart.Figure} id="phase" title="…" xlabel="…" ylabel="…"
     series=${[{ key: "run-id", label: "vec", color }]}
     settings=${["scale", "smooth", "colormap"]}
     csv=${rows}
     draw=${(el, { width, height, prefs, hovered }) => { /* d3, svg or canvas */ }} />`
   ```
   `ChartFrame` provides the head, settings panel, legend with hide and solo, hover both ways, downloads
   (SVG or PNG from `el`, CSV from `csv`) and persisted preferences. `draw` runs again on a change of data,
   prefs, hover or size.

Files: `web/src/kit/index.ts`, `web/src/kit/protocol.ts`, `web/src/blocks/custom.ts`. When a frame uses
`Figure`, it sends `{ type: "chrome", own: true }`, and `Custom` hides its own head so there aren't two.

Also export Beamtime's visual vocabulary, so that custom blocks reuse it instead of retyping it:

- `bt.ui.Sym({ kind, value, word? })`: the app's symbol for a value, through `ui/symbols.ts:symbolFor`, for every
  `Kind` there (run status, prediction result, verdict, note type, research status). Not a raw `SymbolSpec`, so
  a custom block can't pick its own icon and tone for a known value.
- `bt.ui.Icon` (lucide by name) and `bt.ui.Tag` (a pill with a tone).
- `bt.ui.Predictions`: the built-in `proposal` block's prediction rows with the live check.
- `bt.theme.tone(name)`: the colour of `good`, `bad`, `warn`, `muted` or `accent` in the current theme, so
  that a d3 drawing colours a pass or fail like the app does.

Bump `bt.version` to 2, additions only.

Done: browser test: a `Figure` with a d3 line gets settings, hover to a table row and back, a download, and
follows the theme and live data. Port `curves.js` from the remote as the test's content.

### C2. Built-in `scorecard` (sonnet)

The block agents wrote by hand on the real project: one row per value of a field, one column per metric,
mean ± std over seeds, shaded per column by direction.

- `m.Scorecard(rows: field, columns: list[metric field], baseline?: value, expected?: list)`, where
  `expected` keeps queued rows visible. Compiles to one `runs` query.
- `web/src/blocks/scorecard.ts`, computing with the `aggregate` semantics on the server if possible;
  hover and click like `table`; live.
- A `predictions` alias for the proposal block, showing the live check.

Done: reproduces the remote's `scorecard.js` from a 10-line YAML; the guide's `sweep` example uses it.

### C3. Validator lints (haiku)

`views/validate.py`, `views/code.py`. All warnings, each with its fix:

- a caption that starts with `x:` or is longer than 140 characters → "the axes say that now; say what the
  chart shows";
- custom code using `d3.line`, `createElementNS` or `<svg` without `bt.chart.` → "use `bt.chart.Figure` to
  keep hover, settings and downloads";
- custom code without `useData` or `subscribe` → "this block won't follow live data";
- a `custom` block with a typed-in result: no declared query, and the caption says "snapshot" → "use a
  query, or a `predictions` block";
- custom code with a colour literal (`#abc`, `#aabbcc`, `rgb(`, `hsl(`) → "use `bt.theme` (`tone`, `runColor`,
  `scale`) so colours follow the theme and mean what they mean elsewhere";
- custom code with status glyphs (`✓ ✔ ✗ ✘ ❌ ✅ ⚠`) or hand-written status words in a pill-like element →
  "use `bt.ui.Sym` with the matching kind";
- a top-level `section` or custom block whose title has more than two words → "titles of one or two words
  go in the left column; this one stays in the content, so shorten it and move the rest to a caption";
- a `text` block starting with a Markdown heading, or custom code with a titled `bt.ui.Section` or an
  `<h1>`–`<h3>` as its first element, at the top level → "make it a top-level `section` so the title goes in
  the left column".

Done: tests per lint; running validation on the real views' YAML flags `curves`, `predictions` and `price`.

---

## D. Sources

### D1. All sources are the same (sonnet + review) — **done `b7244e1`**

Rule: **a source is a named log dir. `local` is one when this machine has runs, otherwise it doesn't exist.**
No flag needed.

Backend:

1. `Context.has_local`: the log dir exists and (no remotes are configured, or it contains a run; stop at the
   first hit). `Context.default_source`: the only source when there is exactly one and no local. `has_local` is
   **not** decided once: `serve` runs the indexing loop whenever the log dir exists and re-checks `has_local` on each
   poll while there are remotes, so a first local run made after startup is indexed and listed without a restart.
2. `serve/server.py`: refuse only with no source at all, with a message naming `beamtime source add` and
   `beamtime serve host:/path`. Split `Daemon` into its lock and status file (which `via_serve` needs for the
   port) and its indexing loop; without local, only the first runs.
3. `remote/route.py`: `@local/...` is accepted and stripped. Paths without a prefix go to `default_source`.
   `federate` doesn't ask local without `has_local`. `target_of` and `page_of` raise a clear error instead
   of touching `Index` for a missing local.
4. Works from any directory: `Context.make` already falls back to the working directory, and `cache_dir`
   hashes a path. Check that nothing writes into the cwd. `beamtime mcp` needs no `--root`.
5. New user-only ops: `source add <name> <host:/path> [--command]` (writes user settings by default and
   probes over ssh for the command: `command -v beamtime`, then `<path>/../.venv/bin/beamtime`), `source list`,
   `source rm`. Keep the settings key `remotes:`; renaming it would churn without gain.
6. `api.meta`: `sources: [{name, kind, state, logdir}]`. `status` lists them all, in one format.

Frontend:

7. `app.py`: `/` redirects to the first source. `/f/local` redirects there too when there is no local.
8. `sidebar.ts`, `tree.ts`: every source is a root row with a symbol and collapse, local included. Remove the
   special-casing (`n.path.startsWith("@")`).
9. `shell/settings.ts`, "about": one row per source.

Tests: `tests/remote/test_no_local.py` with the test transport: serve, UI, CLI and MCP with only a remote,
from an empty directory; unprefixed paths route; `@local` works; nothing is created in the cwd.
Done when `cd /tmp && beamtime serve au002a.tphys.uni-heidelberg.de:/remote/gpu04/.../beamtime` works, and
`beamtime-serve/beamtime/` can be deleted.

### D2. Views and blocks on a remote (sonnet + review) — real data — **done `f9f1f40`**

Notes, proposals, memory and `name` already route. Views refuse because drafts are local.

Principle: **the draft stays with the agent, the check and the write happen on the source.** One bundle, sent
over the existing API, reuses all the validation, the library and `write_version` on the remote.

1. New API-only ops `view_check` and `view_put`, with `{group, yaml, files: {ref: base64}, author, message}`
   and a 16 MB limit stating what to do instead. They materialize the bundle in a temporary dir and call
   `validate.static` and `write_version`. `view_compile` does the same and returns what `shown` returns, for
   rendering.
2. `ops/views.py`: `new`, `validate`, `save_draft`: when the draft's group starts with `@`, build the bundle
   and route; otherwise run locally as today. `store.write_draft_meta` keeps the full `@x/group`. `new` fetches
   the current YAML and files through `view_show` and a small `view_files` op. `guide.example`'s
   `values_of` goes through `remote.answer`.
3. `render` runs locally: `serving(ctx)` gets sources (build `Sources` for the call), the URL uses the `@x`
   path, and `dispatch` answers `view` and `code` with a `draft` parameter locally (through `view_compile`),
   while queries route as usual. So a remote without Chromium isn't a problem.
4. `block promote`: same bundle. Remove `drafts=True` routing and the "run it there (ssh)" message from
   `route.py`.
5. `hello` carries the version; a remote too old for an op answers: "@au002a runs beamtime 0.1.1; this needs
   0.2: `uv pip install -U beamtime` there". Upgrading doesn't disturb running jobs.
6. `view_text`, `save_view` and `view_upgrade` already route. Test them too.

Tests: `tests/remote/test_views.py` with the test transport: the whole cycle `new`, edit, `validate`,
`render`, `save` with a custom block and a data file; the file lands on the remote under its hash; findings
come from the remote's index; a too-old remote gets the message. Same in `test_docker.py`.

### D3. Guide and instructions for remotes (haiku) — **done `3761001`**

- `parts/instructions.md`: drop the ssh hints; "a group on another source is `@name/group`; everything works
  the same".
- Check `mcp install` and `init --instructions` in a project without a local log dir.
- `docs/design/04-remotes.md` rewritten around D1 and D2, plus `docs/guides/` for remotes.

### D4. The proposal block through a remote (haiku) — reproduced — **done `18adc31`**

On `refactor-1-sources`, after the D review. Present since 0.1.1. Reproduce with:

```python
data = {"proposal": api("proposal_show", {"group": "exp/a"}, "exp/a"),
        "check": api("check", {"group": "exp/a"}, "exp/a")}
prefix({"blocks": [{"data": data}]}, "au")  # check gets @au/exp/a, proposal keeps exp/a
```

1. `prefix()` in `remote/route.py`: a block's call (a dict with `method` and `params`, as `views/compile.py:api`
   builds it) is always walked, also under a key in `USER_CONTENT`. `USER_CONTENT` stays as it is, so a
   proposal's text (`proposal_show`'s answer, a note's `proposal`) is still left alone. Don't rename the block's
   data key instead: saved pages and the frontend read `data.proposal`.
2. Tests in `tests/remote/test_route.py`: the case above gives `@au/exp/a` in both calls' `group` and `scope`; a
   `proposal_show` answer whose YAML holds `group: x` comes back unchanged. If `test_federation.py` can serve
   a page from a fake remote, add a page with a proposal block and assert both calls answer.

---

## E. Run lifecycle

E1 to E4 are on `refactor-1-lifecycle`, rebased on `refactor-1`, not merged: `d9130b0` E1, `6583a26` E2, `2ae9cf5` E3,
`a513e2b` review fixes, `5d7a83a` decided departures and the Lightning requeue, `c46417e` E4. **None of their UI
parts were built**; they are E5.

### E1. Resuming after a wall-time limit (sonnet + review) — **done `d9130b0`**

Files: `sdk/run.py`, `sdk/env.py`, `sdk/lightning.py`, `query/read.py`, `ops/`, `docs/design/02-sdk.md`.

`02-sdk.md` already notes that the job id alone isn't enough, since one job may train several models.
Resolution in `init`, wrapped so it can never break the experiment (on any error: new run, warning):

1. `resume=<id>`, or env `BEAMTIME_RESUME=<id>`: continue that run, as today.
2. `key="..."`, or env `BEAMTIME_RUN_KEY`: stored in `_run.json`. The newest run in this folder with this
   key: not finished → continue; finished → new run with a warning. For a job submitted again by hand. A run whose
   heartbeat is still fresh is never continued by key, since a run has one writer; a requeue of that run's own job
   may continue it.
3. Requeue, automatic: `SLURM_RESTART_COUNT > 0` and the job made **exactly one** run in this folder (any status;
   filtered by `name` when given), and that run is unfinished → continue. A job with several runs (models trained
   one after another) gets a new run and a warning naming `key=` or `name=`. Matching by config was rejected:
   timestamped `default_root_dir` values differ on a requeue (user's decision, in `02-sdk.md`). **Unfinished
   means `running` or `killed`** (not `finished` or `failed`): a run cut by its time limit is `killed`, and is
   hours old when the job restarts. Reuse `find_by_job_key`'s folder scan, but not its filter: today it accepts only
   `running` runs created within `RANK_RECENT_S` (`sdk/run.py`), which would never find the run on a requeue. The
   recency window stays for the rank-sharing path it exists for.
4. Otherwise a new run.

Starting over from step 0 stays safe: the index already drops the older attempt's points from the resume step
on.

Also:

- Time limits: in `chain_signal`, `SIGTERM` within 300 s of `SLURM_JOB_END_TIME` adds `reason: "time_limit"`
  to `exit` and to an event. Status stays `killed`. The UI shows "killed · time limit" (E5).
- New read-only op `beamtime resume <run>` (also over MCP). **It runs nothing**: it prints the recorded command
  and cwd, the last step, the newest checkpoint (through E2's resolver once it exists, else `_artifacts.jsonl`), the
  scheduler, and what to export
  (`BEAMTIME_RESUME=<id>`), so an agent can write the `sbatch` call.
- `_elapsed` counts active time: subtract the gaps between attempts. A gap is the next attempt's `started_at` minus
  the last `_t` of the previous attempt's metrics (the previous end is not stored; the `attempt_started` event's
  `metrics_offset` bounds each attempt's lines). A resumed run's curve shouldn't show a 6-hour queue wait.
- Charts mark attempt boundaries with a thin dashed line, from `attempts[].resume_step` (`LineSpec.marks`) (E5).
- Lightning installs its SLURM auto-requeue handler only where `SIGUSR1` has none (lightning 2.6.6,
  `signal_connector.py:62`), and `BeamtimeLogger` installed one first, so Lightning's requeue never worked with it.
  Fixed in `b92c8a7`: the logger leaves `SIGUSR1` to Lightning, so a Lightning requeue records no
  `requeue_requested` event.
- `BeamtimeLogger(key=...)`, passed on. `examples/` gets a SLURM script with
  `#SBATCH --requeue --signal=USR1@120` and Lightning's `ckpt_path="last"`.

Tests in `tests/sdk/` via the `script` fixture with a fake environment: requeue continues; two candidates give a
new run and a warning; key across job ids; finished key; a broken `_run.json` in the folder doesn't stop `init`;
SIGTERM near the end time records the reason. Lightning tests pass in the throwaway env. **Then a real check on
the cluster**, still pending per `pending-cluster-check`: an `sbatch --time=2` job with requeue.

### E2. `beamtime cp` (sonnet + review) — **done `6583a26`**

Additive, so agents may use it; CLI path `cp`, MCP `cp`, routed like other writes (E4). In
`ops/admin.py`, or better a new `ops/copy.py`.

`beamtime cp <run|group> <dest-group> [--name NAME] [--with-checkpoints] [--with-record]`

For a run:

1. Refuse a running run, like `mv`, and a destination inside a run or with a reserved name (reuse `inside`).
2. New run id: run ids stay unique everywhere, which federation relies on.
3. Copy to a temporary directory in the destination group with a reserved name, so discovery ignores it. All files
   except `checkpoints/` unless asked. Rewrite `_artifacts.jsonl` as in [Checkpoint references](#checkpoint-references).
4. Rewrite `_run.json`: new `id`; `copied_from: {id, path, at}`; `proposals`: the run's own `.` entry stays,
   old ancestors go, and the destination's ancestors get their **current** proposal version with hash, as a
   new run would; `created_at` and `attempts` stay, because the data is from then. Drop `key` and set `job_key` to
   null, so resuming the source's key or job never continues the copy beside it. Append a `copied` event.
5. Fsync, then `os.rename` into place, with `_run.json` written before the rename. A crash leaves only a
   temporary directory, which `gc` removes.
6. Never modifies the source. Never hardlinks: a resume or a checkpoint overwrite would change both copies.

#### Checkpoint references

Decided by the user: **a copied run references where its checkpoints are.** It must also hold after the source group
is moved. `_artifacts.jsonl` knows three cases today; the real runs use the first.

| Record in the source | In the copy, by default | With `--with-checkpoints` |
|---|---|---|
| `uri` outside the source run (`lightning_logs/…/x.ckpt`) | unchanged | file copied to `<copy>/checkpoints/`, `uri` rewritten |
| `uri` inside the source's `checkpoints/` (Lightning's default) | `uri` kept, plus `origin: {run: <source id>, path: "checkpoints/x.ckpt"}` | file copied, `uri` rewritten, no `origin` |
| `path` (`artifacts/x.ckpt`, a small copied file) | unchanged: `artifacts/` is copied with the run | same |
| A file in `checkpoints/` with no record | a new record, as in the second row | file copied, with a record |

The last row matters: `BeamtimeLogger` records only the best and last checkpoint, and a reference can't exist for a
file nobody listed. A record that already has `origin` (a copy of a copy) is kept as it is: it names the run holding
the file. New fields only; old files read as before. `read_artifacts` drops every field it doesn't name, so add `origin`,
`score` and `monitor` to `format/run.py:Artifact`; the first would be lost otherwise.

One resolver, `ops/copy.py:checkpoints(ctx, run_dir)`, answers `[{name, kind, score, location, exists, via}]`:
`path` → inside the run; `origin` → the source run found **by id** through the index, so it follows `mv`, falling back
to `uri`; else `uri`. It runs on the source that holds the run, so a remote path is checked on the remote.

Where it shows:

- `card` gets `checkpoints` and `copied_from`.
- (E5) The run page's details list them with location and a copy button, plus "copied from <run>" with a link. A missing file
  is marked, with the reason.
- `beamtime resume <copy>` (E1) uses the resolver. **Its answer warns** when the recorded command saves to the
  directory of a referenced checkpoint: "the recorded command saves checkpoints to <dir>, where the source's are; set
  another dirpath". Otherwise a resumed copy could overwrite the source's files, as real runs set an explicit `dirpath`.
- The `cp` answer names how many checkpoints are referenced, where, and their total size.

Removing a source: copies aren't blocked by it, but user-only `rm` and `gc --yes` list the runs referencing its
checkpoints (`json_extract(info, '$.copied_from.id')`), since `gc` deletes for good. Those copies stay readable; only
the checkpoint is gone, and `exists: false` says so.

For a group: the same per run, with new ids, into `<dest>/<name>`, keeping subfolders. `--with-record` also
copies `proposal/`, `notes/`, `view/`, `memory/` and `blocks/`, which still cite the original run ids; say so in
the answer. Report files, size and any skipped checkpoints.

Across sources: refused for now with a pointer to `pull`.

Tests: `tests/ops/test_copy.py`: the copy is found by discovery with a new id; curves are identical; the card is
the same; it counts for the destination's proposal and `check`, and no longer for the old group; source files are
byte-identical; a kill before the rename leaves nothing visible; `resume` on a copy continues the copy; a copy
over the test transport. For checkpoints, each row of the table above; a reference still resolves after `mv` of the
source's group; a copy of a copy resolves to the file's holder; a deleted source gives `exists: false`, and `rm` lists
the copy; `--with-checkpoints` leaves no reference to the source; `resume` warns about a shared `dirpath`.
`docs/design/01-storage.md` gets `copied_from` and `origin`.

### E3. Code versions made visible (sonnet) — **done `2ae9cf5`**

The SDK records almost everything. Close the gaps.

1. `sdk/env.py:git_info`: add `untracked` (up to 50 paths from `git status --porcelain`, timeout as usual),
   `dirty` true for those too, and `diff_sha` (first 8 hex of the diff's sha256 plus the untracked list). Today a
   new `.py` file leaves `dirty: false`.
2. `query/fields.py`: `run.branch`, `run.dirty` and `run.code`, where `run.code` is `f385eda+1a2b3c4d`: one
   comparable identity, the same for the same commit and the same changes.
3. (UI in E5) Group header fact when members differ: `3 code versions`; tip lists them with counts. `check` adds a
   note when a proposal's members ran on different code. `compare` (G4) shows it.
4. (E5) Run page: a "Code" row with commit, branch and dirty mark, a link when the remote is GitHub or GitLab (derive the
   https URL from the ssh one), and the diff in a collapsed viewer, read from `_env/git.diff`.
5. (column picker in E5) Run tables: `run.code` is offered as a column, and in the default table only when it differs in the group.

Tests: untracked file on a temporary repo; same diff gives the same id; a real-format `_run.json` without the new
fields reads as before.

### E4. Bring the lifecycle branch in (sonnet) — **done `c46417e`**

Before E5 and before the user merges `refactor-1-lifecycle`. In its worktree (`../purser-refactor-1-lifecycle`):

1. Rebase on `refactor-1` (no merge). Expect conflicts in `query/kinds.py:keys_kind` and
   `views/defaults.py:group_body` against A5 and its `constant` revision: keep both sides' columns and facts.
   Run all checks, the 3.10 SDK tests and the Lightning tests after the rebase.
2. Route `cp` as E2 says ("routed like other writes"); today it isn't: `remote/route.py:PATH_KEYS` doesn't
   name `cp`'s `source`/`dest`, and `cp` refuses any `@`. Route it when both name the same source
   (`cp @au/a @au/b`), refuse across sources with the pointer to `pull`. Add E2's missing test "a copy over the
   test transport" (`tests/remote/conftest.py:box_spec`).

One commit for 2. The user merges afterwards.

### E5. The run lifecycle in the UI (sonnet)

After B7, since the attempt lines go through the chart frame B1 splits. Everything E1 to E3 left out of `web/`; the
data is already in the answers:

1. **E1.** Charts mark attempt boundaries with a thin dashed line from `attempts[].resume_step` (`LineSpec.marks`).
   The status reads "killed · time limit" when `exit.reason` or the `killed` event's reason is `time_limit`
   (both are written).
2. **E2.** The run page's details list the card's `checkpoints` (location, a copy button, a missing file marked with
   the reason) and "copied from <run>" with a link (`card.run.copied_from`).
3. **E3.** The group header fact "N code versions", with a tip listing them by count (`keys.codes`, filled only when
   members differ). A "Code" row on the run page with commit, branch, dirty mark, a GitHub or GitLab link derived
   from the ssh remote, and `_env/git.diff` in a collapsed viewer. `run.code` offered in the table's column picker
   (the default table already adds it when codes differ).

Design rules apply: new components get rules in `design/components/` and a place in `gallery.html`.
`docs/design/07-web-ui.md` gets all three, since E1 to E3 didn't touch it. Done: a browser test on a fixture with a
resumed, a time-limited, a copied and a dirty run.

---

## G. Guides, harness, tools

### Answers to the questions in the findings

**A plugin for the guides?** Not as the source. Keep `src/beamtime/guide/` as the single source, for two reasons: it
ships with the package, so the guide always matches the version the remote runs, and Beamtime is for agents in
general. Generate thin adapters from it: the `AGENTS.md` block (exists), Claude Code skills, and a plugin as a mere
wrapper around those skills and the MCP config. Skills add what's missing today, loading by task instead of agents
having to call `guide` first.

**Testing guides.** Extend the existing harness (`bench/views/`) from views to the whole research record, with
ground truth from the generator's planted effects, A/B runs between guide versions and a mistake ledger. When agents
fail, **fix in this order: product, validator, error message, guide text.** Text is the weakest fix; the real data
shows it: agents wrote d3 charts despite the guide's "built-in first", because the built-in chart couldn't do what
they needed.

**Which tools?** See G4, ordered by what the real sessions show.

### G1. Guide by topic, with chart best practices (sonnet)

Runs after C3, so that it describes what exists.

`src/beamtime/guide/parts/`, reachable as `beamtime guide <topic>`, each under about 100 lines with an index in
`overview.md`:

- `charts.md`, new: label axes (defaults are usually right; set `xlabel`/`ylabel` with units when not); captions say
  what the chart shows in one sentence, **never restate the axes**; at most eight curves, else `by`, `color`,
  `seeds`; log scale only for positive values, symlog otherwise; prefix sections for many metrics; `x: epoch` for
  training curves; shared y limits in small multiples.
- `kit.md`, rewritten around the three tiers (C1), with `Figure` as a full example and a rule for when each tier
  applies; `useData` for anything live.
- **Reuse Beamtime's vocabulary**, a section in `kit.md` and one line in `checklist.md`: a symbol, colour or pill
  the app already has for a thing is used as is, so the same mark means the same thing on every page. A table
  from thing to kit name: run status, prediction result, verdict and note type → `bt.ui.Sym` with that kind;
  predictions with their check → the `predictions` block or `bt.ui.Predictions`; pass, fail, warning →
  `bt.theme.tone`; runs and groups → `bt.theme.runColor`, `groupColor`, `scale`. Never hex colours, emoji or
  glyphs for status, nor a typed-in result. The C3 lints point here.
- **Section titles go in the left column**, in `overview.md` (where views are introduced), `kit.md` and
  `checklist.md`. How it works (`shell/views.ts`, `bt/labels.ts:labelOf`): every top-level block of a view gets
  its own page Section, and a top-level `section` (or custom block) titled with **one or two words** shows that
  title in the margin. A longer title, a nested section, a Markdown `##` in a `text` block and `bt.ui.Section`
  inside custom code (an `<h3>` in the iframe) all stay in the content column. So the guide says: structure a
  view as top-level `section`s with one- or two-word titles (`validation`, `energy`, `phase space`) and put
  the blocks, custom ones included, inside them; split one big custom block into several, one per section;
  `bt.ui.Section` only for subheadings within one block; longer explanations go in the caption. All five
  example views in `guide/examples/` follow it, and B7's prefix sections show the pattern.
- `proposals.md`, `predictions.md` (`each`, `compare`, `reduce`, windows, thresholds; worked examples from real
  proposals, anonymised: "2.7x cost per step" style reasoning), `notes.md` (all types with when to use each,
  including `theory`), `verdicts.md` (per-prediction verdicts, stating what the check says and no more), `memory.md`,
  `remote.md`, `analysis.md` (which tool for which question; G4).
- `anti-patterns.md` grows with the ledger from G3.

Tests: `tests/guide` checks that every field, block and op the guide names exists, that example views validate,
and that every example view's top-level blocks get a margin label (C3's section lints give no warning).

### G2. Delivery (haiku)

1. `beamtime mcp install --skills` writes `.claude/skills/beamtime-{views,record,analysis}/SKILL.md`: a trigger
   description and "run `beamtime guide <topic>`", no copied content, so they can't go stale.
2. `scripts/build-plugin` generates a plugin directory from the same templates plus the MCP config. Generated and
   not committed; publish later, by hand.
3. MCP prompts (`mcp/server.py`) expose the same topics.

Before building 2, check with Claude Code's docs how plugins and `claude plugin eval` work today; they weren't
evaluated for this plan.

### G3. The agent harness (sonnet + review)

Move `bench/views/` to `bench/agents/`; the view tasks keep working.

1. **Task kinds**, each with ground truth from `synth`:
   - `proposal`: "I want to test whether X": falsifiable predictions, right metric, window, `each` or `compare`, a plan.
   - `verdict`: planted effects; per-prediction verdicts match the truth, no overclaiming, evidence cited.
   - `notes`: right types, including `theory`, supersede instead of duplicating.
   - `view`: as now, plus D2's remote variant over the test transport.
   - `analysis`: answer a question; right answer, tools used, no raw file reads.
   - `lifecycle`: resume a killed run, copy a baseline.
2. **Scores**, deterministic first: task correct; rounds to valid; tool errors; tokens and turns; violations (raw reads
   of `_*` files, editing the log dir, user-only commands); for views also hand-drawn charts, live-capable blocks,
   axis labels and caption length, from C3's lints. A model judge only for prose, as now.
3. **Comparison**: `report.py --base <stamp> --new <stamp>` gives per-task deltas with reps ≥ 3 on haiku and sonnet.
   Guide versions come from a `--guide <dir>` override, so that text can be tested without a release.
4. **The loop**, as `bench/agents/README.md`: run, classify each failure from its transcript (product, validator, error
   message, guide, task), fix in that order, add it to `MISTAKES.md` with its fix, rerun. A held-out third of the tasks
   isn't looked at during refinement, against overfitting the guide to the tasks.
5. **Seed from reality**: `bench/agents/mine.py` (tool counts, errors, raw-file reads over `~/.claude/projects`
   transcripts; the scripts behind this plan's numbers). First tasks from the real errors: unknown fields such as
   `run.started`, a remote view, a group path that doesn't exist, `by` in `runs`.
6. Keep the smoke set small; state what a full matrix costs in runs before starting one.

Done: a baseline run of all kinds is in `RESULTS.md`, and at least one refine cycle shows a measured improvement.

### G4. Agent tools (sonnet, one commit per tool)

All through `ops/registry.py`, so CLI and MCP come together. Answers respect `ops/budget.py`. Ordered by evidence.

| Tool | Answers | Why (real sessions) |
|---|---|---|
| `compare <a> <b> …` | Config differences (via `distinguishing`), code identity, metric table with the differences, status. Runs or groups. | "What differs?" is the first question, now answered by parsing `_config.json` |
| `digest <group>` | One compact page: status counts, best per `varying` value, predictions with check, failures by signature, newest notes, what's missing from the plan | Agents chain `status`, `runs`, `check`, `notes` (54 + 19 + 18 calls) |
| `logs <run or group> [--grep RE] [--tail N]` | Output across runs, with context; the failed runs' last traceback grouped by signature | 90 `tail`, 36 `grep` over `beamtime/` |
| `wait <scope> --until finished\|<condition> --timeout S` | Blocks until true, then answers what changed. Capped for MCP. | Sleep loops; 54 `squeue`/`sacct` |
| `diagnose <scope>` | Flags per run: nonfinite, diverging (`slope_last10pct`), stalled (no new step while running), restarts, stopped early, missing metric. | Agents check by hand |
| `plan missing <group>` | The plan's grid points without a run, with their config, for launching | Typed in by hand in view code (`queued` rows) |
| `runs --by FIELD` | Aggregated tables like `series --by` | Tried and refused: "unknown field `by`" |
| `series/runs --to FILE` | Writes CSV or JSON under `.beamtime/exports/` and answers the path, so big answers skip the token budget | 49 Python one-liners over run files |

Small ones:

- MCP input tolerance: a value arriving as a JSON-encoded string (`"\"all\""`) is decoded once. Seen once in
  `series.points`.
- Field errors list close matches for run fields as they already do for metrics (`run.started` → `run.created_at`).
- `no group 'cln'` lists the top-level groups.

Each tool gets its entry in `guide/parts/analysis.md`, a test on `synth`, and a harness task (G3).

---

## Z. Close

- `CHANGELOG.md` for 0.2.0 with the breaking changes below; `docs/design/*`, `docs/reference/cli.md` (generated),
  `docs/guides/`; `CLAUDE.md`'s "Project specifics".
- Update `todo`: mark the findings done, with one line each.
- `scripts/release.py`, then upgrade on the cluster. **Check the real data first**: all 12 groups and the 10 custom
  blocks render on 0.2.0 from a read-only `pull`.
- Port the remote's `curves.js`, `scorecard.js` and `predictions.js` to built-ins as new view versions, after asking.
- CHANGELOG: Lightning's SLURM auto-requeue never worked alongside `BeamtimeLogger` before 0.2.0 (E1); Lightning
  requeues now record no `requeue_requested` event.
- Generate the favicon's colours (from the A5–A9 review): `scripts/build-tokens` writes the two accent fills of
  `design/favicon.svg` (light and dark) from `design/tokens.json`; today they are hand-copied (`#2f5aa8`,
  `#86a8e8`) and `tests/test_design.py` only checks that they match `tokens.css`. Drop the hardcoded
  `"#2f5aa8"` fallback for the live dot in `web/src/shell/favicon.ts`. A design change, so it lands through
  `design/`.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| `series` with `by`/`seeds` and `x ≠ _step` | steps | real x values, bucket centres | none; the old answer was wrong |
| `seeds` grouping | config minus top-level seed | distinguishing keys minus seed | curves may merge correctly |
| Default view layout | essential grid + "More metrics" | sections by prefix | none; saved views untouched |
| `init()` on a SLURM requeue | new run | continues the job's only run in that folder | give runs that must stay separate their own `key` or `name` |
| Chart `added` pref | `added` only | plus `removed` | old prefs still read |
| `colormap`, `colormap_diverging` settings, `beamtime set colormap` | project-wide | removed; one `colormap` per chart | old keys are ignored with one line; set it per chart or apply to the page |
| `/` with no local | error | first source | none |
| Remote view ops | refused | work; remote needs ≥ 0.2 for them | upgrade the remote |
| `git.dirty` | tracked changes only | also untracked | old files read as before |
| `view render` output | full-page `.png` | `.jpg`, page shots capped at 2520 px with `cut` naming what's below | read `shots[].file` rather than assuming a name |

Not breaking: everything on disk. Old runs, notes, views and proposals keep reading.

## Decisions taken; say if you want otherwise

Executors follow these unless told otherwise.

1. **Resume on requeue is automatic** when the job made exactly one run in the folder (by `name` when given) and it is
   running or killed; a job with several runs starts a new run with a warning (your decision; E1). Config matching
   was rejected: timestamped `default_root_dir` values differ on a requeue.
2. **A copy joins the destination's proposal** and leaves the old group's, since reuse in another group is its purpose.
   Checkpoints stay where they are by default, because they're large, and the copy references them (your decision; E2).
3. **No "key metrics" section**: every metric once, by prefix, with the first two sections open. If you'd rather have a
   pinned row of 4 on top, B7 gets one extra step.
4. **`_elapsed` excludes queue gaps** between attempts.
5. **All colormap choices are in the chart settings, none in Beamtime's** (your decision; B5). Without a choice,
   categorical groups use the theme palette and numeric ones viridis; a chosen colormap applies to both. Open to
   change: charts with one curve per run keep their page-wide run colors, so a run matches its table swatch; there the
   row asks for Color by or a grouping first.
6. **The settings key stays `remotes:`** rather than becoming `sources:`.
7. **A copy drops `key` and has no `job_key`** (your decision; E2), so resuming the source never continues the copy.
   **Resuming by key never continues a run with a fresh heartbeat** (one writer per run); a requeue of that run's own job
   may. `init` reads `BEAMTIME_RESUME` too.
8. **`view_render` gets no `shots` option** (A9). `view_validate` already renders once without an image and returns the findings
   plus the static checks, so the option would be a second, weaker way to do the same. If you want it anyway, it is 5 lines in
   `ops/views.py:render` and `ViewRenderParams`.

## Not verified

- Finding 1 was reproduced on a local log dir, not through ssh; A1's Docker step covers that.
- Findings 2, 4, 5, 6, 12 come from reading the code, so their chunks start with a failing test.
- A9's height cap wasn't measured on a tall page, and the share of `view_render` is by characters of output, not model tokens.
- `price.js` on the remote wasn't read in full. C2 may not cover it; C1's `Figure` does.
- `claude plugin eval` and the current plugin format weren't checked (G2).
- Real SLURM behaviour of `SLURM_RESTART_COUNT`, and whether `SLURM_JOB_END_TIME` is set at all, on your cluster: the
  `sbatch` check with `examples/slurm_toy.sh` and `examples/slurm_lightning.sh` (steps in `examples/README.md`) is still
  yours to run.
