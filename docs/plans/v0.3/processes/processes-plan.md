# Processes: seeing and stopping Beamtime's background processes

Base commit `fb352bd`, branch `setup` (with the setup session's uncommitted spec edits to `docs/design/` read as
the current state). Proposed 2026-11-15, based on the coordinator's brief (the decisions on `ps`, `stop` and
`serve`), the code at the base commit, `docs/design/10-setup.md` § The cache and `docs/plans/setup/setup-plan.md`
(F11, F13, N11), and one reproduction (finding 4). Not interviewed: the user was unavailable, so open points are
decided as **assumed** and listed in [Questions for the user](#questions-for-the-user). It ships in 0.3.0 with the
setup work. Behaviour changes are allowed; they are listed in [Breaking changes](#breaking-changes).

Run a ticket with `/run-ticket docs/plans/v0.3/processes/processes-plan.md <ID>` in a fresh session; review
tickets marked `+ review` with `/review-ticket docs/plans/v0.3/processes/processes-plan.md <ID>` on a stronger
model. `ticket.py status docs/plans/v0.3/processes/processes-plan.md` shows what's done and what's next.

## Goal

The outcome this plan commits to, checked against at the end and in every review:

- **Done means:** `beamtime ps` (user-only) lists every Beamtime process of this user on this machine, grouped by
  kind: `serve` (web UI), `index` (`serve --no-ui`), `remote` (`serve --stdio`), `mcp`, and `ssh` (logins kept
  open for remotes that `beamtime setup` configured). Each row shows root or log dir, pid, URL where there is one,
  cache, uptime, and for serves whether this directory's CLI and MCP calls use it. Records of processes that died
  are flagged and removed. `beamtime stop [<root>|<pid>|--all]` stops serve processes only, through the token,
  with SIGTERM as the fallback; MCP, remote and ssh processes are listed, never stopped. `beamtime serve` for a
  root that already has one prints the running one's URL instead of failing; `--replace` takes over. With a
  `memory` cache, a CLI or MCP call while a serve runs sees the runs (today it sees none).
- **Confirmed by:** the full checks and `uv run pytest -q -n0 tests/test_budgets.py`; `uv run pytest -q
  tests/index/test_procs.py tests/ops/test_procs.py tests/serve/test_procs.py`; by hand: start `beamtime serve`,
  `beamtime serve --no-ui` in another project and `beamtime mcp` from an agent client, then `beamtime ps` lists all
  three, `beamtime serve` again prints the first one's URL, `beamtime stop --all` stops both serves, and
  `kill -9` of an MCP server shows as stale once, then disappears.
- **Out of scope:** processes on remote machines (`ps @cluster`); a process list in the web UI; stopping MCP,
  `serve --stdio` or ssh processes; Windows beyond "the code runs" (no Windows CI for these commands); experiment
  processes (Beamtime records runs, it never runs them); the transient headless renderer and one-shot CLI calls.

## Findings

Evidence: **reproduced** (run), **code** (read, not run; the ticket starts with a failing test).

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | Only `serve` can be found; `beamtime mcp` and `serve --stdio` publish nothing | `mcp/__init__.py:serve` 7–23 and `serve/stdio.py:run` 121–155 write no file; `serve.json` is written only by `index/daemon.py:write_status` 68–80 | code | J51, J52 |
| 2 | There is no machine-wide place to look: serves publish in their own cache (`<cache root>/<hash>/` or `<tmp>/beamtime-<uid>/<hash>/`), and another project's `cache` setting names a root this shell can't know | `index/cache.py:resolve_cache` 158–175, `runtime_dir` 25–41 | code | J51 |
| 3 | A second `serve` fails with "already runs … open that one, or stop it first", and there is no command to stop it | `serve/server.py:serve` 64–74; no stop path in `serve/app.py` | code | J55, J56 |
| 4 | With `cache: memory`, a CLI call while a serve runs answers from an empty index: 47 runs without a serve, 0 with one | `index/index.py:catch_up` 227 skips catching up when `daemon_status` finds a daemon, but a memory `Index` has its own empty `scratch` folder; `via_serve` routes only calls about remotes (`remote/via_serve.py:involves_remotes` 13–27) | reproduced (`uv run python docs/plans/v0.3/processes/memory-repro.py <empty dir>`) | L51 |
| 5 | `serve --no-ui` killed with SIGTERM leaves `serve.json` behind | the SIGTERM handler is installed only on the UI branch (`serve/server.py` 92); the no-UI loop 76–80 has none, so `finally` 101–110 never runs | code | J52 |
| 6 | `daemon_status` probes `serve.lock` by taking it briefly; a `serve` starting at that instant thinks another one runs | `FileLock.held_elsewhere` (`index/cache.py` 236–245) acquires and releases; `serve` gives up after one try (`daemon.start` → `lock.acquire()`, timeout 0) | code | J56 |
| 7 | ssh ControlMaster processes started by `beamtime setup --ssh-share` stay up 12 h and are invisible | `setup/remotes.py` `SSH_BLOCK` 18–23 (`ControlPersist 12h`) | code | J54 |

## Brief

What the tickets build together, so a session doesn't rediscover the design:

- **The process registry** (J51): `src/beamtime/index/procs.py` (new, standard library only). Every long-running
  Beamtime process registers itself in `runtime_base()/procs/`: a lock file `<kind>-<pid>-<6 hex>.lock` it holds
  for its whole life (`FileLock`, so liveness works on POSIX and Windows without `os.kill(pid, 0)`, which
  terminates the process on Windows), and a JSON record with the same stem, written after the lock is taken and
  removed before it is released. A record whose lock can be taken is stale. `runtime_base()` is
  `<tempfile.gettempdir()>/beamtime-<uid>` (mode 0700), or `BEAMTIME_RUNTIME` when set; `runtime_dir(logdir)`
  becomes `runtime_base() / log_hash(logdir)`.
- **The record** (`schema: 1`): `kind` (`serve`, `index`, `remote`, `mcp`), `pid`, `ppid`, `version`, `started`,
  `root` (or `null`), `logdir`, `cache` (the folder with `serve.lock`/`serve.json`/`serve.token`, or the index
  folder), `cache_kind` (`disk`, `memory`, `temporary`), `port` (`serve` only), `sources` (remote names, serve
  only), `client` (the MCP client's name, or the ssh peer from `SSH_CONNECTION` for `remote`; else `null`).
- **Writers** (J52): `serve/server.py:serve` registers `serve` or `index` after `daemon.start()`;
  `serve/stdio.py:run` registers `remote`; `mcp/__init__.py:serve` registers `mcp`. Each removes its record in
  `finally`; a killed process leaves a stale record that the next `ps` removes.
- **Readers** (J53, J54, J55, J56): `src/beamtime/ops/procs.py` (new) holds `ps`, `stop` and the shared
  `serves()`/`stop_serve()`; `ps` also scans `<disk cache root>/*/serve.json` and `runtime_base()/*/serve.json`
  for serves without a record (an older Beamtime still running) and removes `serve.json` whose `serve.lock` is
  free. The token stays (it outlives restarts by design, `serve/auth.py:load_token`).
- **Stopping a serve** (J55): `POST /api/shutdown` with the bearer token, handled in `serve/app.py:build` before
  the registry dispatch, as `watch` is (`shutdown` is no registry method, so the user-only-404 test stays true);
  it calls `app.state.stop()`, which `server.py` sets to `server.handle_exit`. Without a port (`index`) or when the
  request fails: SIGTERM. `stop` waits for `serve.lock` to be free.
- **"Used here"** (J53): for a serve whose `logdir` is this context's log dir: `live index, remote calls` (UI,
  same cache), `live index` (no UI, disk), `all reads` (UI, memory, after L51), `no: memory, no UI`, or
  `no: this shell's cache is <path> (<source>)`; other kinds and other log dirs show `-`.
- **CLI path**: nothing here is imported by `beamtime runs`; `ops/procs.py` loads only when `ps` or `stop` run;
  `index/procs.py` imports only `json`, `os`, `secrets`, `time`, `pathlib` and `beamtime.index.cache`.

Done, for every ticket: its Done line holds; its Check passes; the spec documents say what the code does; its heading
is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` (4 xdist workers; `-n0`
   serially). Budgets after J51, J52, J53: `uv run pytest -q -n0 tests/test_budgets.py`. Tests that start real
   processes use `subprocess.Popen([.venv beamtime, "serve", "--port", "0"])` as `tests/serve/conftest.py:server`
   78–101 does, and always pass a per-test `BEAMTIME_RUNTIME`.
2. Generated files: any change to `src/beamtime/ops/registry.py` regenerates `docs/reference/cli.md` with
   `uv run python docs/site/reference.py` (`tests/test_docs.py` checks it). J53, J55 and J56 change the registry, so
   they run one after another, and only after the setup plan's N11 (which renames `init` to `setup` in the
   registry).
3. Rules: CLAUDE.md's Python style; keep the CLI path light (`tests/test_budgets.py`); never touch
   `docs/design/10-setup.md`, `docs/plans/setup/` or `tests/golden/`. No `os.kill(pid, 0)` anywhere (Windows).
4. Spec: `docs/design/03-index.md` and `docs/design/08-cli-mcp.md` (J50 writes the design); a deviation is written
   back in the same commit.
5. Ticket budget: 140k tokens per ticket session (assumed default); split a ticket that would exceed it.
6. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading. The hash stays in git (`ticket.py status`).

## Order

```
setup F11, F13 (done) ── J50 ─┬─ J51 ─ J52 ─┐
                             └─ L51       ├─ (after setup N11) J53 ─ J54 ─ J55 ─ J56 ─ J57 ─ (after setup D11, Z) J58
                                         ┘
```

What's left runs in this order: J50 J51 J52 L51 J53 J54 J55 J56 J57 J58

The setup plan's F11 (`resolve_cache`, `runtime_dir`) and F13 (`known_logdirs`) are what this plan builds on;
both are done. J53, J55 and J56 regenerate `docs/reference/cli.md` and edit `ops/registry.py`, as the setup plan's
N11 does, so they start after N11. J57 and J58 edit `docs/guides/`, `CHANGELOG.md` and `CLAUDE.md`, as setup's D11
and Z do, so J58 runs after setup Z. J50, J51, J52 and L51 touch nothing the pending setup tickets touch and can start now,
but not in the same checkout while a setup ticket session runs. L51 is independent of J51/J52.

## Decisions taken; say if you want otherwise

1. **The registry lives in the runtime dir, not in a cache** (assumed): `runtime_base()/procs/`, because it is
   the one place every process of a user agrees on regardless of `cache` settings (finding 2), and it is local
   disk. Rejected: records in each cache (a `ps` can't know other projects' caches); `$XDG_RUNTIME_DIR` (Linux
   only, and F11 already publishes memory serves under `runtime_base()`).
2. **Liveness by a held lock, not by pid** (assumed): immune to pid reuse and safe on Windows. Rejected:
   `os.kill(pid, 0)` (kills on Windows), `psutil` (a dependency).
3. **`BEAMTIME_RUNTIME` overrides the runtime base** (assumed), set by `tests/conftest.py` like `BEAMTIME_CACHE`,
   because tests start subprocesses that a `tempfile.tempdir` patch doesn't reach. It also moves `runtime_dir()`.
4. **`serve --no-ui` is the index daemon**: there is no other daemon; `ps` shows it as kind `index`.
5. **`ssh` logins are listed from `~/.ssh/config`'s Beamtime-marked blocks** (`setup/remotes.py:SSH_MARK`) with
   `ssh -O check <host>` (local socket check, 3 s timeout), and `ps` names `ssh -O exit <host>` as the way to end
   them (assumed). Rejected: listing every ControlMaster of the user (not Beamtime's).
6. **`stop` takes a root, a log dir or a pid** (assumed): `beamtime stop` = this context's serve; a path matches a
   serve's `root` or `logdir`; digits match a serve's pid (as `ps` prints it); `--all` stops every listed serve. A
   pid of an MCP, remote or ssh process is refused with "listed, not stopped: it belongs to <client>".
7. **`stop` never sends SIGKILL** (assumed): token, then after 10 s SIGTERM, then after 10 s more it reports
   "still stopping (pid N); `kill -9 N` ends it now" and exits 1.
8. **`serve` on a served root prints and exits 0** (assumed): "Beamtime already serves <logdir> (pid N) at <URL>";
   with `--open` it opens that URL; it never starts a second process. It exits 1 with a hint to `--replace` when
   the running one can't give what was asked: a UI asked of an `index` serve, other explicit sources, or an older
   version (exit 0 there, with the hint, since the UI works).
9. **`--replace`** stops the running serve exactly like `beamtime stop <root>`, then starts as usual, trying the
   old port first when no `--port` was given.
10. **With a memory cache, reads go through a running UI serve** (assumed, finding 4): every operation from
    `beamtime.ops.reading` that isn't user-only is sent through `via_serve.call` when the cache is `memory`; and
    a memory `Index` (`scratch` set) never skips its catch-up because a daemon runs. Rejected: only the guard
    (correct but slow: each call indexes again within 200 ms and answers partially); routing writes too (paths
    and stdin are relative to the caller's working directory).
11. **The token is shown**: `ps` prints the URL with `?token=`, as `serve` does; the record files are mode 0600 in
    a 0700 folder.
12. **`ps` cleans up silently but says so**: stale rows are printed once under "stale (removed)", then deleted.

## J. Processes and the memory fix

### J50. The spec: processes, `ps`, `stop` and attaching serves (sonnet) — code

- **Touches:** `docs/design/03-index.md` (§ Freshness: the daemon 163–183, § Daemon status for agents 185–194,
  new § Processes after it, § Decisions 537), `docs/design/08-cli-mcp.md` (§ User-only commands table 93–110,
  internal entry points 112–113, § Implementation notes `serve` and `demo` bullet ~300, § Decisions 308),
  `docs/design/04-remotes.md` (§ Protocol 225: one sentence that `serve --stdio` registers as `remote`).
- **Read:** this plan's Brief and Decisions; `docs/design/10-setup.md` § The cache (264–306, read-only).
- **Check:** `uv run pytest -q tests/test_docs.py`.
- **Done:** 03-index.md says a second `serve` attaches (or `--replace`), defines the registry, the record fields,
  stale handling and memory routing (decision 10); 08-cli-mcp.md lists `beamtime ps` and `beamtime stop` as
  user-only and `--replace` on `serve`; no code changes; 10-setup.md untouched.
- **Risks:** "one daemon per root … refuses to start" (03-index l. 170) is rewritten, not left contradicting
  (`git grep -n 'refuses to start' docs/design` is empty); the setup session's uncommitted edits in 04 and 08 are
  kept (`git diff` shows only additions from this ticket around them).
- **Stop if:** the setup session has changed § The cache since the base commit in a way that contradicts the Brief.

1. § Processes (about 30 lines): the four Beamtime kinds plus `ssh`; the registry folder and file names; the
   record table; liveness by lock; who writes and when; what `ps` scans in addition; the "used here" values.
2. User-only table rows: `beamtime ps` ("every Beamtime process of this user on this machine, grouped by kind,
   with stale records removed") and `beamtime stop [<root>|<pid>] [--all]` ("stops serves: through the token,
   else SIGTERM; MCP, remote and ssh processes are never stopped"); `serve` row gains `--replace`.
3. Policy line: agents that find no daemon still hand the user `beamtime serve --no-ui`; to see what runs, they
   hand `beamtime ps`.

### J51. The process registry (sonnet + review) — code

- **Touches:** new `src/beamtime/index/procs.py`, `src/beamtime/index/cache.py` (`runtime_dir` 25–41: new
  `runtime_base`), `tests/conftest.py` (21: `BEAMTIME_RUNTIME`), `tests/index/test_cache.py` (the `clean`
  fixture ~30–45 deletes `BEAMTIME_RUNTIME` where it patches `tempfile.tempdir`), new `tests/index/test_procs.py`.
- **Read:** `docs/design/03-index.md` § Processes (J50).
- **Check:** `uv run pytest -q tests/index`; `uv run pytest -q -n0 tests/test_budgets.py`; then the full checks.
- **Done:** a subprocess that registers is listed with every field; after it exits normally its files are gone;
  after `kill -9` the next `listed()` returns it once in `stale` and removes both files; `runtime_dir()` honors
  `BEAMTIME_RUNTIME`; `import beamtime.cli` still loads no heavy module.
- **Risks:** a record without a lock file, or a lock without a record younger than 60 s (a process registering
  right now), is left alone (`test_registering_is_not_stale`); two processes with the same pid stem never share a
  file (`test_names_are_unique`); an unreadable or half-written JSON is skipped, not raised
  (`test_broken_record_skipped`); listing never creates `procs/` when it doesn't exist (`test_list_reads_only`).

1. `cache.runtime_base() -> Path`: `BEAMTIME_RUNTIME` (expanded) if set, else `<gettempdir()>/beamtime-<uid>`;
   mkdir 0700 and chmod as `runtime_dir` does today; `runtime_dir(logdir) = runtime_base() / log_hash(logdir)`.
2. `class Registration` (keyword-only `__init__(kind, fields)`; `open() -> Registration` takes the lock, then
   writes `<stem>.json` atomically (write `.tmp`, `os.replace`, mode 0600); `update(**fields)` rewrites it;
   `close()` unlinks the JSON, releases and unlinks the lock; context manager).
   `register(kind: Literal["serve", "index", "remote", "mcp"], **fields) -> Registration` fills `pid`, `ppid`,
   `version` (`importlib.metadata` imported inside the function), `started`, `schema: 1`.
3. `listed() -> tuple[list[dict], list[dict]]`: live records (lock held elsewhere) and stale ones (lock free;
   their files removed, `OSError` ignored for Windows' open files), sorted by `kind`, then `started`.

### J52. serve, serve --stdio and mcp register themselves (sonnet + review) — code

- **Touches:** `src/beamtime/serve/server.py` (`serve` 26–110; SIGTERM handler before the no-UI branch 76),
  `src/beamtime/serve/stdio.py` (`run` 121–155), `src/beamtime/mcp/__init__.py` (`serve` 7–23),
  `src/beamtime/mcp/server.py` (`build` 266–317: the client's name on first call), new
  `tests/serve/test_procs.py`.
- **Read:** `docs/design/03-index.md` § Processes; this plan's Brief (the record).
- **Check:** `uv run pytest -q tests/serve/test_procs.py tests/serve/test_stdio.py tests/mcp`; then the full checks.
- **Done:** a `beamtime serve --port 0` subprocess is listed as `serve` with its port, cache and sources; `--no-ui`
  as `index` with `port: null`; `serve --stdio` as `remote` with `cache_kind: temporary` and the `SSH_CONNECTION`
  peer; `beamtime mcp` (through `mcp.client.stdio`) as `mcp` with its root and, after one tool call, the client's
  name if the SDK exposes it; each record is gone after a clean exit; SIGTERM to `--no-ui` removes `serve.json`.
- **Risks:** the record is written only after `daemon.start()` succeeds, so a refused serve leaves none
  (`test_refused_serve_leaves_no_record`); `--watch` re-exec (`again` 276) closes the old record first
  (`test_watch_restart_one_record`); MCP outside a project still registers with `root: null`
  (`test_mcp_without_root`); stdout of `--stdio` and `mcp` stays protocol-only (existing stdio and mcp tests).
- **Stop if:** the MCP SDK 2.3 request context has no way to reach the client info; then record `client: null`
  and say so in the commit, don't patch the SDK.

1. server.py: `signal.signal(signal.SIGTERM, stop)` right after `daemon.start()` for both branches; register
   `kind="index" if sock is None else "serve"` with `root=str(ctx.root)`, `logdir`, `cache=str(cache)`,
   `cache_kind="memory" if daemon.memory else "disk"`, `port`, `sources=sorted(sources.clients) if sources else
   []`; close in `finally` before `again()`.
2. stdio.py: register after `resolved` is known (`cache_kind` `temporary` when `own`, else `resolved.kind`),
   `client=os.environ.get("SSH_CONNECTION", "").split(" ")[0] or None`; close in the existing `finally`.
3. mcp: `Context.make(root=root, caller="mcp")` once in `serve` for `root`/`logdir`/`cache` (an `OpError` there
   registers `root: None`); try/finally around `anyio.run`; on the first `call_tool`, `update(client=...)` from
   the request context's connection `client_params.client_info.name` when present.

### L51. A memory cache sees a running serve's runs (sonnet + review) — reproduced

- **Touches:** `src/beamtime/index/index.py` (`catch_up` 227), `src/beamtime/remote/__init__.py` (`answer`
  59–87), `src/beamtime/remote/via_serve.py` (`involves_remotes` 13–27, new `memory_reads`),
  `tests/index/test_cache.py`.
- **Read:** `docs/design/03-index.md` § Freshness: the daemon (as J50 left it); `docs/design/10-setup.md` § The
  cache, the `memory` bullet (read-only).
- **Check:** `uv run pytest -q tests/index tests/remote`; then the full checks.
- **Done:** with `cache: memory` and a running memory daemon, an `Index` catches up itself and finds every run
  (the reproduction's 47 of 47, as a test on the synth log dir); with a UI serve running, `beamtime runs` is
  answered through `via_serve.call` (test with the echo server of `test_serve_with_memory_is_found_by_via_serve`
  150–186); writes and user-only ops still run locally.
- **Risks:** a disk cache keeps the short-circuit (`Freshness(daemon=True)`) exactly as today
  (`test_disk_cache_defers_to_daemon`); a serve that went away between check and call falls back to answering
  locally (`via_serve.call` returns `None`, existing branch 64–66); the routed answer keeps the caller's answer
  sizes (header `x-beamtime-caller`).
- **Stop if:** routing reads changes answers that existing tests pin (other than freshness meta).

1. `catch_up`: `if not daemon and self.scratch is None and daemon_status(self.cache) is not None`.
2. `via_serve.memory_reads(ctx, op) -> bool`: `resolve_cache(ctx.logdir, ctx.settings).kind == "memory"` and
   `op.impl.startswith("beamtime.ops.reading:")` and not `op.user_only`.
3. `remote.answer`: before the local shortcut (line 71), `if memory_reads(...) and (found := via_serve.call(...))
   is not None: return upgraded(found)`; import `via_serve` lazily as today.

### J53. `beamtime ps` (sonnet + review) — code

- **Touches:** new `src/beamtime/ops/procs.py` (`ps`, `serves`, `used_here`), `src/beamtime/ops/registry.py`
  (new `PsParams` after `GcParams` 625; `Op` after `gc` 1281), `src/beamtime/ops/answers.py` (`BARE` 601–605:
  `ps`), `src/beamtime/cli/format.py` (new `render_ps` after `render_status` 610), `docs/reference/cli.md`
  (regenerated), new `tests/ops/test_procs.py`.
- **Read:** `docs/design/03-index.md` § Processes; `docs/design/08-cli-mcp.md` § User-only commands.
- **Check:** `uv run pytest -q tests/ops tests/serve/test_app.py tests/test_docs.py`;
  `uv run pytest -q -n0 tests/test_budgets.py`; then the full checks.
- **Done:** with fixture records (registered by helper subprocesses) of every kind, `ps` groups them in the order
  serve, index, remote, mcp, ssh; prints root (or log dir), pid, URL with token, cache (`disk <path>`, `memory`,
  `temporary`), uptime (`4 min`, `2 h`, as `index.py`'s duration helper 84–91), and "used here" per the Brief;
  `--json` gives the answer; a stale record and a stale `serve.json` appear under "stale (removed)" once; `ps` is
  not an MCP tool and `/api/ps` is 404.
- **Risks:** a serve of an older Beamtime (only `serve.json` + held `serve.lock` in the default cache root or
  `runtime_base()`, no record) is listed once, not twice (`test_legacy_serve_listed_once`); a serve whose cache
  differs from this shell's says so (`test_used_here_other_cache`); `ps` outside a project still lists everything
  (`test_ps_without_root`).

1. `PsParams(Params)`: no fields beyond the base (`NoParams` is fine); `Op(name="ps", kind="ps",
   render=f"{F}:render_ps", params=NoParams, impl="beamtime.ops.procs:ps", user_only=True, summary="Every
   Beamtime process on this machine: serves, index daemons, remotes, MCP servers.")`.
2. Answer: `{"kind": "ps", "groups": {kind: [row, ...]}, "stale": [row, ...], "lines": [...]}`; a row is the
   record plus `url`, `uptime_s`, `used_here`.
3. `serves(ctx) -> list[dict]` (live `serve` and `index` rows, legacy ones included) is the function J55 and J56
   reuse.

### J54. ssh logins in `ps` (sonnet) — code

- **Touches:** `src/beamtime/ops/procs.py` (new `ssh_logins`), `src/beamtime/cli/format.py` (`render_ps`),
  `tests/ops/test_procs.py`.
- **Read:** `src/beamtime/setup/remotes.py` 14–23 (`SSH_MARK`, `SSH_BLOCK`); decision 5.
- **Check:** `uv run pytest -q tests/ops/test_procs.py`; then the full checks.
- **Done:** with a fixture `~/.ssh/config` holding two marked blocks and a fake `ssh` on `PATH` that answers
  `Master running (pid=4242)` for one host and fails for the other, `ps` lists one `ssh` row (host, pid) with the
  hint `ssh -O exit <host>`; without `ssh` on `PATH` the group is empty and nothing raises.
- **Risks:** an `ssh` that hangs is cut at 3 s (`test_ssh_check_timeout`); hosts are checked in parallel, so ten
  marked hosts don't take 30 s (`test_ssh_checks_parallel`); the user's own unmarked hosts are never checked
  (`test_unmarked_hosts_ignored`).

1. `ssh_logins(home: Path) -> list[dict]`: hosts from lines starting with `SSH_MARK` (import the constant inside
   the function); `subprocess.run(["ssh", "-O", "check", host], capture_output=True, timeout=3)` in a
   `ThreadPoolExecutor`; the pid from `pid=(\d+)` in stderr.

### J55. `beamtime stop` (sonnet + review) — code

- **Touches:** `src/beamtime/serve/app.py` (`build` 34–142: `/api/shutdown`), `src/beamtime/serve/server.py`
  (`serve` 93–97: `app.state.stop`), `src/beamtime/ops/procs.py` (new `stop`, `stop_serve`),
  `src/beamtime/ops/registry.py` (new `StopParams`; `Op` after `ps`), `src/beamtime/ops/answers.py` (`BARE`:
  `stop`), `docs/reference/cli.md` (regenerated), `tests/serve/test_procs.py`, `tests/serve/test_app.py`
  (`test_errors_and_user_only_operations` 63–74 stays green).
- **Read:** `docs/design/08-cli-mcp.md` § User-only commands (J50); decisions 6 and 7.
- **Check:** `uv run pytest -q tests/serve tests/ops/test_procs.py tests/test_docs.py`; then the full checks.
- **Done:** `beamtime stop` in a served project stops a `serve --port 0` subprocess through `/api/shutdown`
  (exit 0 within 5 s, `serve.json` and the record gone); a `--no-ui` serve stops by SIGTERM; `--all` stops two
  serves of two projects; `stop <pid of an mcp record>` exits 2 with "listed, not stopped"; nothing to stop
  prints "no serve runs for <root>" and exits 0.
- **Risks:** `/api/shutdown` without the token is 401 (`test_shutdown_needs_token`); a wrong token in a cookie of
  another port is refused (existing `TokenGuard`); the reply reaches the client before the server exits
  (`test_shutdown_replies_first`); a serve that ignores the token falls back to SIGTERM after 10 s
  (`test_stop_falls_back_to_sigterm`, with the timeout patched short).

1. app.py: `Route("/api/shutdown", shutdown, methods=["POST"])` before `/api/{method}`; `shutdown` replies
   `{"kind": "stop", "pid": os.getpid()}` and schedules `request.app.state.stop()` via a background task.
2. server.py: after `server = server_class()(config, hub=hub)`, `app.state.stop = lambda:
   server.handle_exit(signal.SIGTERM, None)`.
3. `StopParams(target: str | None = None, all: bool = False)`, `positional=("target",)`; `stop_serve(row,
   wait_s=10.0) -> Literal["token", "sigterm", "running"]`, polling `FileLock(cache/serve.lock).held_elsewhere()`
   every 0.1 s.

### J56. `serve` attaches to a running serve; `--replace` (sonnet + review) — code

- **Touches:** `src/beamtime/serve/server.py` (`serve` 59–74), `src/beamtime/index/daemon.py` (`start` 58–66: a
  0.5 s lock timeout), `src/beamtime/ops/registry.py` (`ServeParams` 654–676: `replace`), `docs/reference/cli.md`
  (regenerated), `tests/serve/test_procs.py`.
- **Read:** `docs/design/03-index.md` § Freshness: the daemon (J50); decisions 8 and 9.
- **Check:** `uv run pytest -q tests/serve tests/index`; then the full checks.
- **Done:** a second `beamtime serve` in a served project prints "Beamtime already serves <logdir> (pid N) at
  <URL>" and exits 0 without binding a port; `--no-ui` while a UI serve runs does the same; a UI asked while an
  `index` serve runs exits 1 naming `beamtime serve --replace`; `--replace` stops the first one and the new one
  serves on the old port; `demo` follows the same rules.
- **Risks:** the lock probe of a concurrent `ps` doesn't make a starting serve attach to nothing
  (`test_start_survives_probe`: a thread probing `held_elsewhere` in a loop while `Daemon.start` runs); a stale
  `serve.json` with a free lock never counts as running (`test_stale_status_ignored`); with memory, the attach
  finds the serve in `runtime_dir` (`test_attach_memory`).
- **Stop if:** attaching needs the browser on a headless machine; it doesn't open one without `--open`.

1. Check `daemon_status(cache)` before `bind()`; when running, build the message from it and the token
   (`serve/auth.py:TOKEN_FILE`), `webbrowser.open(url)` only with `p.open`, return `{"kind": "serve", "lines":
   [...]}`; with `p.replace`, `ops.procs.stop_serve(row)` first and `p.port` defaults to the old port.
2. `Daemon.start`: `self.lock.acquire(timeout=0.5)`.
3. Version mismatch (`running["version"] != version("beamtime")`): one more line naming `--replace`.

## K. Docs

### J57. User docs (haiku) — code

- **Touches:** `docs/guides/settings.md` (the cache section: where a memory serve publishes, `beamtime ps`),
  `docs/guides/agents.md` (38: the user-only list gains `beamtime ps`, `beamtime stop`), `docs/guides/remotes.md`
  (47–54: `serve` again prints the running URL; `stop`), `docs/quickstart.md` (42: one line on `ps`/`stop`),
  `src/beamtime/guide/parts/` (the part that names `beamtime serve --no-ui`: add `beamtime ps`).
- **Read:** `docs/design/08-cli-mcp.md` § User-only commands; CLAUDE.md § Layout (docs bullet).
- **Check:** `uv run pytest -q tests/test_docs.py tests/guide`; `cd web && npm run docs`.
- **Done:** each named page mentions `ps` and `stop` in one or two lines; the guide's live-data default names
  `beamtime ps`; the docs site builds.

## Close

### J58. Close (sonnet) — code

- **Touches:** `CHANGELOG.md` (0.3.0 section), `CLAUDE.md` (Layout: `index/procs.py`, `ops/procs.py`;
  `BEAMTIME_RUNTIME` in the tests line), `docs/design/03-index.md` (Implementation notes 471).
- **Read:** [Breaking changes](#breaking-changes); the Goal.
- **Check:** the full checks; `uv run pytest -q -n0 tests/test_budgets.py`.
- **Done:** the changelog lists `ps`, `stop`, `serve --replace`, the attach behaviour and the memory fix; the
  Goal's "Confirmed by" checks pass, including the by-hand run; `ticket.py status` shows every ticket done.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| a second `beamtime serve` for a root | exits 1 ("already runs … stop it first") | prints the running URL, exits 0 | scripts that relied on the failure check `beamtime ps --json` |
| `runtime_dir()` | `<tmp>/beamtime-<uid>/<hash>` | the same, or under `BEAMTIME_RUNTIME` | none |
| a CLI call with `cache: memory` while a serve runs | answers from an empty index | reads go through the serve, or index themselves | none |
| `serve --no-ui` and SIGTERM | killed without cleanup | stops cleanly | none |

## Not verified

- That `tempfile.gettempdir()` is the same for an MCP server started by a GUI agent client and for the user's
  shell (macOS sets `TMPDIR` per user through launchd; a cluster job may set its own `TMPDIR`). J52's by-hand check
  starts an MCP server from Claude Code and runs `ps` from a terminal; a mismatch also affects F11's memory serves.
- That `systemd-tmpfiles` doesn't age out a long-lived record in `/tmp` (default 10 days by mtime): J51 could touch
  the record on `update`; checked by reading the distro default, not run.
- How the MCP SDK 2.3 low-level server exposes `client_info` in the `call_tool` context (J52 checks it).
- `ssh -O check` output format on OpenSSH versions other than this machine's (J54 parses only `pid=`).
- Windows: `FileLock` liveness and SIGTERM (`TerminateProcess`) are read, not run.

## Questions for the user

1. Should `beamtime serve` on a served root also open the browser without `--open`? Recommended: no, print the
   URL only (decision 8), since a headless login node may start a text browser.
2. Should `stop` escalate to SIGKILL after the SIGTERM wait? Recommended: no, print the `kill -9` command
   (decision 7).
3. Finding 4 is a defect in the setup plan's F11 (memory caches). Fix it here as L51, or hand it back to the setup
   session? Recommended: here, since it decides what "used here" means.
4. Should reads with a memory cache go through a running serve (decision 10), or only index themselves?
   Recommended: through the serve.
5. Should `ps` list ssh ControlMaster logins at all (J54)? Recommended: yes, read-only with the `ssh -O exit` hint.
6. Is `BEAMTIME_RUNTIME` acceptable as a documented override, or tests-only? Recommended: documented in one line
   of the settings guide, next to `BEAMTIME_CACHE`.
