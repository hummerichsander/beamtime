# v0.3 UI: charts that tell the truth early, a steady sidebar, the `///` mark

Base commit `fb352bd`, branch `setup`. Proposed 2026-11-15, based on the v0.3 UI list in `todo`, the audit
`docs/plans/v0.3/auto-detection-audit.md` (items 2, 3, 4, 6, 7, 8), the coordinator's settled decisions of
2026-11-15 (the logo mockup included), the code at the base commit and three reproductions on a scratch log dir.
No interview was possible (background run): defaults the plan had to choose are marked **assumed** under
Decisions. Behaviour changes are allowed; they are listed in [Breaking changes](#breaking-changes).

Run a ticket with `/run-ticket docs/plans/v0.3/ui/ui-plan.md <ID>` in a fresh session; review tickets marked
`+ review` with `/review-ticket docs/plans/v0.3/ui/ui-plan.md <ID>` on a stronger model.
`ticket.py status docs/plans/v0.3/ui/ui-plan.md` shows what's done and what's next.

## Goal

The outcome this plan commits to, checked against at the end and in every review:

- **Done means:** a metric a running run has just logged charts at once, and a chart whose runs are running
  but haven't logged a value yet says "Waiting for the first value" instead of an error. The sidebar
  (un)collapses on every chevron click and on a click on the current group's name. Markers follow one
  rule per chart, with a Markers auto/on/off setting. Hiding a run shrinks the x axis to the shown curves.
  Color by offers run fields, preselects the swept key, and lists alias and dropped config keys with the
  reason. Sections accept `val/`, `val.` and `val_`, and a prefix of one metric keeps its section. Log
  scale comes from the values, clocks from the leaf name, seed merging from the arms. The top bar and the
  favicon carry the `///` mark with its "gather left" motion. `beamtime guide type` tells agents exactly
  which type class to use for each kind of text in custom blocks and views, and `view_validate` rejects
  font literals (`font-size`, `font-family`, the `font` shorthand, `line-height`) in custom code. Logged
  images can be stepped through every logging, by step or by a clock such as epoch, and open in a large
  dialog that zooms, pans and downloads the original file. Every screen, the agent guide and the spec follow the modern design
  system (decisions 17 and 18): section labels above the content, sans titles, panels and hover rows, drawn
  controls, and serif only for what people and agents wrote.
- **Confirmed by:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`;
  `cd web && npm ci && npm test && npm run build` with the bundle committed; the tests named in each
  ticket (failing first where the evidence is **code**); `uv run pytest -q tests/serve/test_browser.py`
  where Chromium exists; by hand: `beamtime serve` on a scratch log dir with a running toy run
  (`examples/train_toy.py --sleep 1`) shows the waiting state, live charts, sections and the mark.
- **Out of scope:** the record-and-tools part of the audit (items 1, 5, 9, 10: direction by tokens, one
  seed rule, failure signatures, lost-run age); the `– steps` header of a running run (seen while
  reproducing, not asked for); markers and x range of trajectory charts (`trajectoryChart`); the scatter
  and bar charts; a mark animation outside the top bar and favicon.

## Findings

Evidence: **reproduced** (run), **code** (read, not run; the ticket starts with a failing test). Paths in the
table are short: `blocks/`, `bt/`, `shell/`, `styles/` sit under `web/src/`, `query/`, `views/` under `src/beamtime/`.

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | A chart of a new metric errors while the run is running: `'metric.val/loss.count': no run in 'exp' has metric key 'val/loss'` (once any run in scope has a card that lists other metrics; the card is rewritten every 180 s) | `series_kind` (`query/kinds.py` 217) selects `metric.<y>.count`, and `select_runs` → `check_known` (`query/select.py` 117–140) only looks at cards; `keys` already merges running runs' column keys (`with_live_keys`, kinds.py 174), so the view draws a chart the series call refuses | reproduced (`beamtime series exp --y val/loss`, a finished run with `train/loss` plus a running one) | Q31 |
| 2 | No "waiting" state: a chart with no curve says "No run in scope logs …" (`blocks/line.ts` 222) even while its runs run | `empty` (line.ts 147) knows nothing of running runs; the series answer carries no such fact | code | W35 |
| 3 | Sidebar entries don't collapse | ancestors of the current group are forced open on every render (`withAncestors`, `shell/sidebar.ts` 25, 125–131) while the chevron shows `open` only (26, 83): the chevron says closed, children show, clicks flip a set nobody sees; the twisty is a 16×14 px target (`styles/shell.css` 57), the rest of the row navigates (sidebar.ts 96–100); a filter forces every item open (83) | code | W31 |
| 4 | Markers come and go | `markers()` (`bt/curves.ts` 142–149) decides per curve on the aligned, downsampled data (`bt/uplot.ts` 77): a curve with ≤ 30 points is marked, its neighbour with 31 isn't, and a curve loses its markers at its 31st point | reproduced (12-point curve marked) / code | W33 |
| 5 | x limits don't shrink when a run is hidden | the x scale's range (`bt/uplot.ts` 105) gets `min`/`max` of `data[0]`, the union of every curve's x (`align`, curves.ts 97), hidden ones included; `applyHidden` (203) only toggles `show` | code | W32 |
| 6 | Color by shows only "none" | it lists `keys.config.varying` minus `config.seed` (`blocks/line-settings.ts` 97–102, 186): nothing for a seed-only group or a run page, aliases and determined keys vanish silently (`query/distinguish.py` 36–53) | code | W34, D33 |
| 7 | `val/loss` and `train/loss` land in "other (2)" | a prefix with one metric goes to Other (`views/defaults.py` 234–237); only `/` separates (`prefix` 316–322, `ordered_metrics` 285–293) | reproduced | D31 |
| 8 | Losses are log by name | `compile.py` 303: `"log" if lower_is_better(y) and "loss" in y`; non-positive values become gaps (`reshape`, curves.ts 33) | code | D34 |
| 9 | `train/epoch`, `step`, `iter` get charts | `CLOCKS` (defaults.py 23) is three exact names | code | D32 |
| 10 | Seeds merge only above 8 runs | `many = … and direct > SEED_GROUPING_ABOVE` (defaults.py 14, 87) | code | D33 |
| 11 | Favicon shows a dot when live; the top bar has no mark | `shell/favicon.ts` 16–52, `shell/bars.ts` 28; `design/favicon.svg` is three rotated rects | code | L31, L32 |
| 12 | Agents hard-code fonts in custom blocks: 10 `font-size="12"` on SVG text in 2 of 8 custom-code files of the bench runs (`bench/agents/runs/20261031-144758/sweep-heatmap-*`) | no guide part says which type class fits which text (the guide names no class at all); `views/code.py` checks color literals only (`COLOR` 39, `problems` 41–76), though `05-views.md` 790 marks "colors, fonts or sizes in custom code" as detected | real data / code | T31 |
| 14 | The design system moved on (2026-11-18): cool neutrals, Section labels above the content, `heading` in the sans, panels and rounded hover rows, `radius` 12px, drawn native controls, and a strict font rule (serif only for written text, sans for the interface, mono as its accent); `design/` and the shell's main screens follow it, but the agent guide, the spec documents and some tests still describe the margin column, and the other screens were never looked at | the change landed in `design/` with a working pass over `web/` (labels in collapse toggles, note rows, controls); `guide/parts/kit.md` 113–120, `views.md` 60–63 and `checklist.md` 13 teach "the left column"; `docs/design/05-views.md` 508, 675, 712, 989 and `07-web-ui.md` 45–47, 558 describe the notebook look; `tests/guide/test_guide.py` 135–139 asserts "left column" | code | S31, T31 |
| 13 | Logged images show only the latest step: 144 px thumbnails, no way to see earlier loggings, no zoom, no download, no expand | the default view asks `data` with `step: "last"` (`views/defaults.py` 141–142, `m.Images.step` `views/model.py` 164–168, compiled at `compile.py` 214–216); the `data` answer doesn't say which steps exist (`query/kinds.py` `data_kind` 476–528); `Images` (`blocks/logged.ts` 13–29) is a bare `Panel` with fixed `<img>` tiles (`styles/blocks.css` 96–99), not a `ChartFrame` (`bt/frame.ts` 66–110), so it gets none of the chart tools; `05-views.md` 206 already lists a `slider` as wave 2 | code | Q32, W37 |

## Brief

What the tickets build together, so a session doesn't rediscover the design:

- **Live keys in queries** (Q31): `src/beamtime/query/select.py` gains `live_metric_keys(ctx) -> set[str]` (column keys of
  running runs in scope); `check_known` and `known_keys("metrics")` accept them. The series answer's meta
  gains `running` (matched runs whose derived status is `running`), summed across sources in
  `ops/answers.py:merged`.
- **Default view rules** (D31–D33, `src/beamtime/views/defaults.py`): `prefix(metric)` knows `/` always and `.` or `_` after
  a known prefix (`EVAL_PREFIXES`, `TRAIN_PREFIXES`); `is_clock(metric)` matches the leaf against
  `CLOCK_LEAVES`; `merges_seeds(ctx, path, varying) -> bool` replaces the 8-run threshold; a sweep's one
  swept key becomes the charts' `color`.
- **Scale** (D34): compile emits `scale` only when the view or the block says so; the chart resolves a missing
  scale with `curves.autoScale(answer)`: log when every finite value is positive and max/min > 100, else
  linear.
- **Chart settings** (W33, D32): `m.Line.markers: Literal["auto", "on", "off"] = "auto"`; `src/beamtime/views/settings.py`
  derives settings from `m.Line`, and `scripts/build-chart-defaults` regenerates `web/src/bt/chart-defaults.ts`
  (also `CLOCK_LEAVES` after D32). `web/test/fixtures/chart-settings.json` is shared by
  `tests/views/test_settings.py` and `web/test/chart-settings.test.ts`; edit it by hand.
- **One decision per chart** (W32, W33): `LineSpec` carries `markers: boolean`; the x range is the extent of
  the shown curves (`curves.xExtent`), read through `current` like the y range.
- **The mark** (L31, L32): `///` as three round-capped strokes in a 24 viewBox, rest paths `M2.5 19.5 L9.5 4.5`,
  `M8.5 19.5 L15.5 4.5`, `M14.5 19.5 L21.5 4.5`, stroke 2.6, `accent`; "gather left" moves the middle −2 and
  the right −4 in x over 420 ms. The component is `Mark` (`design/components/Mark.md`, `.mark` in
  `design/components.css`, `web/src/ui/mark.ts`).
- **Images through their steps** (Q32, W37): the `data` answer's meta gains `steps` (every step at which a run in
  scope logged the key, ascending) and, with `clock: <metric>`, `clocks` (that metric's value at each of those
  steps, through `read.x_values`); entries stay those of the asked step, so a page loads one step's files at a time.
  The `images` block becomes a `ChartFrame` with a step scrubber under the images, the chart tools (download,
  expand) and, in the expanded dialog, zoom and pan.
