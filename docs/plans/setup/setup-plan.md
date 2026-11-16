# Setup: an interactive `beamtime setup`

Base commit `ebb5b27`, branch `main`. Proposed 2026-11-12, based on `docs/plans/setup/decisions.md` (the input),
the agreed mockup `docs/design/10-setup-mockup.html`, the spec `docs/design/10-setup.md` (approved 2026-11-12), the
`imported_from` and scoped-move additions to `docs/design/01-storage.md`, and the interview of 2026-11-12. It ships
in 0.3.0 with refactor 2. Behaviour changes are allowed; they are listed in [Breaking changes](#breaking-changes).
Updated 2026-11-15 at `fb352bd` (branch `setup`, F11 to W13 done) with the user's decisions 14 to 17 of
`decisions.md`: reconfiguring a current setup (W16), the rename to `beamtime setup` (N11) and a proposal word limit
(G14). Tickets marked done name `beamtime init`, as the command was then; from N11 on it is `beamtime setup`.

Run a ticket with `/run-ticket docs/plans/setup/setup-plan.md <ID>` in a fresh session; review tickets marked
`+ review` with `/review-ticket docs/plans/setup/setup-plan.md <ID>` on a stronger model.
`ticket.py status docs/plans/setup/setup-plan.md` shows what's done and what's next.

## Goal

The outcome this plan commits to, checked against at the end and in every review:

- **Done means:** `beamtime setup` (renamed from `init`, no alias) in a terminal runs the four flows of the mockup
  (first setup, teammate, cluster, update) and, in a current setup, reconfigures from the saved answers; each
  answer has a flag, nothing is written before the review is confirmed, and "Show the command" prints a
  `beamtime setup --yes ...` that makes the same plan. Without a terminal it asks nothing and writes only
  with `--yes`. The `cache` setting is resolved by one function for the CLI, `serve`, MCP and `serve --stdio`.
  `beamtime.yaml: agent` drives `beamtime guide` and a generated rules block. Agents get a portable MCP command for
  seven clients. Runs from TensorBoard, W&B offline, MLflow, CSV and other Beamtime log dirs import with
  `imported_from`. `setup --check` and `status` report a stale setup, and the `migrate` prompt hands notes and
  memory to an agent. `agent.proposal_words` reaches the guide, the wizard's form and a soft warning of
  `proposal set`.
- **Confirmed by:** the full checks and `uv run pytest -q -n0 tests/test_budgets.py`; `uv run pytest -q tests/setup`
  (scan fixtures, flags-equal-prompts per scenario, no-trace aborts, pty runs of the four flows, importer fixtures,
  `--check` against 0.1.1 and 0.2.0 setups, reconfiguring a current setup); `ticket.py status` shows every ticket
  done; `beamtime init` is an unknown command; by hand, `beamtime setup` in a scratch copy of a project reproduces
  the mockup's first-setup screens, and a second `beamtime setup` there opens the list of answers.
- **Out of scope:** reading another project's runs in place (a local-path source); calling a model from the
  wizard; importing TensorBoard images, histograms or text and MLflow artifacts; a pure-Python `.wandb` reader;
  Windows-specific polish beyond the `msvcrt` input path; publishing the release; `beamtime ps`/`stop` and reusing
  a running `serve` (planned separately).

## Findings

Evidence: **code** (read, not run; the ticket starts with a failing test); **reproduced** (run).

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | `beamtime init` asks nothing; writes `beamtime.yaml` and a `beamtime/` ignore line | `ops/admin.py:init` 40–72 | code | P11, P12, W11 |
| 2 | An MCP server started by a client can use another cache than the shell | `index/cache.py:cache_dir` 16 reads only `BEAMTIME_CACHE`/XDG; `serve --stdio` sets the env var itself (`serve/stdio.py` 133) | code | F11 |
| 3 | `mcp install` writes an absolute path into a project file shared by git | `admin.py:register` 692: `shutil.which("beamtime")` into `.cursor/mcp.json` | code | A11, A12 |
| 4 | The rules text is fixed and can't follow project settings | `guide/parts/instructions.md` read verbatim (`admin.py:instructions` 668) | code | G12 |
| 5 | Two rules texts exist across releases (0.1.0 = 0.1.1, 0.2.0 = 0.2.1 = HEAD) | `git show <tag>:src/beamtime/guide/parts/instructions.md` hashes | reproduced | G12 |
| 6 | The index cache doesn't know which log dir it indexes | `index/store.py` `meta` holds only `schema` (155) | code | F13 |
| 7 | Moves apply to every file in the log dir | `format/moves.py` `current` 57, `earlier` 43 | code | F14 |
| 8 | `init` in a set-up, current project answers "already set up" and asks nothing, so changing one answer means flags; a rules block whose `agent` settings were edited stays as written | `ops/admin.py:init` 76–94 (terminal branch only for `first`, `teammate`, `cluster`); `stale.py:stale_rules` 72 matches the current release | code | W16 |
| 9 | The command is `init`, which reads like the SDK's `beamtime.init()` | `ops/registry.py` op `init` 1152–1158; 109 lines outside the plans name it (N11's grep) | reproduced | N11 |
| 10 | No proposal length knob; agents write long proposals that freeze once a run records them | `settings.py` `PRESETS` 31, `AGENT_KEYS` 94; `ops/record.py:proposal_set` 246 warns only on unknown metrics | code | G14 |

## Brief

What the tickets build together, so a session doesn't rediscover the design:

- **Package** `src/beamtime/setup/` (new): `scan.py` (`Scan`, `scan(root)`), `plan.py` (`Answers`, `Change`,
  `plan()`, `command()`), `apply.py`, `flow.py`, `term.py`, `agents.py`, `remotes.py`, `sdk.py`, `stale.py`,
  `changes.py`, `importers/`. Nothing in it is imported at module level by `beamtime runs`; `ops/admin.py:init`
  imports it inside the function.
- **One path for flags and prompts**: prompts and flags both fill `Answers` (msgspec struct); `plan(scan,
  answers) -> list[Change]` is the only place that decides what is written; `apply(changes)` is the only writer.
  A `Change` has `where` (`project`, `machine`, `remote`, `import`), `label`, `before`, `after` and a zero-argument
  `run` callable; the review renders the list grouped by `where`.
- **Settings** (`settings.py`): `cache` (both levels), `agent` (project-only; `style` plus overrides; presets
  `careful`, `hands-on`, `analysis`), `remotes.<name>.enabled`; `Settings.remotes` (enabled remotes only) and
  `Settings.agent` (resolved knobs with provenance). `expand_path()` moves here from `serve/stdio.py:expand`.
- **Cache** (`index/cache.py`): `resolve_cache(logdir, settings) -> Cache(path, kind, refused)`; `network_fs`
  moves here; `cache_dir(logdir, settings=None)` returns `resolve_cache(...).path`.
- **Agents** (`setup/agents.py`): `CLIENTS` table (spec § Agent clients), `mcp_command(env, root, shared) ->
  list[str]`, `register(client, root, command) -> Change`; rules come from `guide/rules.py`
  (`render(agent) -> str`, `release_of(block) -> str | None`, `write_block(file, block)`).
- **Importers** (`setup/importers/`): each source module has `detect(path) -> Found | None` and `runs(path) ->
  Iterator[Imported]`; `write.py:write_run(logdir, dest, imported)` is the one writer, reusing
  `synth/summary.py:card_and_preview`; Beamtime log dirs copy through `beamtime.py` instead.
- **Names after N11**: the command and op are `setup` (`SetupParams`, `ops/admin.py:setup`, answer kind
  `setup`); `beamtime.init()` in the SDK and `flow.setup()` keep theirs. No `init` alias anywhere.
- **Reconfiguring** (W16): `Answers.saved(scan)` is what is set up; `plan(scan, Answers.saved(scan))` is empty
  except for a rules refresh; `flow.reconfigure()` asks only the picked step and the steps it newly enables.
- **Voice and output**: plain, no emoji, no exclamation marks; the wizard's strings are the mockup's
  (`docs/design/10-setup-mockup.html`, its `<script>`), which win over paraphrase.

