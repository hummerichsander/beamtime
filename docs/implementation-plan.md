# Implementation plan for v1

This plan turns the design in [docs/design/](design/00-overview.md) into a v1. It is ordered so that
something usable exists early and every later step can be tested against real experiments.

Estimates are in **full-time weeks with heavy use of coding agents**. For part-time work, divide by the
share of a week spent on Beamtime (2 days a week: multiply by about 2.5).

## Approach

1. **Vertical slices, early use.** After the first three milestones, Beamtime records real runs and
   answers questions in the CLI and through agents. From then on, using it in research decides what
   comes first.
2. **Tests first where bugs are subtle.** Output capture, the write protocol, attempts, statistics and
   the sandbox get their tests before their implementation. The synthetic log-dir generator is built
   first, because every later test needs data.
3. **One milestone, one spec.** Each milestone names the design sections it implements. Agents work from
   those sections; deviations are decided and written back into the design before the code lands.
4. **Agents in parallel only behind stable interfaces.** Parallel work starts once the operation set,
   the file format and the query answers are fixed (after M2). Parallel agents use separate worktrees,
   after asking.
5. **Every milestone ends usable.** Ruff, the tests and the CI budgets pass; the new capability works
   end to end, not only in unit tests.

## Package layout

```
src/beamtime/
  __init__.py      # SDK entry points (init, current, data wrappers); imports nothing else eagerly
  sdk/             # run, capture, env, data, files, paths, lightning      (Python 3.10, stdlib + PyYAML)
  format/          # file names, schema versions, readers for every file kind (Python 3.10, stdlib + PyYAML)
  index/           # SQLite store, column files, ingest, attempts, discovery, freshness
  query/           # msgspec query models, evaluation, downsampling, answers
  record/          # proposals, plans, predictions, statistics, checks, notes, links, memory, status
  views/           # view and block schemas, compilation, validation, guide content and examples
  ops/             # the operation set: one function per operation, shared by CLI, MCP and the API
  remote/          # stdio protocol, ssh client, federation, pull
  cli/             # argparse frontend, text formatting
  mcp/             # MCP server (low-level SDK API), prompts
  serve/           # Starlette app, API, SSE, renderer (Playwright), static files
  synth/           # synthetic log-dir generator with planted effects       (Python 3.10, stdlib + PyYAML)
web/               # TypeScript: shell, bt kit, built-in blocks, sandbox bridge; esbuild → serve/static
bench/             # benchmarks, query-form experiment, view evaluation harness
tests/             # unit, property, crash, capture, golden-group and end-to-end tests
```

- `sdk/`, `format/` and `synth/` never import from the other packages, so the SDK runs on Python 3.10
  in training environments. `format/` is shared: the SDK writes with it, the index reads with it.
- `ops/` is the single source of the operation set. CLI commands, MCP tools and API methods are thin
  adapters generated from or mapped onto it, so names and parameters cannot drift.

## Milestones

### M0: Foundations (0.5–1 week) — done

- Package layout above; `pyproject.toml` with the base install (PyYAML, msgspec) and the
  `beamtime[serve]` extra (Starlette, uvicorn, MCP SDK, Playwright).
- CI: ruff, pytest, an import-time budget for `beamtime runs` (about 150 ms), a Python 3.10 job for
  `sdk/` and `format/`, a Windows job for the SDK.
- `format/`: constants and readers for every file kind of [layer 1](design/01-storage.md), with
  `schema` handling.
- **The synthetic log-dir generator, version 0**: writes valid run folders with planted effects
  (sweeps, seeds, a diverging run, a killed run, logged tables and images), driven by a seed. It
  becomes the fixture source for everything after. It lives in `beamtime.synth`, since `beamtime demo`
  uses it, and computes card and preview exactly from whole series: the reference for M1's property
  tests.
- Golden run folders for schema 1, checked in.

*Done when*: CI runs on all jobs, the generator writes groups that `format/` reads back.