- **The modern design system** (S31): `design/` is the spec and already changed (`design/README.md` § Look,
  § Differences from the export); the app's main screens follow it. S31 brings the rest along: the guide's section
  titles become "the section label" (mono, above the block, or in its collapse toggle), the spec documents lose
  the margin column and the warm notebook look, and every remaining screen is checked in both themes.
- **Type for agents** (T31): a guide topic `type` (`src/beamtime/guide/parts/type.md`) maps each kind of text in
  custom code and in views to a type class; `views/code.py` gains `FONT`, checked in `problems` like `COLOR`.

Done, for every ticket: its Done line holds; its Check passes; the spec documents say what the code does; its heading
is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` (4 xdist workers; `-n0`
   serially); a subset with `uv run pytest -q -n0 <files> -k <names>`. Web: `cd web && npm test` while working,
   then `cd web && npm ci && npm test && npm run build`. Browser tests: `uv run pytest -q tests/serve/test_browser.py`
   (skipped without Chromium; say so in the commit when skipped). The full suite runs in CI.
2. Generated files: any change in `web/` or `design/` rebuilds `src/beamtime/serve/static/` (commit it; the shell
   stays under 120 KB compressed); a change to `m.Line` runs `uv run python scripts/build-chart-defaults`; a
   change to `design/tokens.json` or `design/favicon.svg` runs `scripts/build-tokens`. Every ticket that
   touches `web/` or `design/` therefore runs alone, in the Order below.
3. Rules: CLAUDE.md's Python style; the CLI path stays light (`tests/test_budgets.py`); `design/` rules in
   `design/README.md` (sizes only from type classes, values only from tokens, `scripts/check-design`). Never
   touch `docs/plans/setup/`, `docs/design/10-setup.md`, `src/beamtime/guide/rules/` (the rules template and
   its release history) or `tests/golden/`.
4. Spec: `docs/design/03-index.md`, `05-views.md`, `07-web-ui.md` and `design/` are the spec; each ticket writes
   its change there in the same commit. Another session may hold uncommitted edits under `docs/design/`:
   commit only your own hunks (`git add -p`).
5. Ticket budget: 140k tokens per ticket session (default, **assumed**); split a ticket that would exceed it.
6. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading. The hash stays in git (`ticket.py status`).

## Order

```
Q31 ─ Q32 ─ D31 ─ D33 ─ T31             Python (Q31, Q32 share kinds.py and answers.py; D31, D33 share defaults.py;
                                        T31 edits guide parts and 05-views.md)