Done, for every ticket: its Done line holds; its Check passes; the spec documents say what the code does; its heading
is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` (4 xdist workers; `-n0`
   serially). New tests live in `tests/setup/` with fixtures in `tests/setup/conftest.py`; every setup test points
   `HOME`, `XDG_CONFIG_HOME` and `XDG_CACHE_HOME` at `tmp_path` (a `home` fixture, added in S11) and never touches
   the real `~/.ssh`, `~/.codex` or `~/.claude`. Budgets: `uv run pytest -q -n0 tests/test_budgets.py` after any
   ticket that touches `cli/`, `settings.py`, `index/cache.py` or `ops/registry.py`.
2. Generated files: `docs/reference/cli.md` is generated by `uv run python docs/site/reference.py` and checked by
   `tests/test_docs.py`; rebuild and commit it in every ticket that changes CLI flags or command names (P11, A12,
   W13, N11). These tickets also all edit `ops/registry.py`, so they run one after another.
3. Rules: CLAUDE.md's Python style; `sdk/`, `format/` and `synth/` stay standard library plus PyYAML
   (`tests/test_boundaries.py`); the wizard uses only the standard library for terminal I/O; no module-level
   PyYAML, NumPy or `importlib.metadata` in modules `beamtime runs` loads. Never touch `tests/golden/schema1/`.
4. Spec: `docs/design/10-setup.md` (and `01-storage.md` for F14, I11, I15; `09-research-record.md` and
   `08-cli-mcp.md` for G14). A deviation is written back into the spec in the same commit.
5. Ticket budget: 140k tokens per ticket session; split a ticket that would exceed it.
6. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading. The hash stays in git (`ticket.py status`).

## Order

```
F11 ─ F12 ─┬─ G11
         ├─ G12 ─ A12 ─┐
F13, F14   │           │
T11       │           │
S11 ─ A11 ─┴───────────┤
I11 ─┬─ I12 I13 I14 I16   │       independent of each other
    └─ I15            │
G13                   │
S12 (after I11 F13 A12) ─┤
K11 (after S11) ───────┤
P11 (registry) ─ P12 ─ R11 ─ W11 ─ W12 ─ W13 (registry) ─ N11 (registry) ─ G14 ─ W14 ─ W15 ─ W16 ─ D11 ─ Z
```

What's left runs in this order: F11 F12 F13 F14 T11 S11 A11 G11 G12 G13 A12 I11 I12 I13 I14 I15 I16 S12 K11 P11 P12 R11 W11 W12 W13 N11 G14 W14 W15 W16 D11 Z

N11 runs first of what is left, so every later ticket is written and tested against `beamtime setup`. G14, W14, W15
and W16 all edit `setup/flow.py` (and W14, W16 the terminal branch of `ops/admin.py:setup`), so they run one after
another; W16 comes after W14 because both add a flow to `run()`. D11 documents all of it.

F11 and F12 both edit `settings.py`; P11, A12 and W13 edit `ops/registry.py` and regenerate `docs/reference/cli.md`. I12,
I13, I14 and I16 are independent of each other and of the G/A tickets.

## Decisions taken; say if you want otherwise

1. **Release** (your decision): the wizard ships in 0.3.0 with refactor 2; its changelog lines join the existing
   0.3.0 section. Rules history files are named `0.1.0.md` and `0.2.0.md`, and this release's text is the template.
   Rejected: releasing 0.3.0 first, because the mockup and the spec already speak of 0.3.0.
2. **W&B history** (your decision): read through the `wandb` package's datastore reader when it is importable;
   otherwise config and summary only, and the review says so. Rejected: a pure-Python `.wandb` reader (risky
   format) and an import extra (heavier install).
3. **Ticket budget** (your decision): 140k tokens.
4. **Disabled remotes are filtered in one place**: `Settings.remotes` returns enabled remotes; the call sites that
   read `settings.get("remotes")` switch to it, except `source list` and `beamtime settings`, which show all.
   Rejected: dropping disabled remotes inside `load()`, because `settings` must still show them.
5. **Scoped moves carry `within`** as an optional fourth field; `moves.read` returns `Move(old, new, within)`;
   `current` and `earlier` take `named_in: str | None` (the group path of the file that names the path) and apply
   a `within` move only when `named_in` is at or below it. User input resolves with `named_in=None`, so a typed
   `scaling` means the native group. Rejected: rewriting paths inside copied notes (they are immutable versions).
6. **TensorBoard decoding is pure Python** (TFRecord framing without CRC checks, a minimal protobuf varint reader
   for `Event` fields 1, 2, 5 and `Summary.Value` fields 1, 2, 8), so no `tensorboard` dependency. Rejected: the
   `tensorboard` package, a heavy optional dependency for a one-time import.
7. **Non-TTY `init` without `--yes` writes nothing** (spec § Answers, flags and settings). Existing tests that call
   `init` without a terminal pass `yes=True`.
8. **The clipboard** for "Copy the prompt" uses `pbcopy`, `wl-copy`, `xclip -selection clipboard` or `clip`,
   whichever is on `PATH`; without one, the prompt is printed. No new dependency.
9. **Imported run ids** use the source's start time and fresh random suffix (`format/ids.py`); Beamtime imports
   keep their ids. Deduplication is by `imported_from.path` plus `id`, looked up by walking `imported/` only.
10. **Conventions are the user's** (your decision, settled in the W11 review): setup neither detects nor asks for
    `main_metric`, `direction`, `seed_key` and `domain`; a set value has the source `project` and the guide labels it
    `beamtime.yaml`. The `detected` source kind and `settings.DETECTED_KEYS` are gone. D11 and the mockup say so.
11. **The update is planned in W13, shown in W14** (settled in the W13 review): `Scan.stale`, `Answers.defaults`
    (ticked items into `--update`, a `runs` item's folder into `--import`) and `Planner.updates()` make `init --yes`
    act on every ticked item, so `init --check` exits 0 after it. W14 adds only the screens: it renders `Scan.stale`
    plus `stale_remote()` after its probe, maps the ticks to `Answers.update` and `Answers.imports`, and plans
    through `plan()`. Rejected: leaving `--yes` without updates until W14, because W13's Done line needs it.

12. **The command is `beamtime setup`** (your decision, 2026-11-15): no `init` alias, before 0.3 ships; the op,
    its params (`SetupParams`), the answer kind, messages and docs follow. The SDK's `beamtime.init()` keeps its
    name. Rejected: keeping `init` as a hidden alias, because 0.3 is the release that changes setup anyway.
13. **Reconfigure a current setup** (your decision, 2026-11-15): on a terminal, the `current` flow opens the
    `Change an answer` list from `Answers.saved(scan)`; picking a step asks it and the later steps it newly enables
    (proposed detail), then the review; `Change an answer` returns to the list. A current-release rules block whose
    `agent` settings changed is planned there; `--check` and `status` stay quiet about it. Without a terminal
    nothing changes ("already set up"; `--update rules` rewrites the block). Rejected: reporting the mismatch in
    `--check` (the W13 review), because the release is current and the user edited the settings on purpose.
14. **`agent.proposal_words`** (your decision, 2026-11-15; name fitted to the `agent:` key): default 150 in every
    preset, `positive_int`. Counted (proposed) as the words of `statement`, `rationale` and every prediction's
    `description`. The guide's Defaults names it (left out when `research_record` is `off`) and the proposals
    part fills `{{agent.proposal_words}}`; `proposal set` adds a warning line and still writes; the wizard's form
    has a `proposal length` row (100, 150, 300 words). The rules block does not carry it. Rejected: refusing long
    proposals, because the knobs are guidance (spec § Agent settings).

## F. Foundations

### F11. One cache setting for every consumer (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/index/cache.py` (`cache_dir` 16; new `Cache`, `resolve_cache`, `network_fs`,
  `runtime_dir`), `src/beamtime/settings.py` (`DEFAULTS` 10, `read_level` 67; new `expand_path`),
  `src/beamtime/serve/stdio.py` (`run` 120–149, `expand` 152 and `network_fs` 162 moved), `src/beamtime/index/index.py`
  (`Index.__init__` 93–105), `src/beamtime/index/daemon.py` (`__init__` 19–45), `src/beamtime/serve/server.py`
  (`serve` 42–54), `src/beamtime/remote/via_serve.py` (`call` 37–40), `src/beamtime/remote/pull.py` (32–34),
  `src/beamtime/ops/admin.py` (`doctor` 207–215), `src/beamtime/serve/api.py` (`cache_info` 96);
  new `tests/index/test_cache.py`, `tests/serve/test_stdio.py`.
- **Read:** `docs/design/10-setup.md` § The cache; § Settings.
- **Check:** `uv run pytest -q tests/index tests/serve/test_stdio.py tests/remote tests/ops`; then the full checks
  and `uv run pytest -q -n0 tests/test_budgets.py`.