### M1: SDK (2–3 weeks) — implemented; the SLURM check is pending

Implements [layer 2](design/02-sdk.md). Everything below is in place and tested locally (Linux-style
POSIX on macOS, Python 3.10 and 3.11, Lightning 2.6); the run on a cluster with
`examples/slurm_toy.sh` and the SLURM requeue with Lightning remain to be checked.

- `init` with root and log dir resolution, ids and names, `_run.json` with `proposals` and `job_key`,
  `_config.json`, the run's proposal version, `_env/`.
- `log`, data wrappers, card and preview (constant memory, pairwise bucket merging), heartbeat by
  `os.utime`, `finish`, context manager, `current()`.
- Exit and signal handling with chaining; notebooks.
- **Output capture**: pipe, bounded buffer with drop markers, rotation, join timeout. Tests first:
  SIGTERM, SIGKILL, forked data-loader workers, a stalled log file, very fast output.
- Resume by id: attempts, rebuilding card and preview.
- Distributed: the rank-0 rule, `NullRun`, per-rank capture via `BEAMTIME_RUN_DIR` and `job_key`.
- `BeamtimeLogger` for Lightning, with a version matrix including SLURM requeue.
- Crash tests: a writer killed mid-line, mid-replace and mid-resume leaves readable groups.

*Done when*: a real training script, locally and on a cluster under SLURM, produces correct groups,
including a preempted and requeued job and a killed run that shows as `lost`.

### M2: Index and queries (1.5–2 weeks) — done

Implements [layer 3](design/03-index.md).

- SQLite metadata, column files with manifests, incremental ingest, attempt truncation, discovery by
  subtree with modification-time pruning, removal of vanished runs.
- The query language as msgspec models with helpful errors and numeric coercion; the kinds `keys`,
  `runs`, `series` (downsampling, `by`, `seeds`, `smooth`), `data`, `timeline`, `groups`, `file`.
  `importance` follows in v1.1.
- One pure-Python read path with `math.fsum`; property tests of downsampling and aggregates against
  exact recomputation; answers from previews where they suffice.
- Freshness: catch-up within a time budget, the `serve.lock` rule, freshness meta in every answer.
- Re-run the index benchmark on the generator's data to confirm the budgets.

*Done when*: queries over the generator's scale-M log dir meet the targets of layer 3.

Measured in `bench/index/RESULTS.md` (M2 section): every target is met except the 10k-run table
without a daemon (112 ms; 36 ms with the daemon), where the per-run freshness check dominates.

### M3: Operations, CLI and MCP (1–1.5 weeks) — done

Implements [layer 8](design/08-cli-mcp.md) for reading.

- `ops/` with the reading operations; the CLI with compact text output, `--json` and exit codes; MCP
  over stdio with the reading tools and token budgets.
- `init`, `mcp install`, `status`, `settings`, `doctor` (local checks), `reindex`, `mv`, `rm`, `gc`.
- Settings with user and project levels.

Not in M3, by design: the reading operations of the research record (`notes`, `proposal show`,
`check`, `memory show`) come with M4, `guide` with M6, `serve` and `demo` with M5. MCP ships the
`review`, `debug` and `compare` prompts.

**Milestone A1, after about 5–7 weeks: first use.** Runs are recorded in real research; an agent can
answer "how did last night's runs go?" through MCP.

### M4: Research record (1–1.5 weeks) — done

Implements [the research record](design/09-research-record.md). Can run in parallel with M5.

- Proposal versions, membership from `_run.json`, freezing and superseding, plans and progress.
- Predictions `each` and `compare`; t-intervals (Welch and paired) with t quantiles computed in pure
  Python (inverse regularized incomplete beta), tested against reference values.
- Checks with `insufficient`, `inconclusive` and provisional results; group status.
- Notes with types, typed fields, link resolution and backlinks; memory with staleness.
- The writing operations (`note add`, `proposal set`, `memory update`), the `proposal`, `verdict` and
  `memory` prompts.