W35 after Q31, W37 after Q32 and D32; then one at a time (shared bundle):
S31 ─ W31 ─ W32 ─ W33 ─ W34 ─ W35 ─ W36 ─ D32 ─ W37 ─ D34 ─ L31 ─ L32 ─ Z31
```

S31 runs before T31: T31's `type` part describes the type and labels S31 makes true.

What's left runs in this order: Q31 Q32 D31 D33 S31 T31 W31 W32 W33 W34 W35 W36 D32 W37 D34 L31 L32 Z31

## Decisions taken; say if you want otherwise

1. **Waiting state** (decided): while a chart has no point and a run in its scope is running, it shows an info
   `Notice` "Waiting for the first value of `<title>`." Root cause first: the error is the series refusing a
   live key (Q31). Rejected: hiding such charts, because the chart would jump in later.
2. **The series meta says `running`** (assumed): the chart learns that its runs run from its own answer, not a
   second call. Rejected: a `runs` call per chart.
3. **Sidebar** (decided, details assumed): ancestors of the current group open once on navigation (added to the
   stored open set) instead of on every render; the twisty is a 24 px wide, full-row-height target; a click on
   the name of the current, expandable group toggles it. While the filter has text, every match shows
   expanded and the chevrons are inert (`aria-disabled`). Rejected: making the whole row toggle, because
   navigation is the row's main job.
4. **Markers** (decided; rule assumed): `auto` marks every point of every curve when the shown curve with
   the most finite points has at most 30 (`SPARSE`); `on` always, `off` never. A curve with exactly one
   finite point is marked in every mode, since it is otherwise invisible. The count is taken on the answer
   as drawn (after downsampling, before smoothing). Rejected: per-curve decisions (today's flicker).
5. **x range** (decided): the extent of the shown curves' x, padded only when it is a single value; a zoom
   still wins. Rejected: recomputing data without hidden curves, because it would rebuild colors and indices.
6. **Color by** (decided; grouping assumed): options in groups "Config" (varying keys, the seed included),
   "Run" (`run.status`, `run.tags`, `run.name`, `run.group` labelled status, tags, name, folder) and
   "Same split" (aliases as "`<key>` · same split as `<canon>`", keys `distinguish.py` dropped as
   "`<key>` · set by `<finer key>`"); all selectable. The `keys` answer gains `config.dropped` (key → the
   key that determines it).
7. **Swept key preselected** (assumed): in a group's default view, when seeds are not merged and exactly one
   varying config key other than the seed exists, every metric chart gets `color: <that key>`.
8. **Sections** (decided): `/` always separates; `.` and `_` separate after a known prefix (`val`, `valid`,
   `eval`, `test`, `validation`, `train`, `training`; matched case-insensitively, the longest first); a
   prefix with one metric keeps its own section; the guide recommends `/`.
9. **Log scale from the data** (decided; where assumed): resolved in the chart from the answer, so a live
   loss that crosses two decades turns log; an explicit `scale` (block, view `metrics`, viewer) wins. The
   y-scale control highlights the resolved scale; picking one fixes it until "Reset this chart".
   Rejected: deciding in `compile.py`, which has no values.
10. **Clocks by leaf** (decided): the last segment after `/` or `.` is one of `epoch`, `step`, `global_step`,
    `iteration`, `iter`. Clocks get no chart and are offered under "Progress" as x axes. `run.progress`
    stays on the exact `epoch` metric.
11. **Seed merging** (decided): merge when `config.seed` varies and some arm (the runs sharing every other
    varying key) has two or more seeds.
12. **The mark** (decided): as in the Brief; hover and page load play "gather left" once (420 ms, ease
    in-out, back to rest); under `prefers-reduced-motion` it jumps to the pose and back with no animation.
    The live favicon is `favicon-live.svg`, drawn in the gathered pose with a 2.8 s loop for browsers that
    animate SVG icons (Chrome shows the still gathered pose). The top bar mark does not loop (assumed).
    The 420 ms is an exception to `design/README.md`'s 120–150 ms motion rule, written there.
13. **Font instructions** (your decision): a new guide topic `type`, not a section in `kit.md`; linked one line
    from `kit`, `kit-api`, `anti-patterns`, `checklist` and the overview, and part of the `beamtime-views` skill.
    It covers custom code (one type class per kind of text, SVG and canvas) and views (which field renders in
    which style, Markdown conventions). Rejected: a kit helper returning font strings (`bt.theme.font(style)`),
    because classes reach SVG and HTML and the one canvas font already exists as `bt.theme.tokens.font`.
14. **Font literals are errors** (check: your decision; level **assumed**): `FONT` matches `font-size`,
    `font-family`, `fontSize`, `fontFamily`, `line-height`, `lineHeight`, `font:` and `.font =` (not `font: bt.theme.tokens.font` or `.font = bt.theme.tokens.font`),
    in strings too, comments masked, and is reported by `problems` (an error, like a color literal). Font
    *weight* stays allowed (`<b>`, `font-weight` for the one number that matters, as `design/README.md` says).
    Rejected: a warning in `lints`, because the spec already promises this as a ✓ check and colors are errors.
15. **Image steps** (your request 2026-11-18; details **assumed**): one scrubber per `images` block, its stops
    the logged steps (so it moves one logging interval at a time); ←/→ and Home/End when it has focus. It reads
    "step 4 000" or, when the page has a clock (D32's `CLOCK_LEAVES`, `epoch` first), "epoch 12 · step 4 000",
    and a "by step / by epoch" toggle in the block's tools spaces the stops by that value. On a group page every
    run's figure shows the scrubbed step; a run that logged nothing at that step shows its latest earlier image,
    labeled with its own step and muted. A view's `step: <n>` sets where the scrubber starts. While the scrubber
    is at the last stop, live updates move it to each new logging; after the viewer moves it, it stays. The step
    is kept per viewer like chart zoom (back and forward restore it), not in the URL. Rejected: loading every
    step's entries at once (`step: "all"`, which the `entries` limit of 200 cuts on a long run); a play button
    (not asked for).
16. **Figure tools for images** (your request 2026-11-18; details **assumed**): the block uses `ChartFrame`, so it
    has the chart head, download menu and expand button. Download gives the original file of each shown image
    (`<run>-<key>-step<n>.<ext>`), not a re-encoded PNG. Clicking an image or Expand opens the dialog on that run:
    the image as large as the dialog allows, pixelated when enlarged (as now), wheel or pinch zooms around the
    pointer, drag pans, double-click or the reset button fits it again, `+`/`−` buttons and keys, the scrubber
    below, and ‹ › to the previous or next run's image. No new library: zoom and pan are a CSS transform (the
    shell stays under 120 KB). Exports and screenshots show the starting step without the scrubber (`recording`).

17. **The modern design system** (your decision 2026-11-18): cool neutral grays at the old contrast targets;
    a centered content column of at most 1120 px; Section labels in mono above the content, folded into a
    collapsible block's toggle when its title repeats the label; `heading` in IBM Plex Sans 17 px 600; sub-groups
    and stats on `surface` panels; runs and notes as rows without lines and with a rounded hover tint; `radius`
    12 px; buttons fill on hover instead of drawing an edge; checkboxes, ranges, selects and number fields drawn
    by the system. Four directions were compared on a snapshot of a group page (current, airy, dense,
    editorial); you chose the current one. The `margin` token stays, unused by the app, because custom blocks
    may use it.
18. **Fonts say who wrote the text** (your decision 2026-11-18): serif (XCharter: `statement`, `prose`,
    `caption`) only for what a person or an agent wrote; sans (IBM Plex Sans: `title`, `heading`, `body`,
    `small`, `number`) for everything Beamtime names, labels, counts or states, names chosen by people
    included (groups, runs, metrics, block and chart titles), and status and verdict words; mono (IBM Plex
    Mono: `code`) as an accent of the interface: section labels, ids, code, logs, keys, never running text.
    Written into `design/README.md` § Type; agents learn it from T31's `guide type`.

## Q. Queries

### Q31. A live metric is a known metric (sonnet + review) — reproduced — **done**

- **Touches:** `src/beamtime/query/select.py` (`known_keys` 84–95, `check_known` 117–140, new
  `live_metric_keys`), `src/beamtime/query/kinds.py` (`series_kind` 217–265: meta `running`),
  `src/beamtime/ops/answers.py` (`merged` 676–681), `tests/query/test_queries.py`, `docs/design/03-index.md`.
- **Read:** `docs/design/03-index.md` § Query language (l. 196–210), § Query kinds `series` (l. 340–375),
  § Answers (l. 439); `tests/query/test_queries.py` `test_keys_of_running_runs_come_from_their_columns` (495).
- **Check:** `uv run pytest -q -n0 tests/query/test_queries.py -k "running or series or live"`, then the full checks.
- **Done:** a running run's new metric answers `series`, `runs` with `metric.<k>.last` and `where` on it,
  without error; an unknown metric still fails with suggestions (live keys among them); the series meta has
  `running`, and a merged answer sums it.
- **Risks:** a lost run (raw `running`, derived `lost`) still counts its columns → `test_live_keys_of_lost_runs`;
  a run in scope without a manifest yet → `test_live_keys_without_columns`; scope `depth: 1` excludes
  subgroup runs → `test_live_keys_respect_depth`.
- **Stop if:** the column keys of a running run are not readable without the index lock, or the fix needs
  the SDK to write its card earlier (that is the record plan's area).

`check_known` reads cards only; a running run's card lags up to 180 s (`CARD_EVERY_S`), so the view (which
uses `with_live_keys`) charts a metric the series call refuses. Start from a copy of the test at 495 that
asks `series {y: [live/new]}` and fails today.

1. `live_metric_keys(ctx: Context) -> set[str]`: runs in `scope_condition(ctx)` whose raw status is
   `running`, union of `open_columns(ctx.index.series / id)[1]` keys minus `TIME_KEY`; a missing manifest
   counts as none. Reuse it in `with_live_keys` only if that stays as simple; don't restructure it.
2. `check_known`: for `ns == "metric"`, a key in `live_metric_keys(ctx)` (computed once per call) is known.
   `known_keys(ctx, "metrics")` unions it, so suggestions include live keys.
3. `series_kind`: `meta(..., running=sum(r["run.status"] == "running" for r in runs))`; add `run.status` to
   the selected fields. `answers.merged`: `running` joins `matched`, `groups`, `means`.
4. 03-index.md: one line under `series` (meta `running`) and one under Query language (live keys count as known).

### Q32. The data answer lists its steps and their clock values (sonnet) — code — **done**

- **Touches:** `src/beamtime/query/models.py` (`Data` 143–148: new `clock: str | None = None`),
  `src/beamtime/query/kinds.py` (`data_kind` 476–528: meta `steps`, `clocks`), `src/beamtime/ops/answers.py`
  (`merged` 665–690: `steps` as a sorted union, `clocks` merged by step), `tests/query/test_queries.py`,
  `tests/remote/test_federation.py`, `docs/design/03-index.md` (§ Query kinds `data`, l. 517–523).
- **Read:** `tests/query/test_queries.py` around 547 (images come as references); `src/beamtime/query/read.py`
  `x_values` 302 and `value_at` 254; Q31's commit (the same meta merge).
- **Check:** `uv run pytest -q -n0 tests/query/test_queries.py -k "data or images"`;
  `uv run pytest -q tests/remote/test_federation.py -k data`; then the full checks.
- **Done:** `data {key: samples, step: last}` on the synth lr sweep answers the last step's entries and
  `meta.steps` with every logged step; `clock: epoch` adds `meta.clocks` with one value per step (`null` where no
  run logged the clock at or before it); `step: <n>` still answers only that step's entries, with the same
  `steps`; two sources' `steps` merge into one sorted list.
- **Risks:** a key logged by many runs at different steps lists their union, not per run (the block needs one
  axis) → `test_data_steps_union`; an unknown `clock` is a `QueryError` with suggestions, like an unknown metric
  (`check_known`), not a silent `null` column → `test_data_unknown_clock`; the query stays one SQL read plus one
  column read per run (no file reads): time it on scale M in the test's comment if it is close.
- **Stop if:** clock values differ between runs at the same step in a way one value per step can't show (then
  report: per-run `clocks` would be the alternative).

1. `data_kind`: `steps = sorted({s for _, s, _ in rows})` before the step filter; `meta(..., steps=steps)`.
2. With `q.clock`: `check_known` on `metric.<clock>.last`; for each run in `by_run`, `x_values(cols, q.clock,
   steps)` from its columns; per step the first run's non-`null` value; `meta(..., clocks=values)`.
3. `answers.merged`: `steps` → sorted union; `clocks` → by step, first non-`null`.
4. `03-index.md` § `data`: the two meta fields and `clock`.

## D. The default view and the chart rules

### D31. Sections by prefix with `/`, `.` and `_` (sonnet) — reproduced — **done**

- **Touches:** `src/beamtime/views/defaults.py` (`curves` 220–262, `ordered_metrics` 285–293, `prefix`
  316–322, new `KNOWN_PREFIXES`), `src/beamtime/guide/parts/charts.md` (l. 21), `docs/quickstart.md` (l. 32),
  `docs/design/07-web-ui.md` (l. 473–479), `tests/views/test_views.py` (480, 503).
- **Read:** `docs/design/07-web-ui.md` § the built-in default view (l. 471–485); `src/beamtime/guide/__init__.py`
  270–310 (uses `prefix`).
- **Check:** `uv run pytest -q -n0 tests/views tests/guide -k "section or prefix or example"`, then the full
  checks (`tests/test_docs.py` covers the quickstart).
- **Done:** `val_loss`, `val.acc` and `val/f1` share section `val`; `train/loss` alone is section `train (1)`;
  `lr` and `value_x` stay in Other; the guide's charts topic recommends `<prefix>/<name>`.
- **Risks:** `validation_loss` must not split as `val` + `idation_loss` → `test_longest_known_prefix_wins`;
  `value_loss` and `vale` stay unprefixed → `test_prefix_needs_a_separator`; `sys/cpu` stays System and a
  group with one section and no pins stays a plain grid → existing tests at 480 and 503.
- **Stop if:** section ids must change for metrics that already had a section (stored open/closed state).

1. `prefix(metric) -> str`: text before the first `/` if any; else, for the longest `p` in
   `KNOWN_PREFIXES = EVAL_PREFIXES + TRAIN_PREFIXES` with `metric.lower().startswith(p)` and the next
   character `.` or `_`, the metric's own first `len(p)` characters; else `""`.
2. `curves`: drop `sizes` and the one-metric rule (231–235); a metric's section is `prefix(k)`. Docstring: Other
   is unprefixed metrics only.
3. `ordered_metrics`: rank by `prefix(k).lower()` with the same table.
4. charts.md: "Name metrics `<prefix>/<name>` (`train/loss`, `val/acc`): each prefix gets its section; `val_`
   and `val.` work for the known prefixes." quickstart.md: log `"train/energy"` in the example.
5. 07-web-ui.md: the sections sentence without "prefixes of one metric", with the separators.

### D33. Seeds merge by arms; the swept key colors (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/views/defaults.py` (`SEED_GROUPING_ABOVE` 14 removed, `group_body` 73–120, new
  `merges_seeds` and `swept`, `curves`/`line` 220–283: a `color` argument), `tests/views/test_views.py`,
  `docs/design/07-web-ui.md` (l. 473–474).