- **Done:** `cache: /tmp/{user}/bt` in a project resolves to `/tmp/<user>/bt/<hash>` for `Index`, `Daemon`,
  `serve`, `via_serve`, `pull` and `doctor`; a path whose `/proc/mounts` entry is `nfs` resolves to `kind="memory"`
  with `refused="nfs"`; `cache: memory` gives each `Index` its own temp dir, removed at `close()`; a `serve` with
  memory writes `serve.json` under `runtime_dir()` and `via_serve.call` finds it.
- **Risks:** `BEAMTIME_CACHE` still wins over the setting (`test_env_overrides_setting`); the built-in default on a
  network `$HOME` falls back to memory (`test_default_on_nfs_is_memory`); `serve --stdio` without `--cache` and
  without a setting stays memory (existing `test_hello_reads_and_errors`); two `Index` objects in one process with
  memory don't share a directory (`test_memory_is_per_process`).
- **Stop if:** a consumer has no `Settings` at hand and would need a new `load()` on the CLI hot path.

1. `settings.expand_path(path: str, user: str | None = None) -> str`: `{user}` (default `getpass.getuser()`),
   `${VAR}`, `~`; `stdio.expand` becomes an import of it.
2. `DEFAULTS["cache"] = None`; `read_level` accepts `cache` as `"memory"` or a string path at both levels.
3. `cache.network_fs(path) -> str | None` and `NETWORK_FS` move from `stdio.py` unchanged.
4. `Cache(path: Path, kind: Literal["disk", "memory"], refused: str | None, source: str)` (frozen dataclass);
   `resolve_cache(logdir, settings=None) -> Cache`: order `BEAMTIME_CACHE`, `settings.get("cache")`, XDG/`~/.cache`
   (`source` names which). Expand, then refuse network filesystems for memory. For memory, `path` is
   `runtime_dir(logdir)` = `<tempfile.gettempdir()>/beamtime-<os.getuid()>/<hash>` (mode 0700).
5. `Index(logdir, cache=None, settings=None)`: when the resolved cache is memory, index into
   `tempfile.mkdtemp(prefix="beamtime-index-")`, removed in `close()`; `serve.lock`, `serve.json` and the token stay
   in `Cache.path`. `Daemon` likewise.
6. `stdio.run(logdir, cache)`: `cache` from the argument, else the remote's own settings, else memory; it no longer
   sets `BEAMTIME_CACHE`; `CACHE` reports `resolve_cache`'s fields.
7. `cache_dir(logdir, settings=None) -> Path` stays, returning `resolve_cache(...).path`; the callers above pass
   `ctx.settings`. `doctor` prints the path, kind and `source`.

### F12. Agent settings and disabled remotes (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/settings.py` (`DEFAULTS` 10, `REMOTE_KEYS` 22, `PROJECT_ONLY` 23, `read_level` 67,
  `Settings` 35; new `AGENT_KEYS`, `PRESETS`, `AgentSettings`), `src/beamtime/ops/context.py` (83),
  `src/beamtime/ops/reading.py` (`status` 1066), `src/beamtime/serve/server.py` (195), `src/beamtime/views/render.py`
  (246), `src/beamtime/remote/__init__.py` (71), `src/beamtime/remote/sources.py` (`client_for` 100),
  `src/beamtime/ops/admin.py` (`doctor` 226); new `tests/test_settings.py`.
- **Read:** `docs/design/10-setup.md` § Agent settings; § Settings.
- **Check:** `uv run pytest -q tests/test_settings.py tests/remote tests/ops`; then the full checks.
- **Done:** `agent: {style: hands-on, seeds: 5}` resolves to hands-on's knobs with `seeds=5`, each knob's
  provenance `preset`, `project` or `default`; `agent` in the user file is a problem and ignored; an unknown knob
  or value is a problem and the preset value is used; a remote with `enabled: false` is absent from
  `Settings.remotes`, `status`, `serve`'s sources and routing, and present in `beamtime settings` and `source list`.
- **Risks:** `agent: {style: custom}` resolves from careful (`test_custom_starts_from_careful`); `significance: 1`
  is out of range (`test_agent_values_checked`); `enabled: false` in the user file over a project remote merges
  key by key (`test_disabled_project_remote`).

1. `PRESETS: dict[str, dict[str, Any]]` with exactly the spec's table; `AGENT_KEYS` maps each knob to its allowed
   values or a validator (`int >= 1`, `0 < float < 1`, `str`).
2. `PROJECT_ONLY = ("logdir", "agent")`; `REMOTE_KEYS` gains `enabled` (bool).
3. `AgentSettings` (frozen dataclass): `style`, every knob, `source: dict[str, Literal["default", "preset",
   "project", "detected"]]`; detected conventions (`main_metric`, `direction`, `seed_key`, `domain`) are `None` when
   unset and marked `detected` when set (the wizard only writes them from detection).
4. `Settings.agent -> AgentSettings` and `Settings.remotes -> dict[str, dict]` as properties; switch the listed call
   sites to `Settings.remotes`.

### F13. The cache knows its log dir (haiku) — code — **done**

- **Touches:** `src/beamtime/index/store.py` (`create` 144–155, `Store.__init__` 92), `src/beamtime/index/index.py`
  (`Index.__init__` 93), `src/beamtime/index/cache.py` (new `known_logdirs`), `tests/index/test_cache.py`.
- **Read:** `docs/design/10-setup.md` § The scan (the paragraph on other projects' log dirs).
- **Check:** `uv run pytest -q tests/index`; then the full checks.
- **Done:** opening an `Index` writes `meta('logdir', <resolved logdir>)` if missing or different; `known_logdirs(
  root=None) -> list[Path]` reads it from every `*/index.db` (or the file the store uses) under the disk cache
  root, skipping unreadable caches and log dirs that don't exist.
- **Risks:** a locked database (another process ingesting) is skipped, not waited on (`test_known_skips_locked`);
  `known_logdirs` never creates a cache directory (`test_known_reads_only`).

1. Write the key with `INSERT OR REPLACE` inside the schema transaction or on open; no schema version bump.
2. `known_logdirs` opens each database read-only (`file:...?mode=ro`, `uri=True`, timeout 0.1 s).

### F14. `imported_from` and scoped moves in the format (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/format/run.py` (`RunInfo` 26–48, `read_run_info` 51), `src/beamtime/format/moves.py`
  (`record` 16, `read` 25, `earlier` 43, `current` 57), `src/beamtime/query/resolve.py` (7, the `current` calls),
  `src/beamtime/record/proposals.py` (324), `tests/format/test_run.py`, new `tests/format/test_moves.py`.
- **Read:** `docs/design/01-storage.md` § `_run.json` (`imported_from` bullet), § Deleting and cleaning up (the
  `mv` bullet with `within`).
- **Check:** `uv run pytest -q tests/format tests/query tests/record`; then the full checks.
- **Done:** `RunInfo.imported_from` reads the field and is `None` for every golden run; `record(logdir, old, new,
  within=None)`; a `within` move maps `scaling` only for `named_in` at or below `within`; existing move tests pass
  unchanged.
- **Risks:** `within` equal to `named_in` counts as below (`test_within_is_inclusive`); a `within` move never
  applies to user input (`test_typed_path_is_native`); golden fixtures still read byte-exact (`tests/format`).
- **Stop if:** a reader of moves has no way to know which file named the path.

1. `RunInfo.imported_from: dict[str, Any] | None = None`.
2. `Move(old: str, new: str, within: str | None)` (named tuple); `read()` returns `list[Move]`.
3. `current(logdir, rel, named_in=None)` and `earlier(logdir, rel, named_in=None)` skip a move with `within` unless
   `named_in` is under it. `proposals.py:324` passes the run's group; `resolve.py` passes `None`.

## T. Terminal

### T11. Prompt primitives (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/setup/__init__.py`, new `src/beamtime/setup/term.py`, new
  `tests/setup/__init__.py`, new `tests/setup/test_term.py`.
- **Read:** `docs/design/10-setup.md` § The terminal; the mockup's `<script>` (`ln`, `rl`, `ok`, `fact` and the
  multi-select footer) for layout.
- **Check:** `uv run pytest -q tests/setup/test_term.py`; then the full checks.
- **Done:** in a `pty`, scripted keys drive `select`, `multi` (with an `+ Add` row whose check rejects a value and
  accepts another), `text`, `form` and `task`, and the returned values match; the numbered fallback works over a
  pipe; ctrl-c raises `Aborted` and the terminal's `termios` attributes equal those before the call.