*Done when*: a proposal written before a sweep is checked automatically as the sweep runs, and an agent
writes a verdict and updates the memory.

Checked by `tests/record/test_end_to_end.py`: a proposal saved with `proposal set` before any run, a
seeded sweep through the SDK in subprocesses, the check provisional after half the grid and final
after all of it, a verdict with the check snapshot, and a memory update that is no longer stale.

### M5: Web UI shell (2–2.5 weeks) — done

Implements [layer 7](design/07-web-ui.md) and the theme of [layer 5](design/05-views.md#theme). Can
start after M2.

- `serve` on Starlette: API routes for the operations, SSE notifications, static files, the token, the
  lock.
- The TypeScript frontend with esbuild: shell, group tree, frame, context drawer, status bar, URLs,
  command palette, keyboard navigation.
- Theme tokens, the default light and dark theme, theme files with `extends`, run colors.
- The `bt` kit core and the first widgets needed by the built-in default view: `line`, `table`,
  `stat`, `images`, `text`, `proposal`, `note`, `output`, `memory`.
- The built-in default view; live updates with in-place chart updates.
- The bundle-size budget in CI.

*Done when*: `beamtime serve` shows the group tree, the header and the default view of any group or
run, with every state in the URL, and running curves grow in place.

Checked by `tests/serve/test_browser.py` (a real `serve` and headless Chromium: navigation without
reloads, the proposal and its badges, a curve refetched after new metric lines) and the timing script
`bench/web/timing.py` (scale M: first view 135 ms, group to group 53 ms). The `groups` block came
early, for groups whose runs live in subgroups. Fixed on the way: runs whose streams a time budget
had deferred were never stream-indexed once they had ended.

**UI refactor after M5** (done): the folder/group rename across CLI, MCP, queries and docs (the
chart parameter `group` became `by`); a notebook-like look (warm "paper and ink blue" themes, a
serif for reading, larger type, symbols, whitespace instead of boxes); concise default views; uPlot
for every chart instead of Vega-Lite, with W&B-like interactions; Markdown with KaTeX for notes and
memory; editing written texts in place (new versions, never changed files). Checked by the extended
browser test (navigation by click, zoom, aggregation, hiding runs, opening and editing a note) and
`bench/web/timing.py` (scale M: first view about 140 ms, group to group 80 ms, hover 16 ms).

**Milestone A2, after about 9–11 weeks: the UI in daily use.**

### M6: Views (2–2.5 weeks)

Implements [layer 5](design/05-views.md) for authored views.

- The view format, inheritance, versions, drafts; compiling YAML widgets to queries and components.
- The remaining wave-1 widgets on uPlot: `scatter`, `bar`, `histogram`, `data_table`, `timeline`,
  `tabs` (there is no `vega` block; charts beyond the widgets are custom blocks).
- "Save as view" in the UI: the viewer's chart panels and settings become a new view version, with
  the local account as author.
- Static validation; the headless renderer as a client, `view render`, the single validation render
  with layout checks; graceful skip without Chromium.
- View history; the view operations and MCP tools; the `view` prompt.
- The agent guide with progressive disclosure and the five examples.

*Done when*: an agent builds a useful view of a real sweep through MCP within two screenshot rounds.

### M7: Custom blocks and the library (1.5–2 weeks)

- The sandboxed iframe, the `postMessage` bridge, declared queries with placeholders, `libs`,
  height handling, error panels.
- The kit API inside iframes; static files served without the token.
- Library blocks: definition, location, `promote`, `fork`, `validate`, `save`, generalization checks,
  pinning in `uses`, `outdated` and `upgrade`, `block export` and `import`.

*Done when*: the `custom` example works, is promoted to a library block, and a second view reuses it.

### M8: Remotes (1.5–2 weeks)

Implements [layer 4](design/04-remotes.md). Can run in parallel with M6 and M7 after M3.

- The stdio protocol (`hello`, operations, `subscribe`, `files`), the ssh client with reconnects, the
  remote's in-memory index and optional cache.
- Federation: listings merged with exact `limit`, aggregates per source.
- Remote writes; `pull` with incremental copies and snapshot status; port forwarding with the token.
- `doctor` checks for remotes. **Testing on at least one real cluster**, including a login node with
  two-factor authentication through `ControlMaster`.

*Done when*: the laptop's UI and an agent see local and cluster runs together, and a verdict note
written on the laptop lands on the cluster.

### M9: Export, evaluation and release (2–3 weeks)

- HTML export (custom blocks inlined for `file://`) and per-block figures, `--points`.
- The evaluation harness: tasks, scoring, the first runs; iterate on the guide and examples with it.
- `beamtime demo`; user documentation (quickstart, cluster recipe, Lightning page); the
  instruction-file snippet.
- Packaging: the wheel with the built frontend, release automation, PyPI.
- Timing budgets measured on the generator's data; fixes from daily use; a few outside testers.

**v1, after about 16–22 weeks.**

## Schedule

| Milestone | Weeks | Cumulative (full time) | Cumulative (2 days a week) |
|---|---|---|---|
| M0 Foundations | 0.5–1 | 1 | 2.5 |
| M1 SDK | 2–3 | 4 | 10 |
| M2 Index and queries | 1.5–2 | 6 | 15 |
| M3 Operations, CLI, MCP → **A1** | 1–1.5 | 7 | 18 |
| M4 Research record (parallel to M5) | 1–1.5 | – | – |
| M5 Web UI shell → **A2** | 2–2.5 | 10 | 25 |
| M6 Views | 2–2.5 | 12.5 | 31 |
| M7 Custom blocks and library | 1.5–2 | 14.5 | 36 |
| M8 Remotes (parallel to M6/M7) | 1.5–2 | – | – |
| M9 Export, evaluation, release → **v1** | 2–3 | 17.5 | 44 |

The critical path is M0 → M1 → M2 → M5 → M6 → M7 → M9. M4 and M8 run alongside; done sequentially, they
add about 3 weeks.

## Working with agents

For each milestone:

1. **Spec**: the agent reads the milestone and the design sections it names, and lists the open
   questions before coding. Decisions go back into the design documents.
2. **Tests first** for the invariants the design states (one writer, sorted steps, never blocking
   training, exact aggregates, frozen proposals).
3. **Implement** in small commits that each pass ruff and the tests.
4. **Review** with the code-review tooling, at high effort for capture, statistics, the sandbox and
   the protocol.
5. **Use it**: the milestone's "done when" is checked by hand on real data, not only by tests.

## Risks

| Risk | Mitigation |
|---|---|
| Output capture misbehaves on some cluster or framework | tests first in M1; test on a real cluster before A1; an escape hatch that restores the file descriptors |
| UI polish takes longer than planned ("seamless" is iterative) | the shell early (M5) and in daily use from A2; budgets measured, not guessed |
| Chromium unavailable where agents work | validation degrades to static checks; renders happen on the laptop |
| Remote access differs per cluster (2FA, policies, old Python) | `doctor`; pull as the fallback; Python 3.10 for the remote's SDK |
| Scope creep from wave 2 and "later" items | wave 2 waits for v1.1; new ideas go into the design's "Later" sections first |
| Agent-written code that passes tests but violates the design | the spec step and review against the design; invariants as tests |

## Decisions

- **t quantiles** are computed in pure Python (inverse regularized incomplete beta), tested against
  SciPy's values (M4).
- **License**: Apache 2.0 (`LICENSE`, and `license` in `pyproject.toml`).
- **Cluster for testing**: a SLURM cluster; M1 and M8 are tested there.

## Still to decide

- **Outside testers** for M9: who, and when to invite them.
