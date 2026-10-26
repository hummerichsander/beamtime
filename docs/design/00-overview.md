# Beamtime design overview

Beamtime is an agents-first experiment logger: runs are plain files, every experiment carries a
frozen proposal with checkable predictions, notes and a compressed memory form the research record,
and agents build the result views. This overview is the entry point to the design. It fixes the
canonical names that every layer uses, the scope of v1, and the cross-cutting rules.

## Layers

| # | Document | Covers |
|---|---|---|
| 1 | [01-storage.md](01-storage.md) | the file format: root, settings, folders, runs, write protocol |
| 2 | [02-sdk.md](02-sdk.md) | the Python SDK that writes runs, including PyTorch Lightning |
| 3 | [03-index.md](03-index.md) | the index cache and the query language |
| 4 | [04-remotes.md](04-remotes.md) | runs on other machines: remote queries, port forwarding, pulls |
| 5 | [05-views.md](05-views.md) | views: widgets, custom blocks, the kit, theme, library, agent guide |
| 6 | [06-server.md](06-server.md) | the self-hosted server (post-v1) |
| 7 | [07-web-ui.md](07-web-ui.md) | the web UI |
| 8 | [08-cli-mcp.md](08-cli-mcp.md) | the CLI and the MCP server, and the API both use |
| – | [09-research-record.md](09-research-record.md) | proposals, predictions, checks, notes, memory |

## Canonical names

| Thing | Name or format |
|---|---|
| project settings | `beamtime.yaml` in the root; user settings in `~/.config/beamtime/settings.yaml` |
| default log dir | `beamtime/` in the root |
| index cache | `~/.cache/beamtime/<root-hash>/` |
| run id | `YYYYMMDD-HHMMSS-<8 base32>`, e.g. `20261024-101532-k3m9xq2a` |
| version id of authored files | `YYYYMMDD-HHMMSS-<4 base32>`, e.g. `20261025-091200-x8k2`; the file is `<id>.<ext>` |
| machine-written files | start with `_`: `_run.json`, `_config.json`, `_run_card.json`, `_preview.json`, `_metrics.jsonl`, `_data.jsonl`, `_data/`, `_events.jsonl`, `_artifacts.jsonl`, `_output.log` (+ tail and rank files), `_env/` |
| authored folders (versioned) | `proposal/`, `notes/`, `view/`, `memory/`, `blocks/<name>/` |
| reserved names in a log dir | the authored folders above, every name starting with `_` or `.`, `artifacts/`, `checkpoints/` |
| schema version | a `schema` field in every JSON file and every YAML or frontmatter file |
| identity on authored files | `author` (person or model id) and `user` (the account) |
| remote folders | `@<source>/<path>`, e.g. `@cluster/scaling` |
| research status of a folder | `open`, `proposed`, `running`, `evaluable`, `concluded` |
| run status | `running`, `finished`, `failed`, `killed`; derived: `lost` |
| check outcomes | `pass`, `fail`, `inconclusive`, `insufficient`, `pending`; marked provisional until the plan is complete |
| verdicts | `confirmed`, `refuted`, `inconclusive` |
| note types | `observation`, `decision`, `idea`, `question`, `verdict` |
| CLI and MCP names | the MCP tool is the CLI command path with `_` for spaces: `beamtime note add` ↔ `note_add` |

## Scope

**v1** is the first release. **v1.1** follows it closely with features designed now. **Later**
means designed in outline, built when needed.

| Area | v1 | v1.1 | Later |
|---|---|---|---|
| Storage | the full file format | | |
| SDK | runs, data, card, preview, capture, resume by id, ranks, Lightning, notebooks | auto resume | other framework adapters, uploader |
| Index | metadata in SQLite, column files, one pure-Python read path, all query kinds | | smaller cache, precomputed levels, auto-started daemon |
| Remotes | remote queries over ssh (listings federated, aggregates per source), port forwarding with token, pulls | | |
| Research record | versioned proposals, plans, predictions `each` and `compare` with t-intervals, manual predictions, notes, links, folder status, memory | `trend` and `best` predictions | calibration from `confidence` |
| Views | YAML widgets (wave 1), `vega`, custom blocks on the kit, library and pinning, theme files, static validation plus one render | wave 2 widgets, linked selection, packages | migrations for block upgrades, VS Code theme import, high-contrast and print themes, community gallery, params |
| Web UI | the shell, URLs, SSE invalidation with refetch, HTML and figure export | | PDF export, rearrangeable panels |
| CLI and MCP | all commands and tools for v1 features, eight prompts, stdio MCP | | MCP over HTTP |
| Server | `author`/`user` on authored files, no network code in the SDK | | the server itself |

Wave 1 widgets: `line`, `scatter`, `bar`, `table`, `stat`, `images`, `text`, `data_table`,
`histogram`, `proposal`, `note`, `memory`, `folders`, `timeline`, `output`, `vega`, `custom`, and the
layout blocks `section`, `row`, `grid`, `tabs`. Wave 2: `importance`, `heatmap`, `parallel`,
`compare`, `repeat`, `facet`, baselines with matching, linked selection.

## Platform and dependencies

| Part | Python | Dependencies | Platforms |
|---|---|---|---|
| SDK (`import beamtime`) | 3.10+ | standard library and PyYAML; NumPy, Pillow, PyArrow, Matplotlib only when a data wrapper needs them | Linux, macOS, Windows |
| CLI (`beamtime`) | 3.11+ | PyYAML, msgspec | Linux, macOS (POSIX-first) |
| `beamtime[serve]` | 3.11+ | Starlette, uvicorn, the MCP SDK, Playwright (Chromium downloaded on first use) | Linux, macOS |

The SDK modules never import CLI or server modules, so the SDK can run in older training
environments. On Windows, the SDK captures output through a pipe, retries file replacements that a
reader blocks, and installs no SIGTERM handler.

## Cross-cutting rules

- **Files are the source of truth; every file has one writer.** Everything else is a cache.
- **Readers accept every schema version forever.** There is no migration command; old runs stay as
  they were written.
- **Agent writes are additive.** Agents never delete, install, configure, start servers or move runs;
  they give the user the command to enter.
- **Never break the training run.** The SDK never raises after `init` and never blocks the process.
- **One read path.** Every number is computed by one implementation, so the CLI, MCP and the UI
  never disagree.

## Testing strategy

- **Golden run folders** per schema version, checked in, as reader fixtures.
- **A synthetic log-dir generator** with planted effects (from the [evaluation harness](05-views.md#evaluation-harness))
  for fixtures, demos and the harness.
- **Property tests** for preview buckets and downsampling against exact recomputation.
- **Crash tests**: writers killed mid-line, mid-replace and mid-resume; readers and the index must
  recover.
- **Capture tests** in subprocesses: SIGTERM, SIGKILL, forked workers, a stalled log file.
- **A Lightning version matrix**, including signal-handler composition on SLURM requeue.
- **Budgets in CI**: CLI import time (about 150 ms for `beamtime runs`), web bundle size.

## Onboarding and documentation

- `beamtime init` sets up a project, `beamtime demo` generates a sample log dir and serves it, and
  `beamtime doctor` checks root and log dir resolution, write access, Chromium, and remote
  reachability.
- User documentation is separate from this design: a quickstart, a cluster recipe (`BEAMTIME_LOGDIR`,
  batch scripts, remotes), and a Lightning page. Agents use `beamtime guide`.
- An importer for TensorBoard event files is a strong adoption lever after v1.