- **Risks:** Enter on an unticked row ticks it and confirms (`test_enter_on_unticked`); `NO_COLOR` drops every
  escape (`test_no_color`); a terminal narrower than a hint truncates, never wraps the rail (`test_narrow`).

1. `class Term` (keyword-only: `inp`, `out`, `color: bool`, `raw: bool`) with `select(title, options, default,
   hint=None, body=()) -> str`, `multi(title, options, default, add=None) -> list[str]`, `text(title, default,
   hint=None) -> str`, `form(title, rows, default) -> dict[str, str]`, `task(title) -> TaskLines` (a context
   manager with `line(text)`), `say(lines)`, `collapse(title, summary)`.
2. `Option(value, label, hint=None, exclusive=False)`; `Add(label, prompt, check: Callable[[str], Option |
   str])` where a `str` is the error shown in place.
3. Raw input via `termios`/`tty` (POSIX) or `msvcrt` (Windows) behind one `keys()` generator yielding `up`, `down`,
   `space`, `enter`, `digit:<n>`, `char:<c>`, `ctrl-c`; `raw=False` reads lines (`2`, `1,3`, empty = default).
4. Colors: a small ANSI map for the mockup's span classes (`m` muted, `c` code, `g` good, `w` warn, `b` bad, `a`
   accent, `t` title); off when `color=False`.

## S. Scan

### S11. Scan: project, git, Python, code, disks, ssh (sonnet) — code — **done**

- **Touches:** new `src/beamtime/setup/scan.py`, new `tests/setup/conftest.py` (fixtures `home`, `project_tree`),
  new `tests/setup/test_scan.py`.
- **Read:** `docs/design/10-setup.md` § The scan; § The flow (which facts pick the flow).
- **Check:** `uv run pytest -q tests/setup/test_scan.py`; then the full checks.
- **Done:** on fixture trees, `scan(root, home=...)` reports: `project` (settings present, log dir counts), `git`
  (branch, clean), `env` (`PythonEnv(tool, path, python, beamtime_version, has_serve)` for a uv project, a pip
  `.venv`, a conda env from `CONDA_PREFIX`, none), `framework`, `job_scripts` with named hosts, `ssh_hosts` (with
  an `Include`), `disks` (from a fixture `/proc/mounts` path), `scheduler`, `display`, and `flow` (`first`,
  `teammate`, `cluster`, `update`) per the spec's table; it runs in under a second on a 2,000-file tree.
- **Risks:** `beamtime-*.dist-info` read from `site-packages` without importing (`test_env_version_without_import`);
  wildcard `Host *` entries are skipped (`test_ssh_wildcards`); a project with a log dir but no `beamtime.yaml` is
  `update`, not `first` (`test_flow_logdir_only`).

1. `scan(root: Path, *, home: Path | None = None, mounts: Path = Path("/proc/mounts"), env: Mapping[str, str] |
   None = None) -> Scan`; every reader is a small function returning a dataclass; nothing runs ssh or the network.
2. Walk depth: 2 for code and job scripts, 3 for past work (S12); skip `SKIP` from `ops/admin.py` plus `.git`.
3. `Scan.flow` is computed after S12's agent facts exist; until then teammate detection uses only project remotes
   missing from the user settings.

### S12. Scan: agents, rules, conflicts, past work, stale (sonnet) — code — **done**

- **Touches:** `src/beamtime/setup/scan.py`, `tests/setup/test_scan.py`, `tests/setup/conftest.py`.
- **Read:** `docs/design/10-setup.md` § The scan; § Agent clients; § Notes and memory files.
- **Check:** `uv run pytest -q tests/setup`; then the full checks.
- **Done:** `Scan.agents` lists each client of `agents.CLIENTS` found (project files or command on `PATH`), with
  its rules file and `guide.rules.release_of` of its block; `Scan.conflicts` lists `(file, line, text)` for the
  pattern list; `Scan.past` lists `importers.detect` results under the root (depth 3, outside the log dir) and
  from `cache.known_logdirs()` (marked `other=True`); notes and memory files, including Claude Code's project
  memory at `<home>/.claude/projects/<root with / and . as ->/memory/`.
- **Risks:** the project's own log dir is never offered as past work (`test_own_logdir_not_offered`); a conflict
  line inside the beamtime markers is ignored (`test_conflict_outside_block`).
- **Stop if:** Claude Code's project-dir escaping doesn't match a real `~/.claude/projects` name on this machine.

1. Conflict patterns (case-insensitive, one compiled regex): `NOTES\.md`, `results? (go|belong|are kept) in`,
   `experiment log`, `keep (notes|results) in`, `lab notebook`.
2. `Scan.stale` stays empty here; W13 fills it.

## A. Agents and MCP

### A11. The portable MCP command (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/setup/agents.py` (`mcp_command`, `check_command`), `src/beamtime/cli/__init__.py`
  (`Version` 152–163), `tests/test_cli.py` (`test_version` 10), new `tests/setup/test_agents.py`.
- **Read:** `docs/design/10-setup.md` § The MCP command.
- **Check:** `uv run pytest -q tests/setup/test_agents.py tests/test_cli.py`; `uv run pytest -q -n0
  tests/test_budgets.py`; then the full checks.
- **Done:** for each `PythonEnv` kind of S11 and a tool install on a fake `PATH`, `mcp_command(env, root,
  shared=True)` returns the spec table's command, and never an absolute path when `shared`; `beamtime --version`
  prints `beamtime <v> (no serve extra)` when `importlib.util.find_spec("mcp")` is `None`.
- **Risks:** a project on Python 3.10 can't host the MCP server and falls through to the tool install
  (`test_py310_project_falls_through`); a conda env without the serve extra falls through (`test_conda_no_serve`);
  only a pip venv in a shared file returns `None` so the caller picks machine scope (`test_venv_not_shared`);
  `--version` stays within the CLI budget.

1. `mcp_command(env: PythonEnv | None, root: Path, *, shared: bool, which=shutil.which) -> list[str] | None`, the
   spec's order; `--root` is added by `register` (A12), not here.
2. `check_command(cmd: list[str]) -> tuple[str | None, bool]`: runs `cmd[:-1] + ["--version"]` style probe with a
   5 s timeout and parses version and serve extra.

### A12. Clients, registration and the rules block (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/setup/agents.py` (new `CLIENTS`, `Client`, `register`, `rules_change`),
  `src/beamtime/ops/admin.py` (`mcp_install` 630, `instruction_file` 656, `instructions` 668, `register` 692 moved
  out), `src/beamtime/ops/registry.py` (`McpInstallParams` 600), `docs/reference/cli.md` (regenerated),
  `tests/ops/test_ops.py` (`test_mcp_install_for_cursor` 306, `test_instructions_block` 394),
  `tests/setup/test_agents.py`.
- **Read:** `docs/design/10-setup.md` § Agent clients; § The MCP command (the root bullet); § The rules block.
- **Check:** `uv run pytest -q tests/setup tests/ops tests/test_docs.py`; then the full checks.
- **Done:** `register(client, root, env)` returns a `Change` that writes each client's config as data, keeping other
  servers; Claude Code, Cursor and VS Code use machine scope when the command isn't portable; Codex and Windsurf get
  `--root <abs>`; "Another agent" returns the JSON to print; `beamtime mcp install --client <any of 7>` works through
  the same code and `--instructions` writes the generated block (G12) into `CLAUDE.md`, `GEMINI.md` or `AGENTS.md`.
- **Risks:** an existing `.mcp.json` with other servers keeps them (`test_mcp_json_merges`); Codex's TOML table is
  replaced, not duplicated (`test_codex_table_replaced`); invalid JSON in a client file is an error naming the
  file, never overwritten (`test_bad_client_json`).
- **Stop if:** a client's documented config format differs from the spec's table; write it back into the spec.

1. `Client(name, label, config: str, key: str, shared: bool, rules: str, start: list[str] | None, skills: bool)`;
   `CLIENTS` in the spec's order, plus `other`.
2. `McpInstallParams.client` becomes a `Literal` of the seven names.

## G. Guide and prompts

### G11. The guide reads the agent settings (sonnet) — code — **done**

- **Touches:** `src/beamtime/guide/__init__.py` (`guide` 53, `read` 75), `src/beamtime/guide/parts/overview.md`
  (`## Defaults` 97–104), `src/beamtime/guide/parts/proposals.md`, `predictions.md`, `memory.md`,
  `src/beamtime/ops/record.py` (353, budget), `src/beamtime/record/memory.py` (`BUDGET_CHARS` 14),
  `tests/guide/test_guide.py`.