- **Read:** `docs/design/03-index.md` § Selecting runs, Seeds (l. 297–300); `src/beamtime/query/distinguish.py` 21–53.
- **Check:** `uv run pytest -q -n0 tests/views tests/query/test_distinguish.py`, then the full checks.
- **Done:** a 2-arm × 4-seed group (8 runs) merges; a group of 2 runs differing only in seed merges; a group
  whose every arm has one seed doesn't; a 3-value lr sweep without seeds gets `color: config.lr` on every
  metric chart except System.
- **Risks:** seed aliased to another key (not in `varying`) → no merge (`test_aliased_seed_does_not_merge`);
  arms counted on own runs only when `own` (`depth: 1`) → `test_arms_count_own_runs`; two varying keys → no
  color (`test_two_swept_keys_no_color`).
- **Stop if:** the seed key must be detected by `is_seed` instead of `SEEDS_FIELD` (that is the record plan, audit 5).

1. `merges_seeds(ctx, path, varying, own) -> bool`: `SEEDS_FIELD in varying`; arms from
   `call("runs", {"from": path, "depth": 1 if own else "all", "select": others, "limit": 10000})` with
   `others = [k for k in varying if k != SEEDS_FIELD]`; true when a `Counter` of the row tuples has a count ≥ 2.
2. `group_body`: `many = merges_seeds(...)`; `color = others[0] if not many and len(others) == 1 else None`,
   passed through `curves` to `line` (`m.Line(color=...)`), never for System charts.
3. 07-web-ui.md: "averaged over `config.seed` when some arm has two or more seeds"; one line on the color.

### D32. Clocks by leaf name (sonnet) — code

- **Touches:** `src/beamtime/views/defaults.py` (`CLOCKS` 23 → `CLOCK_LEAVES`, new `is_clock`; uses at 56,
  232), `src/beamtime/guide/__init__.py` (274–284), `src/beamtime/views/settings.py` (`generated_ts` 105–116:
  export `CLOCK_LEAVES`), `web/src/bt/chart-defaults.ts` (generated), `web/src/blocks/line-settings.ts`
  (`xGroups` 23–27), `web/src/bt/axes.ts` (8–18), `tests/views/test_views.py`, `web/test/axes.test.ts`,
  `docs/design/07-web-ui.md` (l. 389–392, 496).
- **Read:** `docs/design/07-web-ui.md` § Charts, settings (l. 389–399).
- **Check:** `uv run pytest -q -n0 tests/views`; `cd web && npm test`; then build and the full checks.
- **Done:** `train/epoch`, `step`, `trainer.global_step`, `iter` get no chart and appear under "Progress" in
  the x-axis picker; `steps_per_s` and `epoch_time` still chart; the x title of `train/epoch` is "epoch".
- **Risks:** `step_size` or `iteration_ms` must not count → `test_clock_is_the_whole_leaf`; the generated file
  is current → `tests/views/test_settings.py`.
- **Stop if:** a clock must also drive `run.progress` (decision 10 says no).

1. `CLOCK_LEAVES = ("epoch", "step", "global_step", "iteration", "iter")`; `is_clock(metric) -> bool` on
   `re.split(r"[/.]", metric)[-1]`. Replace every `k not in CLOCKS`.
2. `generated_ts` exports `CLOCK_LEAVES`; run `scripts/build-chart-defaults`.
3. `xGroups`: Progress lists `_step`, then the logged clocks, `_t`, `_elapsed`; `axes.ts` titles a clock by its leaf.

### D34. Log scale from the values (sonnet + review) — code

- **Touches:** `src/beamtime/views/compile.py` (`line` 282–320: `guess` 303 removed, `scale` only when
  explicit), `src/beamtime/views/model.py` (`Line.scale` description 55–61), `web/src/bt/curves.ts` (new
  `autoScale`), `web/src/bt/chart-settings.ts` (`BASE` 11), `web/src/bt/prefs.ts` (`Effective` 97),
  `web/src/blocks/line.ts` (67–72, 99–100, 142, 178), `web/src/blocks/line-settings.ts` (`scale` 130–135),
  `web/test/curves.test.ts`, `web/test/fixtures/chart-settings.json`, `tests/views/test_views.py`,
  `tests/views/test_settings.py`, `src/beamtime/guide/parts/charts.md` (l. 28–30), `docs/design/05-views.md`
  (l. 187), `docs/design/07-web-ui.md` (l. 396–397).
- **Read:** `docs/plans/v0.3/auto-detection-audit.md` item 2; `docs/design/05-views.md` § blocks table (l. 187).
- **Check:** `uv run pytest -q -n0 tests/views tests/serve/test_chart_settings.py`; `cd web && npm test`;
  `rg -n '"log"|scale' tests/views tests/serve` for expectations to update; then build and the full checks.
- **Done:** a loss from 2.3 to 0.01 draws log; a loss within one decade, an ELBO below zero and any metric
  with a zero draw linear; a view `metrics: {x: {scale: log}}` or a block `scale` still wins; the PDF export
  gets the resolved scale.
- **Risks:** all values null or one value → linear (`autoScale` test); a band below zero with a positive mean
  stays log only if every `y` is positive (decided on `y`) → test; an exported page resolves the same way
  (no server) → `tests/serve/test_export.py` still passes.
- **Stop if:** the renderer's layout check or `src/beamtime/views/export.py` needs the scale on the server.

1. compile: `scale = n.scale or (info.scale if info and info.scale else None)`; pass `scale` only when not
   `None`. Remove the `lower_is_better` import if unused.
2. `autoScale(answer: {curves: any[]}): "log" | "linear"`: over every curve's finite `y` (hidden ones too, so
   hiding never flips the axis): log when all > 0 and max/min > 100.
3. `BASE.scale` becomes `null`; `Effective.scale` is `Scale | null`; line.ts resolves
   `const scale = prefs.scale ?? autoScale(last.current)` before `reshape`, and uses `scale` wherever
   `prefs.scale` was read. The y-scale control marks the resolved scale.
4. Spec and guide: "default: the view's metrics, else log when every value is positive and spans more than
   two decades, else linear".

## W. The web UI

### W31. A sidebar that (un)collapses (sonnet) — code — **done**

- **Touches:** `web/src/shell/sidebar.ts` (`Sidebar` 15–86, `Item` 88–117, `withAncestors` 125–131 replaced),
  `web/src/shell/tree.ts` (new `withPath`), `web/src/styles/shell.css` (`.twisty` 57), `web/test/tree.test.ts`,
  `tests/serve/test_browser.py`, `docs/design/07-web-ui.md` (l. 121–122, 186).
