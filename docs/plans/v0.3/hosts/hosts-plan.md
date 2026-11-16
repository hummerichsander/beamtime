# Hosts: several sources on one remote host

Base commit `84c96a4`, branch `setup`. Proposed 2026-11-16, based on the dataset request
(`docs/plans/datasets/beamtime-dataset-request.md`), the user's setup of the data root (one cluster host carrying
the log dirs of several projects plus a shared data directory) and the interview of 2026-11-16. It runs **after the
setup plan** (`docs/plans/setup/setup-plan.md`; W15, W16 and D11 open at the base commit) and **before the datasets
plan** (`docs/plans/datasets/datasets-plan.md`), which builds on it. Behaviour changes are allowed; they are listed
in [Breaking changes](#breaking-changes).

Run a ticket with `/run-ticket docs/plans/hosts/hosts-plan.md <ID>` in a fresh session; review tickets marked
`+ review` with `/review-ticket docs/plans/hosts/hosts-plan.md <ID>` on a stronger model.
`ticket.py status docs/plans/hosts/hosts-plan.md` shows what's done and what's next.

## Goal

- **Done means:** one remote host entry in the settings carries several named sources, each a log dir or a data
  root: `remotes: {gpu04: {host: gpu04, sources: {flows: <logdir>, md: <logdir>, data: {datasets: <root>}}}}`.
  Their places are `@gpu04:flows/<group>`, `@gpu04:md/<group>`, `@gpu04:data/<path>`; a remote with `path:` keeps
  its one-level places (`@au002a/scaling`) exactly as today. All sources of a host share one ssh connection and one
  `serve --stdio` process. Listings, routing, writes, views, `pull`, live updates and the web UI work on named
  sources as on today's remotes; the sidebar shows a host with its sources below it. `beamtime source add`,
  `source rm`, `source list` and the setup wizard add, remove and show named log dirs and data roots. Data roots are
  configured, connected and shown, and refuse every run operation with a message naming the datasets plan's
  commands. Reading them is the datasets plan's job.
- **Confirmed by:** `uv run pytest -q tests/remote tests/serve tests/setup tests/format/test_place.py
  tests/test_settings.py`. Specifically, a federation test with one `command`-transport host carrying two log-dir
  sources shows both sources' runs in one `runs` listing, placed `@box:a/...` and `@box:b/...`, over **one**
  process (`test_one_process_per_host`). `beamtime serve` against such a settings file shows `box` with children
  `a` and `b` in the sidebar (browser test). `uv run python scripts/release.py` passes its checks.
- **Out of scope:** reading data roots (datacards, `dataset` operations, dataset views), local named sources
  (`@local:data`: datasets plan), several unnamed log dirs per host, sources spanning hosts, renaming or converting
  existing remotes automatically.

## Findings

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | Two log dirs on gpu04 need two remotes, two ssh connections, two `serve --stdio` processes | `remote/sources.py` `spec_of` (12–32) makes one `Spec` per remote entry; `Sources.__init__` (60–68) one `RemoteClient` per spec; `Spec.argv` (`remote/client.py` 54–80) passes one `--logdir` | code | C31 P31 L31 |
| 2 | A source name can't say "this log dir on that host" | `Place.parse` (`format/place.py` 18–29) reads `@name/path`; the name is opaque, which is what makes `host:source` work without a grammar change | code | S31 C31 |
| 3 | `serve cluster:scaling` uses `:` to narrow a remote to a group | `parse_arg` (`remote/sources.py` 35–54) | code | R31 |
| 4 | Settings know only flat remotes | `settings.REMOTE_KEYS` (27), the check in `check_file` (276–287), `write_remote`/`remove_remote` (457–485), `Settings.remotes` (178–187) | code | C31 A31 |
| 5 | Callers build specs themselves in five places | `serve/server.py` 210–231, `views/render.py` 234–249, `remote/sources.py` `client_for` 91–111, `ops/admin.py` `remote_checks` 311 and `source_list` 391, `ops/reading.py` `sources` 1088 | code | R31 |
| 6 | The sidebar has one root per source | `web/src/shell/tree.ts` `buildTree` (21–50); `web/src/router.ts` `sourcedRun` 80, source root 85–91 | code | U31 |

## Brief

- **Names** (S31, C31): a host entry under `remotes:` has either `path:` (one unnamed source, the remote's own name, as
  today) or `sources:` (named sources), never both. The routed source name of a named source is
  `<host>:<source>`, e.g. `gpu04:flows`. `Place.parse` is unchanged and returns `source="gpu04:flows"`; `Place` gains
  read-only `host` and `name` properties that split at the first `:`. `@local` alone still normalizes to `None`.
- **Source specs** (C31): `remote/sources.py` `configured(settings) -> dict[str, Spec]` is the one place that turns
  settings into specs, keyed by routed name. `Spec` gains `host_key: str` (the entry's name), `source: str | None`
  (`None` for a `path:` remote), `kind: Literal["logdir", "datasets"]` and `depth: int` (datasets only, default 2).
  `spec_of` goes.
- **One connection per host** (P31, L31): `serve --stdio` takes `--source NAME=PATH` and `--datasets NAME=PATH`
  (repeatable) besides `--logdir`. Every request line may carry `"source": NAME`; without it the `--logdir` source
  answers. `RemoteClient` is the host's connection; `SourceClient(conn, source)` is what `Sources.clients` holds per
  routed name, with the old surface (`name`, `spec`, `state`, `request`, `describe`, `subscribe`). Code that iterates
  `ctx.sources.clients` keeps working.
- **Protocol** (P31): minor version up; `hello` answers `sources: [{name, kind}]`. A host whose remote answers
  `hello` without `sources` while the settings name sources is unreachable with the upgrade command, as for the
  bundle methods.
- **Data roots** (C31, P31, R31): a `datasets` source has a `Context` whose `logdir` is the data root and
  `kind="datasets"`; every operation on it raises
  `OpError("@<name> is a data root; read it with beamtime dataset list", code=2)` until the datasets plan.
  Federated listings skip data roots.
- **Writing settings** (A31, W31): `source add gpu04:md gpu04:/path` writes `remotes.gpu04.sources.md`, and
  `--datasets` writes `{datasets: <path>}`. `host` and `command` go to the user settings and source paths to the
  project, as for remotes today.

Done, for every ticket: its Done line holds; its Check passes; the spec documents say what the code does; its heading
is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` (4 xdist workers; `-n0`
   serially). Remote tests use the `command` transport against a second log dir (`tests/remote/conftest.py`, `box`);
   the Docker test is opt-in (`BEAMTIME_DOCKER=1 uv run pytest -q tests/remote/test_docker.py`). After a ticket
   touching `cli/`, `settings.py` or `ops/registry.py`: `uv run pytest -q -n0 tests/test_budgets.py`.
2. Generated files: `docs/reference/cli.md` (`uv run python docs/site/reference.py`, checked by `tests/test_docs.py`)
   after CLI flag changes (P31, A31, W31); these run one after another. After any change in `web/`:
   `cd web && npm ci && npm test && npm run build` and commit `src/beamtime/serve/static/` (U31 only).
3. Rules: CLAUDE.md's Python style; `format/` stays standard library plus PyYAML (`tests/test_boundaries.py`); no
   module-level PyYAML in modules `beamtime runs` loads (`tests/test_budgets.py`); every `@` is parsed by `Place`
   (`tests/test_boundaries.py` fences hand-written parses). Never touch `tests/golden/schema1/`.
4. Spec: `docs/design/04-remotes.md`, `docs/design/10-setup.md` § Remotes, `docs/design/08-cli-mcp.md` § User-only
   commands, `docs/design/01-storage.md` § Settings. S31 writes the design first; later deviations go back into it in
   the same commit.
5. Ticket budget: 140k tokens per ticket session; split a ticket that would exceed it.
6. Line numbers are at `84c96a4`; the setup plan's remaining tickets move `src/beamtime/setup/` and `ops/admin.py`.
   Find symbols by name.
7. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading. The hash stays in git (`ticket.py status`).

## Order

```
S31 ─ C31 ─ P31 ─ L31 ─ R31 ─┬─ A31 ─ W31      (cli.md: P31, A31, W31 serialize)
                        └─ U31           (bundle)
                                  Z31    close
```

What's left runs in this order: S31 C31 P31 L31 R31 A31 W31 U31 Z31

## Decisions taken; say if you want otherwise

1. **Sources nest under the host** (your decision): `remotes.<host>.sources.<name>`. Rejected: flat remotes sharing
   a host entry, since the host is what the user thinks in.
2. **`path:` or `sources:`, never both** (your decision). A remote with `path:` keeps its one-level places; converting
   it to `sources:` changes its places, which the user does knowingly. Rejected: both allowed, a default source plus
   named ones.
3. **Places are `@host:source/path`** (your decision). `Place` stays settings-free, so a stored link reads the same on
   every machine. Rejected: `@host/source/path` resolved by settings, where a teammate with a different config
   would read a shared note differently.
4. **The routed source name is the string `host:source`** (proposed). Routing, answer placement (`ops/answers.py`),
   snapshots and URLs keep treating it as an opaque token; only the client layer knows hosts. Rejected: a two-field
   source through routing and answers, which touches every `Answer` and the web router.
5. **One connection per host** (your decision): one ssh connection and one `serve --stdio` per host, with requests
   naming their source. Rejected: one connection per source, since startup on cluster filesystems takes seconds and
   2FA is per connection without a ControlMaster.
6. **Data roots are a source kind** (your decision): `sources.<name>: {datasets: <root>, depth: 2}`. A plain string
   is a log dir. Data roots are configured and connected here; the datasets plan gives them operations.
7. **`serve` narrowing** (proposed): `serve gpu04:flows` names a source, `serve gpu04:flows/cln` narrows it to a
   group, and `serve cluster:scaling` on a `path:` remote narrows as today. The host's shape decides, and the
   settings are read here anyway (the command line, not a stored link).
8. **Snapshots of named sources** (proposed) live in `pulled/<host>--<source>/`, since `:` is not a portable folder
   name. The snapshot record keeps the routed name.
9. **Sidebar: host, then sources** (your decision). A `path:` remote stays one root as today. A data root shows as
   a child with a data icon and is not clickable until the datasets plan.
10. **Setup learns both** (your decision): `source add/rm/list` and the wizard (more log dirs per host, a data root,
    its depth).

## S. Spec

### S31. The design of named sources (sonnet + review) — code

- **Touches:** `docs/design/04-remotes.md` (§ Three modes 30–37, § Federation 71–86, § Routing and merging 120–156,
  § Naming remote groups 158–184, § Configuration 186–223, § Protocol 225–257, § Decisions 297), `docs/design/10-setup.md`
  (§ Remotes 343–387), `docs/design/08-cli-mcp.md` (§ User-only commands 89), `docs/design/01-storage.md`
  (§ Settings 63).
- **Read:** this plan's Brief and Decisions; `docs/design/04-remotes.md` whole (it is the document being changed).
- **Check:** `uv run pytest -q tests/test_docs.py`.
- **Done:** the four documents state decisions 1–10 as the design; no other file changes.
- **Risks:** a section still saying "a source is a named log dir" (§ Naming remote groups 173) → grep `named log dir`;
  the `:` narrowing of `serve cluster:scaling` described twice, contradicting decision 7 → grep `cluster:scaling`.
- **Stop if:** a decision contradicts something else in the design that this plan didn't consider (e.g. pulled
  snapshot naming in § Mode 3).

The spec comes before the code (CLAUDE.md: a deviation is written into the design before it lands).

1. `04-remotes.md` § Configuration: the two shapes with a YAML example each (the Goal's `gpu04` and today's
   `au002a`), the exclusivity rule, the data-root mapping `{datasets, depth}`, and which keys live in which level
   (`host`, `command`, `cache` in the user settings, `sources` in the project).
2. § Naming remote groups: places `@host:source/path`, the rule that `Place` needs no settings, and the routed name
   `host:source`. Replace "a source is a named log dir" with "a source is a named log dir or data root".
3. § Protocol: the `--source`/`--datasets` flags, the `source` field on request lines, `hello.sources`, the minor
   version bump, and that events carry `source`.
4. § Mode 1 and § Federation: one process per host; listings skip data roots; § Mode 3: snapshot folder naming.
5. `10-setup.md` § Remotes: per host, more log dirs (`+ Add a log dir`) and an optional data root with its depth. A
   named source's path goes to `beamtime.yaml`, as `path` does today.
6. `08-cli-mcp.md`: `source add <host:name> <host:/path> [--datasets] [--depth N]`, `source rm <host:name>`.

## C. Configuration

### C31. Settings and specs for named sources (sonnet + review) — code

- **Touches:** `src/beamtime/settings.py` (`REMOTE_KEYS` 27, `check_file` remote loop 276–287, `Settings.remotes`
  178–187), `src/beamtime/remote/client.py` (`Spec` 41–80), `src/beamtime/remote/sources.py` (`spec_of` 12–32
  removed, new `configured`), `src/beamtime/format/place.py` (new `host`, `name` properties),
  `tests/test_settings.py`, `tests/format/test_place.py`, new `tests/remote/test_sources.py`.
- **Read:** `docs/design/04-remotes.md` § Configuration, § Naming remote groups (as S31 left them).
- **Check:** `uv run pytest -q tests/test_settings.py tests/format/test_place.py tests/remote/test_sources.py`.
- **Done:** `configured()` on the Goal's settings returns `gpu04:flows`, `gpu04:md` (`kind="logdir"`), `gpu04:data`
  (`kind="datasets"`, `depth=2`) with the host's `host`/`command`/`cache`; a `path:` remote returns one spec named as
  the remote with `source=None`; `path` and `sources` together is a settings problem and the entry is skipped.
- **Risks:** a source name with `:`, `@`, `/` or `=` → `test_bad_source_name` (reuse `setup.remotes.remote_name_problem`
  56); `depth: 0` or a string → problem, default 2 (`test_depth_checked`); `enabled: false` on the host drops all
  its sources (`test_disabled_host`); `Place.parse("@local:data/x").source == "local:data"`, while `@local/x` still
  normalizes (`test_local_named`).
- **Stop if:** something besides the five callers of R31 reads `conf["path"]` from a remote entry.

1. `REMOTE_KEYS += ("sources",)`. In `check_file`, for a remote: both `path` and `sources` → problem
   `remote {name!r} has both path and sources; keep one`, delete `sources`. `sources` must be a mapping of
   name → str (log dir) or mapping `{datasets: str, depth: int >= 1}`; other shapes are problems and dropped.
2. `Spec` gains `host_key: str = ""` (defaults to `name` in `__post_init__`), `source: str | None = None`,
   `kind: Literal["logdir", "datasets"] = "logdir"`, `depth: int = 2`. `argv` is unchanged here (P31 extends it).
3. `remote/sources.py`: `configured(settings: Settings) -> dict[str, Spec]`: for each entry of `settings.remotes`,
   `path` → one spec as `spec_of` did, `sources` → one spec per source, named `f"{host}:{source}"`. A remote with
   neither → `OpError` with the message `spec_of` gives today, raised only when that name is used (keep a lazy
   error: return it in a second dict `broken: dict[str, str]`, or raise in `client_for`; pick one and test it).
   Delete `spec_of`; R31 moves its callers, and until then keep a two-line shim `spec_of(name, conf)` that calls
   `configured` and is removed in R31.
4. `Place.host` → the part of `source` before `:` (or the whole source), `Place.name` → the part after, else `None`.

## P. Protocol

### P31. `serve --stdio` answers for several sources (sonnet + review) — code

- **Touches:** `src/beamtime/serve/stdio.py` (`Remote` 32–118, `run` 121–155), `src/beamtime/cli/__init__.py` (the
  `serve` parser: `--stdio`, `--logdir`), `src/beamtime/serve/api.py` (`hello` 72–94), `src/beamtime/ops/context.py`
  (`Context`: new `kind`), `src/beamtime/remote/client.py` (`PROTOCOL`, `Spec.argv` 54–80), `tests/serve/test_stdio.py`,
  `docs/reference/cli.md` (generated).
- **Read:** `docs/design/04-remotes.md` § Protocol.
- **Check:** `uv run pytest -q tests/serve/test_stdio.py tests/remote`; `uv run python docs/site/reference.py`.
- **Done:** one `serve --stdio --source a=A --source b=B --datasets d=D` answers `runs` for `{"source": "a"}` from A
  and for `"b"` from B; no `source` with `--logdir L` answers from L; `hello` lists `[{name: a, kind: logdir}, ...]`;
  a `changed` event carries `source`; an operation on `d` answers code 2 with the data-root message.
- **Risks:** an unknown `source` → code 4 `no source <x> here (sources: a, b)` (`test_unknown_source`); `watch` with
  scopes on two sources catches each up in its own index (`test_watch_two_sources`); `--logdir` alone behaves
  exactly as before (the existing stdio tests unchanged); one cache per source when `--cache` is given:
  `resolve_cache(path, …)` is keyed by path already (`test_cache_per_source`).
- **Stop if:** the index or cache can't hold two log dirs in one process (shared module state in `index/`).

1. `Context` gains `kind: Literal["logdir", "datasets"] = "logdir"`.
2. CLI: `serve --stdio` takes `--source NAME=PATH` and `--datasets NAME=PATH` (`action="append"`), and `--logdir`
   becomes optional when either is given.
3. `stdio.run(*, logdir: str | None, sources: dict[str, str], datasets: dict[str, str], cache: str | None) -> int`
   builds one `Context` per source (the same cache logic per log dir; data roots get no index cache), keyed `None` for
   `--logdir`. `Remote(contexts=..., out=...)`.
4. `Remote.answer`: `ctx = self.contexts.get(request.get("source"))`, unknown → error code 4. For a datasets ctx,
   every method but `hello` raises the data-root `OpError`, and `api.dispatch` is not called.
5. `subscribe` takes `{"paths": [...], "source": NAME}` and keeps `watched: dict[str | None, set[str]]`. `watch`
   opens one `Index` per watched log-dir source and sends `{"event": "changed", "source": NAME, "changed": ...}`
   (no `source` key for `None`).
6. `hello` adds `sources: [{"name": n, "kind": k}]` (`None` → omitted). Raise `PROTOCOL`'s minor version.
7. `Spec.argv` takes the list of specs of its host (`argv(self, siblings: list["Spec"])`, or a module function
   `argv_for(specs)`): one `--source`/`--datasets` per named source, `--logdir` for a `path:` remote.

## L. Client

### L31. One connection per host (sonnet + review) — code

- **Touches:** `src/beamtime/remote/client.py` (`RemoteClient` 89–339: `name`, `describe` 119–131, `request`
  133–153, `send` 155–196, `connect` 198–235, `subscribe` 237–246, `read`), `src/beamtime/remote/sources.py`
  (`Sources` 57–84, `client_for` 91–111, new `SourceClient`), `tests/remote/conftest.py` (new `box2` fixture: one
  host, two sources), `tests/remote/test_federation.py`, `tests/remote/test_live.py`.
- **Read:** `docs/design/04-remotes.md` § Mode 1, § Protocol.
- **Check:** `uv run pytest -q tests/remote tests/serve/test_live.py`.
- **Done:** `Sources([spec_a, spec_b])` with one `host_key` starts one process (`test_one_process_per_host`);
  `runs` over `.` merges both sources' rows placed `@box:a/…` and `@box:b/…`; a change in `b` reaches the hub as
  `box:b`'s event; a host that loses its connection shows every one of its sources unreachable at once.
- **Risks:** an older remote whose `hello` lacks `sources` while specs name sources → `Unreachable` with
  `uv pip install -U beamtime` (`test_old_remote_refuses_sources`); a `path:` remote's requests carry no `source`
  field, so older remotes keep working (`test_path_remote_no_source_field`); subscriptions of two sources on one
  connection are both re-sent after a reconnect (`test_resubscribe_both`).
- **Stop if:** federation (`route.federate`) needs to know hosts, beyond skipping data roots.

1. `RemoteClient(*, specs: list[Spec], on_event)` is the host's connection; its argv comes from P31's builder, and
   `connect` checks `hello.sources` against its specs. `send` takes `source: str | None` and puts it on the request
   line when not `None`. `read` hands events to `on_event(source, event)`.
2. `SourceClient(*, conn: RemoteClient, spec: Spec)`: `name` (routed name), `spec`, `state`/`since`/`error`/`info`
   delegated to `conn`, `request(method, params, *, caller, timeout, whole)` → `conn.connect(); conn.send(..., source=spec.source)`,
   `describe()` → the conn's fields with `name=f"@{self.name}"`, `path=spec.path`, plus `kind` and `host_key`,
   `subscribe(paths)` → kept per source on the conn and sent as P31's `{"paths", "source"}`.
3. `Sources(specs, on_event)`: group specs by `host_key`, one `RemoteClient` each, `clients: dict[str, SourceClient]`
   by routed name; `close()` closes connections once. `client_for` builds its one-shot connection from `configured()`
   the same way, caching connections by `host_key` in `opened`.
4. `route.federate` and `route.elsewhere` skip clients with `spec.kind == "datasets"`.

## R. Routing and callers

### R31. Every caller takes its sources from `configured()` (sonnet) — code

- **Touches:** `src/beamtime/serve/server.py` (sources 210–231), `src/beamtime/views/render.py` (234–249),
  `src/beamtime/ops/admin.py` (`doctor` remote loop 280, `remote_checks` 311–362), `src/beamtime/ops/reading.py`
  (`sources` 1088–1104, `status` remotes line 1068), `src/beamtime/ops/context.py` (`remotes` 75–83),
  `src/beamtime/remote/via_serve.py` (`involves_remotes` 13–27), `src/beamtime/remote/sources.py` (`parse_arg`
  35–54; `spec_of` shim removed), `src/beamtime/remote/pull.py` (snapshot folder), `tests/remote/test_route.py`,
  `tests/remote/test_pull.py`, `tests/remote/test_no_local.py`, `tests/ops/test_ops.py`.
- **Read:** `docs/design/04-remotes.md` § Routing and merging, § Mode 3, § Naming remote groups.
- **Check:** `uv run pytest -q tests/remote tests/ops tests/serve`; `rg -n 'spec_of|settings\.remotes' src` lists only
  `settings.py` and `remote/sources.py`.
- **Done:** `serve gpu04:flows` and `serve gpu04:flows/cln` work as decision 7 says; `beamtime status` and `doctor`
  list one line per source, grouped by host; `pull @box:a/g` writes `pulled/box--a/` and answers for `@box:a` while
  `box` is down; `Context.remotes` lists routed names, so `default_source` with one host of one log-dir source (and
  no local) is that source.
- **Risks:** `default_source` with a host carrying a log dir and a data root: the data root doesn't count, so the log
  dir is the default (`test_default_ignores_data_root`); `parse_arg("gpu04:nope")` on a `sources:` host → `no source
  gpu04:nope (sources: gpu04:flows, gpu04:md)` code 2 (`test_unknown_named_source`); an ad-hoc `host:/abs/path`
  stays one unnamed source (`test_adhoc`).

1. `serve/server.py` and `views/render.py`: `specs = configured(ctx.settings)`, filtered by the command line's
   names through `parse_arg`.
2. `parse_arg(arg, specs: dict[str, Spec]) -> Spec`: split `host:rest`; if `host` is a `sources:` host, `rest`'s
   first segment is the source (`gpu04:flows/cln` → `gpu04:flows` scoped to `cln`); if a `path:` remote, `rest`
   is the scope as today; a `/`, `~` or `$` start stays ad hoc.
3. `Context.remotes` → `list(configured(self.settings))` when there are no `sources`; data roots excluded from
   `default_source`.
4. `admin.remote_checks(spec: Spec)` per source (one ssh probe per host, results reused); `reading.sources` adds
   `kind` and `host_key` from `SourceClient.describe`.
5. `pull.py`: snapshot folder `name.replace(":", "--")`; the record keeps `@<name>`.

## A. Admin commands

### A31. `source add`, `rm` and `list` for named sources (sonnet) — code

- **Touches:** `src/beamtime/ops/admin.py` (`source_add` 364–389, `source_list` 391–414, `source_rm` 416–433),
  `src/beamtime/ops/registry.py` (`SourceAddParams`, `SourceRmParams`), `src/beamtime/settings.py` (`write_remote`
  457–469, `remove_remote` 472–485), `src/beamtime/cli/__init__.py` (if flags need text), `tests/ops/test_ops.py`,
  `tests/test_cli.py`, `docs/reference/cli.md` (generated).
- **Read:** `docs/design/08-cli-mcp.md` § User-only commands; `docs/design/04-remotes.md` § Configuration.
- **Check:** `uv run pytest -q tests/ops tests/test_cli.py tests/test_docs.py`; `uv run python docs/site/reference.py`.
- **Done:** `source add gpu04:md gpu04:/scratch/md/beamtime` writes `remotes.gpu04.sources.md` in `beamtime.yaml`
  and `host`/`command` in the user settings; `--datasets` writes `{datasets: …}` (`--depth N` adds `depth`); `source
  rm gpu04:md` removes only that source and the host entry when it was the last; `source list` prints
  `@gpu04:md  logdir  gpu04:/scratch/md/beamtime`.
- **Risks:** adding a named source to a `path:` host → refused with `@gpu04 has a path; move it to sources: first`,
  nothing written (`test_add_to_path_host_refused`); `source add flows ...` without `host:` keeps today's behaviour
  (`test_add_unnamed`); re-adding an existing name replaces its path only (`test_readd`).

1. `SourceAddParams` gains `datasets: bool = False`, `depth: int | None = None`; a `name` with `:` is
   `host:source`.
2. `settings.write_source(path, host, source, value)` and `remove_source(path, host, source) -> bool`, keeping the
   rest of the file as written, like `write_remote`.
3. The command probe (`probe_command`) runs once per host, as today.

## W. Wizard

### W31. The wizard adds log dirs and a data root per host (sonnet + review) — code

- **Touches:** `src/beamtime/setup/flow.py` (the remote steps), `src/beamtime/setup/plan.py` (the settings changes for
  remotes), `src/beamtime/setup/remotes.py` (`probe` 106–122, `probe_host` 124–164: several paths per host),
  `src/beamtime/setup/__init__.py` (answers model: the remotes answer), `tests/setup/test_flow.py`,
  `tests/setup/test_plan.py`, `tests/setup/test_remotes.py`, `docs/reference/cli.md` (if `--remote` changes).
- **Read:** `docs/design/10-setup.md` § Remotes, § Answers, flags and settings, § Reconfiguring (as S31 left them);
  the setup plan's Decisions (`docs/plans/setup/setup-plan.md` § Decisions taken).
- **Check:** `uv run pytest -q tests/setup`.
- **Done:** in the cluster flow, a host can take several log dirs (each named; the first defaults to the project's
  name) and an optional data root with a depth (default 2); the plan writes the `sources:` shape; a host with one log
  dir and no data root keeps writing `path:` (today's shape); reconfiguring reads both shapes back.
- **Risks:** a saved answers file from before this ticket reconfigures without change (`test_old_answers`); the probe
  checks every path's filesystem type with one ssh call per host (`test_probe_many_paths`); a data root path that
  doesn't exist on the host is reported, not fatal (`test_missing_data_root`).
- **Stop if:** the setup plan's answers model can't take a list per host without a schema change of the saved answers;
  come back with the smallest option.

1. The answers model: a remote answer gains `sources: dict[str, str | dict]` next to `path`; the flag form is
   `--remote gpu04:md=gpu04:/path` and `--data-root gpu04:data=gpu04:/path[:depth]` (adjust to the existing flag
   grammar of `10-setup.md` § Answers).
2. The flow: after a host's first log dir, ask `Another log dir on gpu04?` (repeat) and `A data root on gpu04?`
   (path, then `How deep are the cards? [2]`).
3. The plan: one host with exactly one log dir and no data root → `path:`; otherwise `sources:`.

## U. Web UI

### U31. Hosts and their sources in the sidebar (sonnet + review) — code

- **Touches:** `web/src/shell/tree.ts` (`buildTree` 21–50), `web/src/shell/sidebar.ts`, `web/src/router.ts`
  (source parsing 33–37, 58–66, `sourcedRun` 80–83, root 85–91), `web/src/ui/` icons (a data-root symbol from
  lucide), `web/test/tree.test.ts`, new `web/test/router.test.ts`, `src/beamtime/serve/static/` (rebuilt), `tests/serve/test_browser.py`.
- **Read:** `docs/design/07-web-ui.md` § the sidebar; `design/README.md`; `design/components/` for the tree.
- **Check:** `cd web && npm ci && npm test && npm run build`; `uv run pytest -q tests/serve`.
- **Done:** sources `box:a`, `box:b` show as one `box` node with children `a`, `b`; a data root child shows the
  data icon and no link; a `path:` remote is one root as before; `/f/@box:a/g` and `/r/@box:a/<id>` round-trip
  through the router; the shell stays under 120 KB compressed.
- **Risks:** a host whose sources are all unreachable shows the host's state once, not per child
  (`web/test/tree.test.ts`); `sourcedRun` on a `@box:a` page keeps `@box:a` (`web/test/router.test.ts`); a remote
  literally named `a:b`, which can't exist since names can't contain `:`, needs no case.

1. `buildTree(rows, sources)`: group source states by `host_key` (from `meta.sources`); a host with named sources
   is a node `{name: host, children: [one root per source]}`; collapsing works as for hosts today.
2. The router takes the source segment as is (it already splits at `/`); add tests for `:`.

## Z. Close

### Z31. Close (sonnet) — code

- **Touches:** `CHANGELOG.md`, `docs/guides/remotes.md`, `docs/guides/cluster.md`, `docs/guides/settings.md`,
  `CLAUDE.md` (Layout: `remote/` line).
- **Check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`;
  `uv run python scripts/release.py`.
- **Done:** the changelog lists the breaking changes below; the guides show the `sources:` shape and `@host:source`
  places; the Goal's "Confirmed by" checks pass.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| Protocol minor version | hub and remote any 0.3 | a hub using named sources needs the remote at this version | `uv pip install -U beamtime` on the host; `path:` remotes keep working with older remotes |
| `serve --stdio --logdir` | required | optional when `--source`/`--datasets` are given | none |
| `remote.sources.spec_of` | public helper | removed; `configured(settings)` | internal |

## Not verified

- That the index and cache modules hold no per-process state that breaks with two log dirs in one process (P31
  checks it first, `test_watch_two_sources`).
- That the setup plan's answers model, finished after the base commit, can take several sources per host without a
  saved-answers schema change (W31 Stop if).
- That one `serve --stdio` per host is fast enough when it indexes two log dirs lazily (no measurement; the Docker
  test is the place to time it).