- **Read:** `docs/design/10-setup.md` § How `beamtime guide` reads them; § Agent settings (guidance bullet).
- **Check:** `uv run pytest -q tests/guide tests/record tests/mcp`; then the full checks.
- **Done:** `guide` in a project without `agent` prints the Defaults section with every line marked `(default)` and
  the same rules as today; with `agent: {style: hands-on, seeds: 5}` it says "You may launch runs." and "5 seeds";
  `{{agent.*}}` never appears in any part's output; `memory update` warns at `memory_tokens * 4` characters.
- **Risks:** a remote group's guide reads the remote's settings (`test_guide_remote_settings`, through the
  existing remote fixture); detected values absent → their line is left out (`test_no_conventions`).

1. `defaults(agent: AgentSettings) -> str` renders the section; `read(name, agent)` replaces `{{agent.<key>}}`.

### G12. The rules template, history and matching (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/guide/rules.py`, new `src/beamtime/guide/rules/rules.md`, new
  `src/beamtime/guide/rules/history/0.1.0.md`, `0.2.0.md`, `src/beamtime/guide/parts/instructions.md` (removed),
  new `tests/guide/test_rules.py`.
- **Read:** `docs/design/10-setup.md` § The rules block; § Updating an older setup (the release bullet).
- **Check:** `uv run pytest -q tests/guide`; then the full checks.
- **Done:** `render(agent, user_only)` gives the spec's block for each preset; `release_of(text)` returns `0.1.1`
  for the v0.1.0 text, `0.2.1` for the v0.2.0 text, the current version for a fresh render with any settings, and
  `None` for an edited block; `write_block(file, block)` keeps text outside the markers byte for byte.
- **Risks:** a placeholder value containing regex characters (`val/loss`) still matches (`test_match_escapes`);
  CRLF files (`test_crlf_block`).

1. History files are copied verbatim from the tags: `git show v0.1.0:src/beamtime/guide/parts/instructions.md`
   and `git show v0.2.0:...`. `RELEASES = {"0.1.0.md": "0.1.1", "0.2.0.md": "0.2.1"}` names the newest release
   that wrote each text.
2. `release_of` turns each template into a regex (`{{...}}` → `.+?`, everything else `re.escape`d, whitespace
   runs → `\s+`) and returns the newest match.
3. `write_block` and the markers move here from `ops/admin.py`; `instructions` there becomes a thin call.

### G13. The `migrate` prompt (haiku) — code — **done**

- **Touches:** `src/beamtime/mcp/server.py` (`PROMPTS` 108, `get_prompt` 274–290), `tests/mcp/test_server.py`
  (`test_record_writes_and_prompts` 141).
- **Read:** `docs/design/10-setup.md` § The `migrate` prompt.
- **Check:** `uv run pytest -q tests/mcp`; then the full checks.
- **Done:** `migrate` is listed with arguments `paths` (required) and `conflict` (optional); its text names
  `guide notes`, `guide memory`, `note_add`, `memory_update`, the diff-before-edit rule and "never delete or change
  the source files"; nine prompts in total.

### G14. A proposal word limit (sonnet) — code — **done**

- **Touches:** `src/beamtime/settings.py` (`PRESETS` 31–66, `AGENT_KEYS` 94–108, `AgentSettings` 137–155),
  `src/beamtime/record/proposals.py` (new `words`), `src/beamtime/ops/record.py` (`proposal_set` 246–273),
  `src/beamtime/guide/__init__.py` (`defaults` 120), `src/beamtime/guide/parts/proposals.md` (§ Write one before
  launching), `src/beamtime/setup/flow.py` (`TUNE` 43–59), `tests/test_settings.py` (`test_presets_table` 32),
  `tests/guide/test_guide.py`, `tests/record/test_writes.py`, `tests/setup/test_flow.py`.
- **Read:** `docs/design/10-setup.md` § Agent settings (the `proposal_words` row and bullet), § How `beamtime guide`
  reads them; `docs/design/09-research-record.md` § Proposals (first paragraphs); decision 14.
- **Check:** `uv run pytest -q tests/test_settings.py tests/guide tests/record tests/setup/test_flow.py tests/mcp`;
  then the full checks.
- **Done:** every preset resolves `proposal_words == 150`; `agent: {proposal_words: 80}` resolves to 80 with source
  `project` and `proposal_words: 0` is a settings problem; `guide` prints "Keep a proposal near 150 words: statement,
  rationale and prediction descriptions. (default)" and leaves it out for `analysis`; `guide proposals` names the
  limit; `proposal set` with a 200-word statement under `proposal_words: 150` writes the version and its answer has
  the spec's warning line; at 150 words or fewer there is none; the wizard's `Agent settings` form has a
  `proposal length` row and `--agent-set proposal_words=300` plans `agent.proposal_words: 300`.
- **Risks:** prediction names, `where` filters and numbers don't count (`test_proposal_words_prose_only`); a
  proposal without `rationale` or descriptions counts the statement alone (`test_proposal_words_statement_only`); a
  remote group's `proposal set` warns from the remote's settings, as `memory update` does (through `ctx.settings`);
  the pty form scripts of `test_flow.py` still reach the review with one more row (`test_tune_form`).

1. `PRESETS[*]["proposal_words"] = 150`; `AGENT_KEYS["proposal_words"] = positive_int` (before the conventions);
   `AgentSettings.proposal_words: int`.
2. `proposals.words(p: Proposal) -> int`: `len(" ".join(texts).split())` over `statement`, `rationale` and each
   prediction's `description`, skipping `None`.
3. `proposal_set`: after `metric_warnings`, append the spec's warning when `words(proposal) >
   ctx.settings.agent.proposal_words`; the write happens either way.
4. `defaults()`: the line after the record line, keys `["proposal_words"]`, left out when `research_record ==
   "off"`; `proposals.md` gains one sentence with `{{agent.proposal_words}}`.
5. `TUNE["proposal_words"] = ("proposal length", [("100 words", "100"), ("150 words", "150"), ("300 words",
   "300")])`, after `significance`.

## I. Importers

### I11. Importer interface, run writer, CSV (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/setup/importers/__init__.py` (`Found`, `Imported`, `detect`), new
  `src/beamtime/setup/importers/write.py`, new `src/beamtime/setup/importers/csv.py`, new
  `tests/setup/test_importers.py`, new fixtures in new `tests/setup/fixtures/csv/`.
- **Read:** `docs/design/10-setup.md` § Importers; `docs/design/01-storage.md` § `_run.json` (`imported_from`).
- **Check:** `uv run pytest -q tests/setup/test_importers.py tests/format`; then the full checks.
- **Done:** importing a CSV makes a run under `imported/<stem>/` that `runs`, `card` and `series` answer like a
  synth run; `_run.json` has `imported_from` with `kind: csv` and the absolute path; a second import adds nothing;
  `detect(path)` returns a `Found(kind, path, n, label)` for each of the five kinds (stub detectors for the kinds
  I12–I15 fill in, matching file names only).
- **Risks:** a CSV without a step column uses the row index (`test_csv_no_step`); non-numeric columns are skipped
  (`test_csv_text_columns`); a crash mid-write leaves no `_run.json` (write it last, `test_partial_import`).

1. `Imported(name, created_at, ended_at, status, config, rows: Iterable[dict], host, git, command, source_id)`.
2. `write_run(logdir, dest_group, imported, provenance) -> Path`: metrics, config, card and preview via
   `synth/summary.py:card_and_preview`, then `_run.json` last with `src/beamtime/format/io.py` replace.

### I12. MLflow (sonnet) — code — **done**

- **Touches:** new `src/beamtime/setup/importers/mlflow.py`, the file-store fixture in new `tests/setup/fixtures/mlruns/`
  (plain text, committed) and an `mlflow.db` built in `tmp_path` by the test with `sqlite3`,
  `tests/setup/test_importers.py`.
- **Read:** `docs/design/10-setup.md` § Importers (MLflow row).
- **Check:** `uv run pytest -q tests/setup/test_importers.py`.
- **Done:** both stores import with params as config, metrics with their steps, status mapped (`FINISHED` →
  finished, `FAILED` → failed, `KILLED` → killed), the git commit from `mlflow.source.git.commit`, runs grouped by
  experiment name.
- **Risks:** a metric logged twice at one step keeps both lines in order (`test_mlflow_duplicate_step`); deleted
  runs (`lifecycle_stage: deleted`) are skipped (`test_mlflow_deleted`).