- **Read:** `docs/design/07-web-ui.md` § layout (l. 100–125), keyboard (l. 186, 508).
- **Check:** `cd web && npm test`; `uv run pytest -q tests/serve/test_browser.py -k tree`; then build and the full checks.
- **Done:** on a page three levels deep, a click on an ancestor's chevron closes it and a second opens it;
  a click on the current group's name toggles it; a click on another name navigates; a filter shows matches
  expanded with inert chevrons; ArrowLeft/Right behave as before.
- **Risks:** navigating to a group inside a closed group opens its ancestors (once) → `withPath` test;
  closing the current group's parent leaves the current group hidden and the tree consistent → browser test;
  remote paths (`@au002a/a/b`) open `@au002a/a`, never the host root through `open` → tree test.
- **Stop if:** the host roots' `closed` set needs the same change (it doesn't today: hosts are not forced).

1. `tree.ts: withPath(open: Set<string>, path: string | null): Set<string>`: `open` plus every ancestor group of
   `path` (the old `withAncestors`), exported and tested.
2. `Sidebar`: drop `withAncestors` from `visible(...)`; in the existing `current` effect, when `current` changes,
   `setOpen`/`store` `withPath(open, current)` if it adds anything. `isOpen` stays the only truth for the chevron.
3. `Item` gets `filtering: boolean`: the twisty ignores clicks and sets `aria-disabled` while filtering; the
   link's `onClick` toggles instead of navigating when `props.current && expandable && !filtering`.
4. `.twisty`: `inline-size: 24px; align-self: stretch; justify-content: center; align-items: center;
   margin-inline: -4px; cursor: pointer` (tokens only; check with `scripts/check-design`).

### W32. The x axis follows the shown curves (sonnet) — code — **done**

- **Touches:** `web/src/bt/curves.ts` (new `xExtent`), `web/src/bt/uplot.ts` (x `range` 105), `web/test/curves.test.ts`,
  `tests/serve/test_browser.py` (a legend toggle), `docs/design/07-web-ui.md` (l. 382–384).
- **Read:** `docs/design/07-web-ui.md` § Charts, Legend and Zoom (l. 382–388); `web/src/bt/uplot.ts` 286–311 (`update`).
- **Check:** `cd web && npm test`; `uv run pytest -q tests/serve/test_browser.py -k "legend or hide"`; then build
  and the full checks.
- **Done:** two runs to step 1000 and 5000: hiding the long one gives an x axis ending near 1000; showing it
  again restores 5000; a zoom is kept.
- **Risks:** every curve hidden → fall back to uPlot's `min`/`max` (`xExtent` returns `null`); a single x →
  the existing ±1 % padding; raw curves of a smoothed chart count with their curve → curves test.