### I13. TensorBoard (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/setup/importers/tensorboard.py`, fixtures in new `tests/setup/fixtures/tb/` (event files
  written by a tiny encoder in the test), `tests/setup/test_importers.py`.
- **Read:** `docs/design/10-setup.md` § Importers (TensorBoard row); decision 6.
- **Check:** `uv run pytest -q tests/setup/test_importers.py`.
- **Done:** scalars written as `simple_value` and as scalar tensors (dtype float32/float64) import with their steps
  and wall times; `hparams.yaml` beside the events becomes config; Lightning's `version_<n>/` folders become runs
  under `imported/<name>/version_<n>`; non-scalar summaries are counted and named in the answer.
- **Risks:** a truncated last record ends the stream quietly (`test_tb_truncated`); several event files in one run
  directory merge by step (`test_tb_multiple_files`).

### I14. W&B offline (sonnet) — code — **done**

- **Touches:** new `src/beamtime/setup/importers/wandb.py`, fixtures in new `tests/setup/fixtures/wandb/`,
  `tests/setup/test_importers.py`.
- **Read:** `docs/design/10-setup.md` § Importers (W&B row); decision 2.
- **Check:** `uv run pytest -q tests/setup/test_importers.py`.
- **Done:** without `wandb` installed, config, metadata (host, git, command) and the summary import as a one-step
  run and `Found.note` says "history needs the wandb package"; with `wandb` (monkeypatched reader) the history rows
  import; status from `wandb-summary.json`'s exit code when present.
- **Stop if:** the datastore reader's import path differs across wandb versions; record the path used in the spec.

### I15. Beamtime log dirs (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/setup/importers/beamtime.py`, `src/beamtime/ops/copy.py` (reuse `sync_tree` 129;
  no behaviour change), `tests/setup/test_importers.py`.
- **Read:** `docs/design/10-setup.md` § Beamtime log dirs; `docs/design/01-storage.md` § `_run.json`, the `mv`
  bullet; decision 5.
- **Check:** `uv run pytest -q tests/setup tests/record tests/query`; then the full checks.
- **Done:** a synth log dir imported under `imported/demo` answers `groups`, `check`, `notes` and `memory_show`
  with the same verdicts and statuses as the original; ids unchanged; `_moves.jsonl` has one `within` move per
  top-level group; a native group with the same name is untouched; a second import skips every run.
- **Risks:** the source's own `_moves.jsonl` (`test_import_carries_moves`); a run id already present
  (`test_import_skips_known_ids`); `blocks/` at the source root reach views in the imported tree
  (`test_import_library_blocks`).

### I16. Notes and memory as written (haiku) — code — **done**

- **Touches:** new `src/beamtime/setup/importers/notes.py`, `tests/setup/test_importers.py`.
- **Read:** `docs/design/10-setup.md` § Notes and memory files.
- **Check:** `uv run pytest -q tests/setup/test_importers.py`.
- **Done:** each `.md` file (or each file of a folder) becomes one `observation` note on the log dir through the
  record's note writer, description the first heading or file name, author the local account; binary files are
  skipped and named.

## K. SDK

### K11. Adding the SDK with the project's tool (sonnet) — code — **done**

- **Touches:** new `src/beamtime/setup/sdk.py`, new `tests/setup/test_sdk.py`.
- **Read:** `docs/design/10-setup.md` § Git and the SDK (SDK paragraph); § The MCP command (dev group bullet).
- **Check:** `uv run pytest -q tests/setup/test_sdk.py`.
- **Done:** `sdk_change(env, version, mcp_from_env) -> Change | None` gives the commands of the spec per tool (uv
  with the dev group when the MCP command uses the project env, poetry, conda, pip with a `requirements.txt` line),
  as argument lists run with `subprocess.run(check=True)`; an env older than Python 3.10 returns `None` with the
  reason; tests check the commands, not their execution.

## P. Plan and apply

### P11. `Answers`, the flags and the command (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/setup/plan.py` (`Answers`, `command`), `src/beamtime/ops/registry.py`
  (`InitParams` 495–499, the `init` op 1062–1070), `src/beamtime/cli/__init__.py` (only if repeatable flags need
  it), `docs/reference/cli.md` (regenerated), new `tests/setup/test_plan.py`.
- **Read:** `docs/design/10-setup.md` § Answers, flags and settings.
- **Check:** `uv run pytest -q tests/setup tests/ops/test_params.py tests/test_docs.py`; `uv run pytest -q -n0
  tests/test_budgets.py`; then the full checks.
- **Done:** every flag of the spec's table parses into `InitParams`; `Answers.from_params(p, scan)` fills defaults
  from the scan; `command(answers, scan)` prints `beamtime init --yes` plus only the flags that differ from the
  scan's defaults, and parsing that command gives equal `Answers` for each scenario fixture.
- **Risks:** `--remote lab-gpu=jdoe@host` vs `--remote juwels:'${SCRATCH}/x'` vs `--remote a=u@h:/p`
  (`test_remote_grammar`); paths with spaces are quoted with `shlex.quote` (`test_command_quotes`).

1. `InitParams` gains the spec's flags; repeatables are `list[str]`; `--logdir` keeps its meaning;
   `--instructions` stays as a hidden alias that sets `rules=True`.
2. `Answers` (msgspec, kw_only) mirrors the flags with parsed types (`Remote(name, host, path)`).

### P12. `plan()` and `apply()` for the project and this machine (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/setup/plan.py` (`Change`, `plan`), new `src/beamtime/setup/apply.py`,
  `src/beamtime/ops/admin.py` (`init` 40–72), `src/beamtime/settings.py` (`write_key` 193 reused; new
  `write_agent`), `tests/ops/test_ops.py` (`test_init_is_idempotent` 196, 414), `tests/setup/test_plan.py`.
- **Read:** `docs/design/10-setup.md` § Answers, flags and settings; § Settings; § Git and the SDK; § The flow
  (review and apply steps).
- **Check:** `uv run pytest -q tests/setup tests/ops`; then the full checks.
- **Done:** with `--yes` and no terminal, `init` writes `beamtime.yaml` (`logdir`, `agent`, remote paths), the user
  settings (`cache`, remote host and command, `enabled: false`), the log dir link and its `.git/info/exclude` line,
  the marked `.gitignore` block for `record` and `none`, agent registrations and rules (A12), imports (I11–I16) and the
  SDK (K11); without `--yes` and no terminal it prints the review and the command and changes
  nothing; a failing change stops the apply and the answer names what was done.
- **Risks:** an existing `beamtime/` line in `.gitignore` is replaced by the block (`test_gitignore_upgrade`); a
  rerun writes nothing new (`test_init_is_idempotent`); defaults are not written (`test_defaults_not_written`);
  every abort before apply leaves the tree and home byte-identical (`test_no_trace`, hashing both trees).

1. `Change(where, label, before, after, run)`; `plan(scan, answers) -> list[Change]`, ordered project, machine,
   agents, imports, remote (R11 adds remote ones).
2. `apply(changes, say) -> list[Change]` returns the changes done; on an exception it raises `ApplyError(done,
   failed, error)`.
3. `ops/admin.py:init` builds `Answers`, then `flow.run` (W11) on a terminal without `--yes`, else plan and apply.

## R. Remotes

### R11. Probe, install and ssh sharing (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/setup/remotes.py`, `src/beamtime/setup/plan.py` (remote changes),
  `src/beamtime/ops/admin.py` (`probe_command` 311 moved, `source_add` 340 calls it), new
  `tests/setup/test_remotes.py`, `tests/remote/test_docker.py` (one probe and install test).
- **Read:** `docs/design/10-setup.md` § Remotes; `docs/design/04-remotes.md` § Configuration.
- **Check:** `uv run pytest -q tests/setup/test_remotes.py tests/remote`; `BEAMTIME_DOCKER=1 uv run pytest -q
  tests/remote/test_docker.py` where Docker runs; then the full checks.
- **Done:** `probe(hosts, paths) -> dict[str, Probe]` runs one ssh per host in parallel (threads), with a faked
  `ssh` script in tests reporting `ok`, `needs_code`, `unknown_host`, `no_beamtime` and `old_python`; the install
  and ssh-share changes appear in the plan only when asked, the ssh block is appended once and marked; `ssh -fN`
  runs attached to the terminal.
- **Risks:** an existing marked block for the host is not duplicated (`test_ssh_block_once`); a 30 s timeout per
  host never blocks the others (`test_probe_timeout`); `pip install --user` pins this version
  (`test_install_pins_version`).

## W. Wizard

### W11. The flow engine and the first setup (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/setup/flow.py`, `src/beamtime/ops/admin.py` (`init`), new
  `tests/setup/test_flow.py`.
- **Read:** `docs/design/10-setup.md` § The flow; § Principles; the mockup's `FIRST` scenario, `reviewFirst`,
  `applyFirst`, `doneFirst`, `changeStep`.
- **Check:** `uv run pytest -q tests/setup`; then the full checks.
- **Done:** in a `pty` with scripted keys, the first-setup flow on the mockup's fixture project asks the mockup's
  questions in order with its defaults, the review lists the same groups, "Change an answer" jumps back and keeps
  later answers as defaults, "Show the command" prints a command whose `Answers` equal the prompted ones, and
  "Write it" produces the same files as `init --yes` with that command.
- **Risks:** choosing "None" for agents skips the agent questions (`test_no_agents`); `--runs remote` skips the log
  dir question (`test_remote_only`); ctrl-c at the review leaves no trace (`test_abort_at_review`).

1. A step is `Step(id, ask: Callable[[Term, Answers, Scan], None], when: Callable[[Answers, Scan], bool],
   summary)`; a flow is a list of steps; `run(term, scan, answers) -> Answers | None`.

### W12. Teammate and cluster flows (sonnet) — code — **done**

- **Touches:** `src/beamtime/setup/flow.py`, `tests/setup/test_flow.py`.
- **Read:** the mockup's `MATE` and `CLUSTER` scenarios; `docs/design/10-setup.md` § The flow.
- **Check:** `uv run pytest -q tests/setup`.
- **Done:** a project with `beamtime.yaml` and two remotes asks only agents, which remotes, how to reach a host
  missing from `~/.ssh/config`, and ssh sharing, and the review lists `beamtime.yaml` as unchanged; a fixture
  cluster (`sbatch` on `PATH`, `$HOME` on nfs) asks role, link and cache, and agents only for role `full`.

### W13. Stale checks, `--check` and the status line (sonnet + review) — code — **done**

- **Touches:** new `src/beamtime/setup/stale.py`, new `src/beamtime/setup/changes.py`, `src/beamtime/setup/scan.py`
  (`Scan.stale`), `src/beamtime/ops/registry.py` (`InitParams.check`), `src/beamtime/ops/reading.py` (`status`
  1040), `docs/reference/cli.md` (regenerated), new `tests/setup/test_stale.py`.
- **Read:** `docs/design/10-setup.md` § Updating an older setup.
- **Check:** `uv run pytest -q tests/setup tests/ops tests/mcp tests/test_docs.py`; `uv run pytest -q -n0
  tests/test_budgets.py`; then the full checks.
- **Done:** fixture projects set up with the 0.1.1 and 0.2.0 files (rules block, `.mcp.json` pointing at a missing
  file, `colormap` in `beamtime.yaml`, skills, runs outside the log dir) list each stale item with before and after;
  `init --check` exits 3 with one line each and 0 after `init --yes`; `status` adds "set up with 0.1.1;
  `beamtime init` updates it" and nothing for a current or rule-less project.
- **Risks:** `status` doesn't import `setup/` beyond `guide/rules.py` (`test_budgets`); a hand-edited block is
  reported but not ticked (`test_edited_block_unticked`).

### W14. The update flow (sonnet) — code — **done**

- **Touches:** `src/beamtime/setup/flow.py`, `src/beamtime/ops/admin.py` (`setup`, renamed in N11: the `update`
  flow joins the terminal branch), `tests/setup/test_flow.py`.
- **Read:** the mockup's `UPGRADE` scenario; `docs/design/10-setup.md` § Updating an older setup; decision 11
  (the planning exists: `Scan.stale`, `Answers.defaults`, `Planner.updates()`, `stale_remote()`,
  `changes.py:since()`; reuse the `old` fixture of `tests/setup/test_stale.py`).
- **Check:** `uv run pytest -q tests/setup`.
- **Done:** on the 0.1.1 fixture the flow prints the data check, the stale list all ticked with `+ Add a path`,
  asks agent behaviour and rules as new, reviews with "your data · nothing is rewritten" first and the unticked
  items as kept, and ends with `changes.py`'s lines for 0.1 → 0.3 (the rename to `beamtime setup` among them); a
  remote the probe finds older is listed as `remote:<name>`, and the screens' answers give the same `plan()` as the
  printed `beamtime setup --yes` command.

### W15. The agent hand-off (sonnet) — code — **done**

- **Touches:** `src/beamtime/setup/flow.py`, `src/beamtime/setup/agents.py` (`start_command`), `tests/setup/test_flow.py`.
- **Read:** `docs/design/10-setup.md` § The `migrate` prompt (hand-off paragraph); decision 8.
- **Check:** `uv run pytest -q tests/setup`.
- **Done:** after a write with notes or a conflict and an agent that can start, the hand-off offers start, copy and
  later; "start" calls `os.execvp` with the client's command and the paths (patched in tests); "copy" uses the
  first clipboard tool found or prints the prompt; "later" prints `beamtime setup --migrate-with <agent>`;
  `beamtime setup --migrate-with <agent>` alone, in a set-up project, goes straight to the hand-off (before W16's
  list of answers, which it skips).

### W16. Reconfiguring a current setup (sonnet + review) — code — **done**

- **Touches:** `src/beamtime/setup/plan.py` (new `Answers.saved`; `Answers.from_params` 134–192 gains `base`),
  `src/beamtime/setup/flow.py` (`run` 86–127, `pick_answer` 404–415, `intro` 221; new `reconfigure`),
  `src/beamtime/ops/admin.py` (`setup`, the terminal branch 76–88 and the `already set up` answer 93–94),
  `tests/setup/test_flow.py`, `tests/setup/test_plan.py`.
- **Read:** `docs/design/10-setup.md` § Reconfiguring; § The wizard (the `Change an answer` bullet); decision 13.
- **Check:** `uv run pytest -q tests/setup tests/ops`; then the full checks.
- **Done:** on a project made by `beamtime setup --yes --agents claude-code` (with a project remote whose path is
  `${SCRATCH}/x/beamtime`), `plan(scan, Answers.saved(scan)) == []`; after `beamtime.yaml: agent` is edited to
  `hands-on`, it is exactly the rules change of `CLAUDE.md`; in a `pty`, `beamtime setup` there lists every applying
  step with its summary plus `Review the changes`, picking the git step and `no` asks nothing else and the review
  lists only `.gitignore`; with the edited agent setting the list carries the spec's line, the cursor starts on
  `Review the changes`, and Enter reviews the rules change; "Show the command" prints a command whose `plan()`
  equals the review's; without a terminal `setup` still answers "already set up" and `setup --yes --update rules`
  rewrites the edited block.
- **Risks:** saved answers never re-register, re-import or tick the SDK (`fill()` is not called;
  `test_saved_plans_nothing`); picking agents from none to Claude Code also asks the style and the rules
  (`test_reconfigure_new_steps`); `Change an answer` at the review returns to the list, not to the step order
  (`test_reconfigure_change_again`); a remote switched off with `enabled: false` stays off
  (`test_saved_skip_remote`); ctrl-c on the list leaves no trace (`test_reconfigure_abort`).