- **Stop if:** uPlot does not call the x range on `setSeries` and `update` isn't reached on a legend click
  (it is: `all.hidden` is in `useChart`'s deps, line.ts 129).

1. `xExtent(curves: Curve[], hidden: Set<string>): [number, number] | null`: min and max of `x` over points
   with a finite `y` of the shown curves.
2. The x scale's `range` reads `current`: `const e = xExtent([...current.curves, ...(current.raw ?? [])], current.hidden) ?? [min, max]`,
   then the single-value padding. Zooms set the scale explicitly (`applyZoom`) and are unaffected.

### W33. Markers: one rule per chart, and a setting (sonnet) — reproduced — **done**

- **Touches:** `src/beamtime/views/model.py` (`Line` 40–69: `markers`), `web/src/bt/chart-defaults.ts`
  (generated), `web/src/bt/prefs.ts` (`ChartPrefs` 8–25, `Effective` 97), `web/src/bt/curves.ts` (`markers`
  142–149 → `marksChart`), `web/src/bt/uplot.ts` (`LineSpec` ~19, points 77), `web/src/blocks/line.ts`
  (`specFor` 84–117), `web/src/blocks/line-settings.ts` (`Field`, `LINE_FIELDS`, `SECTIONS` 29–39, new field),
  `web/test/curves.test.ts`, `web/test/fixtures/chart-settings.json`, `tests/views/test_settings.py`,
  `docs/design/05-views.md` (l. 187), `docs/design/07-web-ui.md` (l. 396–397).
- **Read:** `src/beamtime/views/settings.py` (all, 116 lines); `docs/design/07-web-ui.md` § Charts, settings.
- **Check:** `uv run python scripts/build-chart-defaults && uv run pytest -q -n0 tests/views/test_settings.py`;
  `cd web && npm test`; then build and the full checks.
- **Done:** a chart of a 12-point and a 400-point curve marks neither (auto), both with `on`; a chart of two
  12-point curves marks both and keeps them while each grows to 30 and drops them together at 31; a
  one-point curve is marked under `off`; `markers: on` round-trips through Save as view.
- **Risks:** a hidden long curve must not suppress markers of the shown short ones → test; the setting at its
  default is not written into a saved view (`settle`) → `test_settings`; null-only curves count 0 → test.
- **Stop if:** uPlot's `points.filter` can't read the per-chart decision through `current`.

1. `m.Line.markers: Annotated[Literal["auto", "on", "off"], msgspec.Meta(description="dots on points; auto when
   every curve is sparse")] = "auto"`; regenerate `chart-defaults.ts`; add `markers` to every `effective` in the fixture.
2. `curves.ts: marksChart(curves: Curve[], hidden: Set<string>, mode): boolean` (decision 4); `pointsOf(ys,
   all: boolean): number[]` returns every finite index when `all`, else the index of a lone finite point.
3. `LineSpec.markers: boolean`; uplot's filter: `pointsOf(self.data[at], current.markers)`.
4. Settings: "Markers" segmented control (auto, on, off) in the Axes section after `legend`.

### W34. Color by offers what can color (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/query/distinguish.py` (`Distinct` 13–18, `distinguishing` 44–53: `dropped`),
  `src/beamtime/query/kinds.py` (`keys_kind` 157–162), `web/src/bt/chart-settings.ts` (new `colorOptions`),
  `web/src/blocks/line-settings.ts` (`color` 97–102, `Context` 41–50, `Settings` 168–198),
  `tests/query/test_distinguish.py`, `web/test/chart-settings.test.ts`, `docs/design/03-index.md` (keys answer),
  `docs/design/07-web-ui.md` (l. 389–399).
- **Read:** `docs/plans/v0.3/auto-detection-audit.md` item 8; `web/src/blocks/line.ts` 38–43, 236–241 (`colorsCall`, `fieldColors`).
- **Check:** `uv run pytest -q -n0 tests/query/test_distinguish.py tests/query/test_queries.py -k keys`;
  `cd web && npm test`; then build and the full checks.
- **Done:** a seed-only group offers `seed`, status, tags, name, folder; a group with `model` determined by
  `arch` lists `model · set by arch`; an alias lists `· same split as <canon>`; picking `run.status` colors
  running and finished runs apart.
- **Risks:** `run.tags` (a list) colors by the combination without throwing → `fieldColors` path, chart test;
  a key both alias and dropped can't happen (aliases are folded first) → distinguish test; a remote answer
  without `dropped` → `colorOptions` treats it as `{}`.
- **Stop if:** coloring by a run field needs a server change beyond `keys` (the `runs` call already selects them).

1. `Distinct.dropped: dict[str, str]`: each dropped key → the first reducer that determines it, both
   `config.`-prefixed; `keys` answer `config.dropped`.
2. `colorOptions(keys): [group: string, [value: string, label: string][]][]` per decision 6, groups omitted
   when empty; the select renders `<optgroup>`s with "none" first.
3. 03-index.md: `dropped` in the keys answer; 07-web-ui.md: the Colors section and what it offers.

### W35. Waiting for the first value (sonnet) — code

- **Touches:** `web/src/blocks/line.ts` (`empty` 147, notice 220–224), `web/src/bt/curves.ts` (`Curves`: `running`),
  `web/test/curves.test.ts`, `tests/serve/test_browser.py`, `docs/design/07-web-ui.md` (l. 418–419).
- **Read:** Q31's commit; `web/src/blocks/common.ts` `Notice` 46–52; `design/components/Notice.md`.
- **Check:** `cd web && npm test`; `uv run pytest -q tests/serve/test_browser.py -k live`; then build and the full checks.
- **Done:** a chart whose curves have no finite point while `meta.running > 0` shows the info notice "Waiting for
  the first value of `<title>`."; with nothing running it shows "No run in scope logs `<title>`."; as soon as a
  value arrives the live refetch draws it.
- **Risks:** a curve with an empty `x` (column opened, nothing committed) counts as empty → curves test; an exported
  page (no `running`) keeps the old text → snapshot test.
- **Stop if:** Q31 is not done.

1. `reshape` keeps `answer.meta?.running ?? 0` as `Curves.running`.
2. `empty = curves && !curves.curves.some((c) => c.y.some((v) => v !== null && Number.isFinite(v)))`; the
   notice picks its text by `curves.running`.

### W36. A data table says when rows are hidden, and the screenshot draws every chart (sonnet) — code

- **Touches:** `web/src/blocks/data.ts` (`DataTable` 15–52: the wrap and the `more-rows` line), `web/src/styles/blocks.css`
  (`.table-wrap` 58, `.more-rows` 74), `web/src/bt/index.ts` (`useVisible` 94–113), `web/src/router.ts` (`rendering`,
  `recording` 167–169), `src/beamtime/views/render.py` (`render_draft` 60, `render_page` 86, `settle` 144–159),
  `web/test/`, `tests/serve/test_browser.py`, `tests/serve/test_render.py`, `design/components/Table.md`,
  `docs/design/07-web-ui.md` (Lazy rendering l. 200, Screenshots l. 247–256).
- **Read:** `design/README.md` and `design/components/Table.md`, `Notice.md` (values only from `design/tokens.json`;
  `scripts/check-design`); `docs/plans/v0.3/view-data/results.md` (the baseline table, l. 52–53, 152) and
  `bench/agents/MISTAKES.md`; `src/beamtime/views/export.py` 54, 101 (exports open pages with `record=1`).
- **Check:** `cd web && npm test`; `uv run pytest -q tests/serve/test_browser.py -k "table or rows"`;
  `uv run pytest -q tests/serve/test_render.py -k "below or tall or rows"`; then build and the full checks.
- **Done:** a `data_table` of 15 rows (the block clips at `max-block-size` 560 px after about 13) says that rows are
  hidden, in a place a screenshot shows (a muted count line such as "13 of 15 rows shown, scroll for the rest", or an
  edge shadow); a table that fits shows no hint; the rows stay scrollable. `view_render` of a page whose charts lie
  below the first screen draws every chart: no blank chart in the page shot, and `settle` still ends within
  `TIME_LIMIT_S`. After this the view-data bench's checklist items "the table has all its rows" and "no empty charts"
  can be judged on the screenshot again (say so in this ticket's commit; the bench itself is not changed here).
- **Risks:** the hint must not double `more-rows` for a table cut by `limit` (one line, one wording); `record=1`
  also opens folded sections, so a fix that reuses it changes what a page shot shows, which is not wanted: the saved
  view's folds stay as saved; a page of many charts costs more render time and requests → time the render of the
  40-chart page in `test_a_tall_page_is_capped_and_names_what_fell_below`; the shell stays under 120 KB compressed.
- **Stop if:** forcing every block visible makes the render exceed `TIME_LIMIT_S` on that 40-chart page (then
  scroll in steps and wait for `__btBusy`, and say so).

1. `DataTable`: know whether `.table-wrap` overflows (a ref and its scroll and client heights, re-measured on resize
   and when `rows` change) and, if it does, show one muted line under the table in the `more-rows` style, merged with
   the existing "`limit` of N rows shown" so that line says both at most once. Describe it in `Table.md`.
2. Rendering: under `?render=1` charts and custom blocks mount without waiting for the viewport (`useVisible`
   starts `true` when `rendering`, as it does when `recording`), or the renderer scrolls the page once before the
   shot; take the first unless it breaks the live browser path (the browser never sets `render`). Folds stay as saved.
3. Tests: a browser test of a 15-row `data_table` (fixture file in the project) that the hint is present and that a
   3-row table has none; a render test of a long page whose lower charts are not blank (the render's blank-block
   check, or the shot's pixels, over the 40-chart page) and one that a folded section stays folded.
4. `07-web-ui.md`: Lazy rendering names the exception (renders and screenshots mount every block); Table.md gets the hint.

### W37. Images: step through every logging, expand, zoom, download (sonnet + review) — code

- **Touches:** `web/src/blocks/logged.ts` (`Images` 13–29), new `web/src/bt/zoom.ts` (pan and zoom of one element),
  `web/src/bt/frame.ts` (`ChartFrame` 66–110, `Downloads` 23: a file download set), `web/src/shell/expanded.ts`
  (the dialog's label for images), `web/src/styles/blocks.css` (`.images` 96–99), `src/beamtime/views/compile.py`
  (214–216: `clock` on the images call when the page has one), `src/beamtime/views/defaults.py` (141–142),
  `design/components/` (new `Images.md`; `components.css` for the scrubber if it isn't a plain `input[type=range]`
  styled from tokens), `web/test/` (new `images.test.ts`), `tests/serve/test_browser.py`, `tests/views/test_views.py`,
  `docs/design/05-views.md` (l. 206: `slider` is no longer wave 2), `docs/design/07-web-ui.md` (logged images, l. 464,
  509; tools on hover 412), `src/beamtime/serve/static/` (rebuilt).
- **Read:** decisions 15 and 16; Q32's and D32's commits; `design/README.md`, `design/components/Chart.md`;
  `web/src/blocks/line.ts` 25–40 (how a chart block expands); `web/src/bt/host.ts` (download, expand);
  `web/src/snapshot.ts` `fileUrl`; `docs/design/07-web-ui.md` 79 (back and forward restore zoom) and 232–237.
- **Check:** `cd web && npm test`; `uv run pytest -q tests/views/test_views.py -k images`;
  `uv run pytest -q tests/serve/test_browser.py -k images`; then build and the full checks.
- **Done:** on the synth lr sweep's group page, the `samples` block shows every run's last image with a scrubber
  under them; moving it (drag, ←/→, Home/End) shows each earlier logging, labeled "epoch e · step s" when the page
  logs an epoch, and "by epoch" spaces the stops by epoch; Download saves the shown images' original files;
  clicking an image opens the dialog on that run, where wheel and drag zoom and pan, double-click fits, ‹ › change
  the run, and the scrubber works as inline; back and forward restore the scrubbed step; a running run's new image
  appears and the scrubber follows it only when it was at the last stop; a key logged once shows no scrubber; an
  export or page shot shows the starting step without the scrubber; the shell stays under 120 KB compressed.
- **Risks:** fast scrubbing must not queue one request per stop (debounce the refetch, keep the old images until the
  new ones load, so the block doesn't flash) → `images.test.ts`; images of different sizes keep one tile size inline
  (`object-fit: contain`) → browser test; zoom must not scroll the page or close the dialog (wheel `preventDefault`
  only inside the image) → browser test; a remote run's file comes through `fileUrl(sourcedRun(...))` as today; the
  text block (`Text`) is not changed.
- **Stop if:** `ChartFrame` can't hold a non-uPlot child without changing its line-chart callers (then wrap the
  images in the same head and tools by hand and say so); Q32 or D32 is not done.

1. `Images`: one `useData("main")` answer; keep the scrubbed step in viewer state (the same store and history entry
   chart zoom uses); refetch with `step: <s>` when it changes. Each run's figure is that run's entry at `s`, else its
   latest entry at or before `s` (Q32's answer has only the asked step: ask `step: [first, s]` with `limit` per run
   if needed, or keep the last answer per run; pick the simpler and test it).
2. Scrubber: an `input type=range` over the indices of `meta.steps` (by step) or the distinct `meta.clocks` (by
   epoch); its label in the `small` type class with `step()` from `bt/fmt.ts`.
3. Frame: `ChartFrame` with `downloads` that save each shown image's file (`host().download(fileUrl(...), name)`),
   `onExpand` → `host().expand(node, view)` with the clicked run in the node's props.
4. Expanded: the large image in `zoom.ts` (`transform: translate(...) scale(...)`, wheel around the pointer, drag,
   double-click and a reset button to fit, `+`/`−`), ‹ › over the runs of the answer, the scrubber below.
5. `compile.py`: the images call gains `clock` when the page's clocks (D32) include one, `epoch` first.
6. Spec: `05-views.md` (the scrubber is part of `images`; `step` is the start), `07-web-ui.md` (logged images: the
   scrubber, the dialog, downloads), `design/components/Images.md`.

## L. The mark

### L31. The `///` mark in the design system (sonnet + review) — code

- **Touches:** new `design/components/Mark.md`, `design/components.css` (`.mark`), `design/favicon.svg`
  (rewritten), new `design/favicon-live.svg`, `design/gallery.html`, `design/README.md` (Components list,
  Motion), `scripts/build-tokens` (`favicon` 73–81: both files, `stroke`), `web/build.mjs` (l. 68: copy
  `favicon-live.svg`), `tests/test_design.py` (32–44, 63), `src/beamtime/serve/static/` (rebuilt).
- **Read:** `design/README.md` (all); `design/components/Sym.md` as a model page; `tests/test_design.py` 32–70.
- **Check:** `python3 scripts/build-tokens --check && scripts/check-design && uv run pytest -q -n0 tests/test_design.py`;
  `cd web && npm run build`; then the full checks.
- **Done:** `favicon.svg` is the rest pose with light and dark accent strokes; `favicon-live.svg` is the
  gathered pose with a 2.8 s CSS loop (gathered → rest → gathered), off under `prefers-reduced-motion`;
  `.mark` animates hover and load as decision 12; the gallery shows rest, gathered and the hover; the
  component test passes for `Mark`.
- **Risks:** `build-tokens` must fill both files' light and dark strokes from `accent` → `test_tokens_css_is_current`;
  a CSS transform on SVG paths needs `transform-box: fill-box` in Safari → by hand in the gallery; reduced
  motion → the gallery under emulation.
- **Stop if:** the motion can't be expressed in `components.css` with tokens (then extend `tokens.json` first and say so).

1. Markup: `<svg class="mark" viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 19.5 L9.5 4.5"/><path class="mark-2" d="M8.5 19.5 L15.5 4.5"/><path class="mark-3" d="M14.5 19.5 L21.5 4.5"/></svg>`,
   `stroke: var(--accent); stroke-width: 2.6; stroke-linecap: round; fill: none`.
2. `.mark:hover .mark-2 { transform: translateX(-2px) }`, `.mark-3` −4 px, 420 ms ease-in-out; a `mark-gather`
   keyframe plays once on load; `@media (prefers-reduced-motion: reduce)`: no transition or animation.
3. Mark.md: what it is, the two poses, the motions, sizes (16 in the top bar), never as a status sign.

### L32. The mark in the app (sonnet) — code

- **Touches:** new `web/src/ui/mark.ts`, `web/src/shell/bars.ts` (`TopBar` 22–41, project link 28),
  `web/src/shell/favicon.ts` (16–52: `withDot` removed), `web/src/styles/shell.css` (`.project`),
  `tests/serve/test_browser.py` (`test_the_title_and_favicon_show_a_running_run` 257–270),
  `docs/design/07-web-ui.md` (l. 102, 119–120, 155–159).
- **Read:** L31's `design/components/Mark.md`; `docs/design/07-web-ui.md` § The browser tab (l. 153–159).
- **Check:** `cd web && npm test && npm run build`; `uv run pytest -q tests/serve/test_browser.py -k favicon`;
  then the full checks.
- **Done:** the top bar shows the mark before the project name, linked with it; it gathers on hover and once on
  load; the favicon is `/static/favicon-live.svg` while runs are live and `/static/favicon.svg` otherwise; an
  exported page still has its data-URI favicon.
- **Risks:** the shell stays under 120 KB compressed (`npm run build` reports it); the favicon swap must not
  flicker on every live tick (set `href` only on change) → browser test; reduced motion → emulated in the browser test.
- **Stop if:** the build can't serve a second favicon file without a server route change.

1. `Mark({ size = 16 })` renders L31's markup; the `.project` link holds `<Mark />` and the name.
2. `setIcon(live)`: `link.type = "image/svg+xml"`, `link.href = live ? LIVE : PLAIN`; the canvas code goes.
3. 07-web-ui.md: top bar "mark · project", the favicon paragraph rewritten for the two files.

## S. The design system

### S31. Adopt the modern design system everywhere (sonnet + review) — code — **done**

The design system (`design/`) and a first pass over the app landed together before this ticket: tokens, the
Section, Table, Stat, Note, Button, IconButton and Field components, the collapse toggles that carry the
section label (`.toggle-label` in `web/src/blocks/common.ts` `Collapsible` and `web/src/blocks/layout.ts`), the
note rows (`web/src/blocks/context.ts` `NoteItem`, `web/src/styles/shell.css` `.note`), the native controls, and
the bundle. Decisions 17 and 18 say what the look is; this ticket makes everything else agree.

- **Touches:** `src/beamtime/guide/parts/kit.md` (§ Titles go in the left column, 113–120), `views.md` (60–63),
  `checklist.md` (13), `src/beamtime/guide/examples/sweep.yaml` (4), `tests/guide/test_guide.py` (41, 135–144),
  `web/src/ui/primitives.ts` (28, comment), `web/src/bt/labels.ts` (1, comment), `docs/design/05-views.md`
  (482, 508, 675, 712, 989), `docs/design/07-web-ui.md` (45–47, 558, and any other mention of the margin),
  `tests/serve/test_browser.py` (464: the `config` section's label is now in its toggle), `web/src/styles/*.css`
  and `web/src/shell/*.ts` only where a screen below breaks a rule of `design/README.md`; the skills generated
  by `scripts/build-plugin` if they carry the changed parts; `src/beamtime/serve/static/` (rebuilt).
- **Read:** `design/README.md` (all, especially § Look and § Differences from the export); `design/components/Section.md`,
  `Table.md`, `Note.md`, `Field.md`; decisions 17 and 18; `git show` of the commit that landed the design system.
- **Check:** `python3 scripts/build-tokens --check && scripts/check-design && uv run pytest -q -n0 tests/test_design.py tests/guide/test_guide.py`;
  `cd web && npm test && npm run build`; `uv run pytest -q tests/serve/test_browser.py`; then the full checks;
  by hand: `beamtime serve` on a synth log dir (`beamtime.synth.generate`), every screen below in light and dark.
- **Done:** no guide part, example, spec document or code comment mentions a margin column, a left column or the
  warm notebook look; the guide says a one- or two-word title becomes the section's label, in mono above the
  block or in its collapse toggle; `test_vocabulary_table_and_title_rule_are_in_the_parts` asserts the new
  wording; each screen below follows `design/README.md` in both themes (labels above, one header line per
  collapsible block, no hairline rows in lists, fonts by decision 18, drawn controls, 12 px radius) or its fix is
  in this commit; the browser tests pass.
- **Risks:** custom blocks of existing views may lay themselves out against the old margin (`var(--margin)`) →
  the token stays (decision 17), grep `guide/examples/code/` for it; the shell stays under 120 KB compressed;
  the exported HTML (`beamtime export --html`) and the headless renderer use the same CSS but are easy to forget →
  export one page and render one view by hand; dialogs and popovers on `surface` with the new 12 px radius may clip
  their content → by hand.
- **Stop if:** a screen needs a look the design system doesn't describe (then extend `design/` first, as
  `design/README.md` § Not in the design system says, and say so in the commit).

1. Guide: rename kit.md's heading to "Titles become section labels" and say: a top-level `section` (or custom
   block) titled with one or two words shows that title as the section's label, in mono above the block (in its
   collapse toggle when the block collapses); longer titles, nested sections, Markdown `##` and `bt.ui.Section`
   render as a sans `heading` inside the block. Same meaning in one bullet of views.md, checklist item 9 ("Does
   every top-level section have a one- or two-word title for its label?") and the comment in `sweep.yaml`;
   rename "margin label" to "section label" in `test_guide.py` and assert "section label" in the three parts.
2. Spec: 05-views.md 482 notes that `margin` is unused by the app and kept for custom code; 508 names mono for
   code and section labels; 675 and 712 say "section label"; 989 drops "notebook look". 07-web-ui.md 45–47
   describes the page as decision 17 does; 558 drops "warm paper, a serif for titles".
3. Screens, in light and dark, against `design/README.md`: group page, run page (config, output, images), the
   drawer (run details, notes), the timeline, settings, view history and diff, the command palette and help, chart
   settings, the add-chart menu, a custom block (`guide/examples/code/`), an exported page, the headless render.
   Fix what breaks a rule (for example a hairline list, a serif name, a browser-default control, a 6 px corner
   hard-coded somewhere); list what you checked in the commit message.
4. Browser test 464: find the config block by its toggle (`.collapse-toggle:has(.toggle-label:text-is('config'))`).

## T. Type

### T31. Font instructions for agents, and a font check (sonnet + review) — real data — **done**

Lines below are at `274fc44`, not the plan's base commit; refresh them if Q31–D33 moved them.

- **Touches:** new `src/beamtime/guide/parts/type.md`, `src/beamtime/guide/__init__.py` (`TOPICS` 16–31),
  `src/beamtime/ops/registry.py` (`GuideParams.part` 452–470), `src/beamtime/guide/skills.py` (`beamtime-views` 10),
  `src/beamtime/guide/parts/overview.md` (topic table 102–114), `kit.md` (§ Reuse Beamtime's vocabulary),
  `kit-api.md` (Rules), `anti-patterns.md`, `checklist.md`, `src/beamtime/views/code.py` (`FONT` new beside
  `COLOR` 39, `problems` 41–76), `tests/views/test_custom.py` (`test_code_checks` 55–72),
  `tests/views/test_views.py` (`test_chart_frames_and_live_data_pass_the_code_lints` 778–787),
  `tests/guide/test_guide.py` (new test), `docs/design/05-views.md` (guide table 696–708, anti-patterns 790).
- **Read:** `design/README.md` § Look (Type: the family rule) and § Components; decision 18; `design/tokens.css` 20–31 (the type styles);
  `src/beamtime/guide/parts/kit.md` (all); `web/src/blocks/common.ts` 35–45 (captions), `web/src/blocks/layout.ts`
  25–40 (section titles), `web/src/bt/md.ts` (what Markdown renders), `web/src/kit/snapshot.ts` 18.
- **Check:** `uv run pytest -q -n0 tests/views/test_custom.py tests/views/test_views.py tests/guide/test_guide.py`;
  `uv run beamtime guide type | wc -w` (under 900 words); then the full checks.
- **Done:** `beamtime guide type` prints the part, which opens with the family rule of decision 18; the overview, `kit`, `kit-api`, `anti-patterns` and `checklist`
  each point to it in one line; `code.problems` reports `font literal 'font-size'` with its fix for each of
  `font-size="12"` on SVG text, `.attr("font-size", 12)`, `.style("font-family", "serif")`, `style="font: 12px x"`,
  `fontSize: 12` and `line-height: 1.2`, and nothing for `class="small"`, `ctx.font = bt.theme.tokens.font`,
  `font-weight` or the guide's phase map; 05-views.md's ✓ row is true.
- **Risks:** a word in a caption string ("font size") must not match → a test with `'pick a font size'`;
  `{font: bt.theme.tokens.font}` in a uPlot option must pass → test; the guide part must only name classes and
  `bt` names that exist (`test_kit_names_exist_in_the_frontend` extended to `type`, and a new test that every
  class the part names is a selector in `design/tokens.css` or `design/components.css`); the part must give each
  class the family `design/tokens.json` gives it (`heading` is sans since decision 17) → the test reads the
  families from `tokens.json`.
- **Stop if:** a field the part describes renders differently from what step 2 says (then write what the code
  does and say so in the commit); `bt.theme.tokens.font` is not the chart font string in the frame.

1. `type.md`, about 60 lines, imperative, no prose beyond one line per rule. It opens with decision 18's rule,
   the one that decides every other line: **the family says who wrote the text**. Serif (`prose`, `caption`;
   `statement` never in blocks) only for sentences a person or an agent wrote, such as an explanation or a note
   shown in a block; sans (`body`, `small`, `number`, `heading`) for everything the block names, labels, counts
   or states: axis titles, ticks, legends, run, group and metric names, status and verdict words, numbers; mono
   (`code`) as an accent for keys, ids, paths and values as logged, never for a sentence. A name stays sans even
   when a person chose it. **Custom code**: never set a font
   family, size, the `font` shorthand or line height, in inline styles, d3 `.attr`/`.style`, SVG attributes or a
   `<style>`; put a type class on the element, the frame loads the app's stylesheet. A table, class → font →
   use: `body` (sans 15, the frame's default: controls, cells, facts); `heading` (sans 17 at 600: titles inside a block, only
   through `bt.ui.Section`); `small` (sans 12.5: axis ticks and labels,
   legends, table headers, meta, status words); `num` (tabular figures, no size: every number in a column or
   on an axis, with `small` or `body`); `number` (sans 24 bold: one headline value; prefer `bt.ui.Stat`); `prose`
   (serif 15.5: sentences inside a block); `caption` (serif italic 14: prefer the block's `caption`); `code`
   (mono 13: run ids, metric and config keys, paths, values as logged);
   `title` and `statement` never in blocks. SVG text: `class="small num"` for ticks, `class="small"` for axis
   titles, `fill="var(--muted)"`; downloads keep it (`snapshot.ts` copies the computed font). Canvas:
   `ctx.font = bt.theme.tokens.font`, the only font string code uses. Emphasis: bold (`<b>`) only for the one
   value that matters; no italic of your own (italic means proposed or live), no uppercase, no letter-spacing.
2. **Views**: `title` is plain text (one or two lowercase words become the section's label, in mono above the
   block or in its collapse toggle; longer ones are a sans `heading`); `caption` is plain text in the serif italic, a sentence, keys as logged without backticks;
   Markdown fields (`markdown` blocks, notes, memory) render `prose`: keys, ids and values in backticks
   (`code`), math as `$…$` (KaTeX), `##` at most, raw HTML shows as text. Verify each claim against the files in
   Read before writing it.
3. Register `type`: `TOPICS`, the `GuideParams.part` literal, `SKILLS["beamtime-views"]`, the overview row
   ``| `type` | which type class for which text in custom blocks and views |``, one line each in `kit.md`,
   `kit-api.md` Rules ("No font literals: a type class, or `bt.theme.tokens.font` on canvas; `guide type`"),
   `anti-patterns.md` (✓ "font sizes or families in custom code" → "a type class; `guide type`") and
   `checklist.md` (11: "Does all text use the app's type: no odd sizes or fonts?").
4. `code.py`: `FONT = re.compile(r"\bfont-(?:size|family)\b|\bfont(?:Size|Family)\b|\bline-?[hH]eight\b|\bfont\s*:(?!\s*bt\.theme\.tokens\.font\b)")`;
   in `problems`, on the comment-masked text before strings are masked (beside `COLOR`), report once:
   `(f"font literal {m.group(0)!r}", "put a type class on the element (small, body, caption, code; guide type); canvas uses bt.theme.tokens.font")`.
5. 05-views.md: the guide table gains the `type` row (~700 tokens); the anti-pattern row names the check.

## Z. Close

### Z31. Close (sonnet) — code

- **Touches:** `CHANGELOG.md` (0.3.0 section), `docs/guides/views.md` (sections, markers, color by, scale),
  `CLAUDE.md` (Layout: `ui/mark.ts`, favicon files) only if a line there became wrong.
- **Check:** the full checks; `cd web && npm ci && npm test && npm run build` (bundle current);
  `uv run pytest -q tests/serve/test_browser.py`; by hand the Goal's serve run.
- **Done:** the changelog lists the Breaking changes below; every Goal check passes; `ticket.py status` shows all done.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| Default chart scale | log for `*loss*` names, else linear | log when every value is positive and spans > 2 decades | set `scale:` in the view or the view's `metrics` |
| Sections | a one-metric prefix in Other; only `/` | own section; `.`/`_` after known prefixes | none; a viewer's open/closed state of moved sections resets |
| Seed merging | above 8 runs | some arm has ≥ 2 seeds | "each run" in the chart settings |
| Clocks | `epoch`, `global_step`, `trainer/global_step` | any metric whose leaf is a clock name | a view can still chart one by naming it |
| Sweep charts | one color per run | colored by the swept key | Color by → none |
| `keys` answer | `config.varying`, `aliases` | also `config.dropped` | additive |
| `series` meta | — | `running` | additive |
| `data` query and meta | — | `clock` param; meta `steps`, `clocks` | additive |
| `images` block | latest step, small tiles, no tools | a scrubber over every logged step, chart tools, an expand dialog with zoom | none; `step:` in a view is now where the scrubber starts |
| Favicon | mark with a dot when live | `///`, gathered when live | none |
| Page layout | Section labels in a left margin column | labels above the content, centered column, panels, rounded hover rows | custom blocks keep `var(--margin)` (unused by the app) |
| Look | warm paper, serif block titles, 6 px corners | cool neutrals, sans titles, 12 px corners, drawn controls | none; themes recolor through the same tokens |
| Custom code with font literals | saved | `view_validate` error `font literal …` | a type class (`guide type`); canvas `bt.theme.tokens.font` |

## Not verified

- That Chromium exists on the executing machine; browser-test steps are skipped otherwise (W31, W32, W35, W37, L32).
- That `ChartFrame` takes a non-chart child without changes to its line-chart callers (W37 Stop if), and that the
  viewer-state store of chart zoom can hold an images block's step (W37 reads it first).
- That clock values agree across runs at the same step often enough for one `clocks` value per step (Q32 Stop if).
- That uPlot calls the x scale's `range` again on `setData(…, true)` after a legend toggle (W32 checks first).
- That Chrome renders an SVG favicon's CSS base state (the gathered pose) and not the first keyframe (L31, by hand).
- Whether `npm ci` works offline on the executing machine.
- That no other reader depends on `compile.py` always emitting `scale` (D34 greps `props["scale"]` and `.scale` first).
- That `bt.theme.tokens.font` inside the frame is the chart font string (`Theme.font`, `web/src/bt/theme.ts` 13); T31 checks first.
- Whether library blocks (`block_save`) run `code.problems`; if not, T31's check reaches only view code (say so).
- Custom blocks in an exported page: the inline frame strips `@font-face` (`web/src/blocks/custom.ts` 217–218) and
  `--font-serif` is `XCharter` with no fallback, so serif classes there may render in the browser's default font.
  Out of scope for T31; see the question below.

- That the generated skills (`scripts/build-plugin`) are committed anywhere that S31 must regenerate.
- That exported pages and the headless renderer show the new look without changes (S31 checks by hand).

## Questions

1. Exported pages: should custom-block frames keep the fonts (inline them as data URIs, or give `--font-serif`
   a fallback), or is a system font acceptable in exports? Not planned yet.