- **Stop if:** `Answers.saved` can't reproduce a setup without a fact the scan doesn't have (a client's registration
  scope, a remote's host); name the fact instead of re-reading client files in `flow.py`.

1. `Answers.saved(scan) -> Answers`, the spec's fields; the project and user files are read with `Planner.read`
   (`scan.root / "beamtime.yaml"`, `scan.home`'s user settings). `from_params(p, scan, base: Answers | None = None)`
   fills from `base` instead of `defaults(scan)` when given.
2. `ops/admin.py:setup`: on a terminal without `--yes` the flow `current` joins the wizard, with `base=
   Answers.saved(found)`; without a terminal nothing changes.
3. `flow.reconfigure(term, scan, answers, steps) -> Answers | None`: the list is `pick_answer` with a last
   `Option("review", "Review the changes")`; after a pick, ask the step, then each later step whose `when` was false
   before and is true now; then `confirm()`; `change` loops to the list. `run()` calls it for `scan.flow ==
   "current"` instead of `fill()` and the steps in order; `intro` says "Set up with <version>. Pick what to change."

## N. The command's name

### N11. `beamtime init` becomes `beamtime setup` (sonnet) — code — **done**

- **Touches:** `src/beamtime/ops/registry.py` (`InitParams` 495 → `SetupParams`, the op 1152–1158: name, kind,
  summary), `src/beamtime/ops/admin.py` (`init` 42–110 → `setup`, `apply_failed` 113–121), `src/beamtime/ops/answers.py`
  (`BARE` 603), `src/beamtime/ops/reading.py` (215, `setup_note` 1086), `src/beamtime/ops/authored.py` (34),
  `src/beamtime/setup/plan.py` (1, 20, `from_params` 134–137, `command` 280–286), `src/beamtime/setup/flow.py` (485),
  `src/beamtime/setup/changes.py` (13, one new 0.3 line), `src/beamtime/setup/stale.py` (34),
  `src/beamtime/setup/remotes.py` (57), `src/beamtime/setup/__init__.py` (1), `src/beamtime/cli/__init__.py` (198),
  `scripts/release.py` (132), `README.md` (13), `docs/quickstart.md` (15), `docs/design/10-setup-mockup.html` (12
  places), `docs/reference/cli.md` (regenerated); `tests/ops/test_ops.py` (214, 429–482), `tests/setup/test_plan.py`,
  `tests/setup/test_flow.py`, `tests/setup/test_stale.py`, `tests/setup/test_scan.py` (323),
  `tests/setup/test_remotes.py` (194), `tests/guide/test_rules.py` (11).
- **Read:** `docs/design/10-setup.md` (opening paragraphs; § The wizard, the `ops/admin.py:setup` sentence;
  § Decisions, last three); decision 12.
- **Check:** the grep below prints nothing; `uv run python docs/site/reference.py`; `uv run pytest -q tests/setup
  tests/ops tests/guide tests/cli tests/test_docs.py`; `uv run pytest -q -n0 tests/test_budgets.py`; `uv run python
  docs/plans/setup/drive-mockup.py docs/design/10-setup-mockup.html` where Chrome is installed; then the full checks.
- **Done:** `beamtime setup --check` and `beamtime setup --yes` behave as `init` did; `beamtime init` exits with
  argparse's unknown-command error; `status` says "set up with 0.1.1; `beamtime setup` updates it"; the printed
  review command starts `beamtime setup --yes`; the MCP instructions' and the rules block's user-only list names
  `setup`; `changes.py:since("0.1.1", ...)` includes the rename; and this prints nothing:
  ```
  git grep -nE 'beamtime init|init --|InitParams|"init"|``init``' -- src tests scripts README.md docs \
    ':!docs/plans' ':!src/beamtime/guide/rules/history' ':!src/beamtime/serve/static' ':!src/beamtime/__init__.py' \
    ':!src/beamtime/sdk' ':!tests/sdk' | grep -vE '"git", "init"|git\("init"|"-C", str\(tmp_path\), "init"|up to 0\.2'
  ```
- **Risks:** the SDK's `beamtime.init()` and its docs stay untouched (`tests/sdk`, the grep's exclusions); the
  history rules texts keep `init` byte for byte, so `release_of` still names 0.1.1 and 0.2.1 (`tests/guide/test_rules.py`);
  inside `ops/admin.py:setup` the wizard is imported as `from beamtime.setup.flow import setup as wizard`, so the
  names don't shadow (`tests/setup/test_flow.py`); the CLI import budget (`tests/test_budgets.py`).
- **Stop if:** something outside this list (a skill, the web UI, a generated plugin file) names the command.

A pure rename, no behaviour change. The design documents already say `setup` (the plan update's commit); the
CHANGELOG line is Z's.

1. Op `setup`, kind `setup`, summary "Set up this project and this machine, or change the setup.";
   `InitParams` → `SetupParams` everywhere; answers' `kind` is `setup`.
2. Every message that prints the command says `beamtime setup` (the `status` line, the "no log dir" errors, the
   apply failure, the printed command, the flow's remote hint).
3. `changes.py`: a 0.3 line "The setup command is now `beamtime setup`; `init` is gone."
4. The mockup: the command in its strings and margins becomes `beamtime setup`; `drive-mockup.py` still runs.

## D. Docs

### D11. User docs (sonnet) — code — **done**

- **Touches:** `README.md`, `docs/quickstart.md`, `docs/guides/settings.md`, `docs/guides/remotes.md`,
  `docs/guides/cluster.md`, `docs/guides/agents.md`, new `docs/guides/setup.md`, `docs/nav.json`,
  `docs/design/10-setup-mockup.html`.
- **Read:** `docs/design/10-setup.md`; CLAUDE.md § Layout (docs bullet: simple main pages, advanced topics in
  `guides/`).
- **Check:** `uv run pytest -q tests/test_docs.py`; `cd web && npm run docs`.
- **Done:** the quickstart starts with `beamtime setup`, and no page says `beamtime init` except the setup guide's
  one line that 0.2's `init` is now `setup` (decision 12); the settings guide documents `cache`, `agent` (with
  `proposal_words`) and `enabled`; the agents guide names `proposal_words` and `proposal set`'s warning; the cluster
  guide uses `--link-logdir` and `cache`; the new setup guide lists every flag with an example `--yes` command, the
  update path, reconfiguring a current setup (the list of answers, the rules refresh, `--update rules` without a
  terminal), and that `setup --yes` copies Beamtime runs found outside the log dir into it by default (a copy, the
  originals stay; `--import ''` declines); the mockup neither detects nor asks for the conventions and labels them
  `beamtime.yaml` (decision 10), and its `Choose each setting` form has the `proposal length` row (decision 14).

## Z. Close

- **Touches:** `CHANGELOG.md` (0.3.0 section: the rename as a breaking change, reconfiguring, `proposal_words`),
  `CLAUDE.md` (Status and Layout: `setup/`), `docs/design/10-setup.md`
  (Status line, Implementation notes), `docs/design/00-overview.md` if names changed.
- **Read:** `docs/design/10-setup.md`; [Breaking changes](#breaking-changes).
- **Check:** the full checks; `uv run pytest -q -n0 tests/test_budgets.py`; `uv run python
  docs/plans/setup/drive-mockup.py docs/design/10-setup-mockup.html` still runs.
- **Done:** the changelog lists every row of Breaking changes and the new features; the spec's status says
  implemented; `ticket.py status` shows every ticket done; the Goal's "Confirmed by" checks pass.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| the setup command | `beamtime init` | `beamtime setup`; `init` is an unknown command (no alias) | replace `init` with `setup` in scripts and docs |
| `beamtime setup` without a terminal | `init` wrote `beamtime.yaml` and `.gitignore` | prints the review and the command; writes only with `--yes` | add `--yes` to scripts |
| `beamtime setup` in a set-up, current project, on a terminal | – (`init` said "already set up") | opens the list of answers to change | none; ctrl-c leaves it as it was |
| `.gitignore` from `setup` | `beamtime/` | a marked block ignoring run data only (`--git record`) | `--git none` keeps the old behaviour |
| `serve --stdio` cache on a remote with a local `$HOME` | always memory unless `--cache` | the remote's own `cache` setting if set, else memory | none |
| `cache_dir()` with `cache: memory` | – | a runtime dir; the index lives in a per-process temp dir | none |
| `mcp install` into shared files | absolute path of `beamtime` | a portable command, or the client's machine scope | run `beamtime setup` (the `mcp` update item) |
| the agent rules block | fixed text from `instructions.md` | generated from `agent` settings | run `beamtime setup` (the `rules` update item) |
| `beamtime --version` | `beamtime 0.3.0` | adds `(no serve extra)` when the extra is missing | parse the first two words |
| `_moves.jsonl` | three fields | optional `within` | older Beamtime releases apply a `within` move everywhere |

## Not verified

- Each client's MCP config format and start command (VS Code `servers` with `type: stdio`, Cursor's
  `${workspaceFolder}`, opencode's `mcp.<name>.type: local`, `gemini -i`, Windsurf's path) — A12 and W15 check them
  against the clients' current docs and write differences into the spec.
- That `uv run --project <root> beamtime mcp` keeps stdout clean for stdio MCP (uv prints to stderr) — A11 runs it.
- The `wandb` datastore reader's import path and API across versions — I14.
- Claude Code's project-memory folder escaping — S12 checks against `~/.claude/projects` on this machine.
- `msvcrt` input on Windows — T11 tests only the POSIX path; Windows runs the numbered fallback in CI.
- That `Answers.saved` can be built from the scan and the two settings files alone, so a current setup plans
  nothing — W16 starts with `test_saved_plans_nothing`.
- That nothing outside N11's list (skills generated by `scripts/build-plugin`, the web UI) prints the command —
  N11's grep covers `src`, `tests`, `scripts` and `docs`.
