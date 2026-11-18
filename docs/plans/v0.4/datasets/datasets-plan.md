# Datasets: read-only datacards, their runs and their views

Base commit `84c96a4`, branch `setup`. Proposed 2026-11-16, based on the dataset request
(`docs/plans/v0.4/datasets/beamtime-dataset-request.md`: 20 cards and 14 archive stubs, 9 of 10 provenance links
unknown, `consumers:` kept by hand), and on the interview of 2026-11-16. It runs **after the hosts plan**
(`docs/plans/v0.4/hosts/hosts-plan.md`), whose named sources (`@host:source`, one connection per host, data roots as a
source kind) it builds on. Behaviour changes are allowed; they are listed in [Breaking changes](#breaking-changes).

Run a ticket with `/run-ticket docs/plans/v0.4/datasets/datasets-plan.md <ID>` in a fresh session; review tickets marked
`+ review` with `/review-ticket docs/plans/v0.4/datasets/datasets-plan.md <ID>` on a stronger model.
`ticket.py status docs/plans/v0.4/datasets/datasets-plan.md` shows what's done and what's next.

## Goal

- **Done means:** a data root (a folder of `datacard.yaml` files on a host or on this machine) is a source of
  datasets. `beamtime dataset list` shows every dataset of every data root with name, kind, status, size and the
  state of its provenance link (`resolved`, `missing`, `elsewhere`, `unknown`). `beamtime dataset show
  @gpu04:data/cln-ms` shows the card, its files with sizes, its parents and children, and its producing group.
  `beamtime runs --uses @gpu04:data/cln-ms` lists the runs whose config or command names a path inside the dataset.
  In views, a `datasets` query lists what a group produced and used. The web UI has a page per dataset and per data
  root, and both are views that agents customise and save like group views. Beamtime never writes a card; it writes
  only `view/` and `blocks/` into a data root. Agents learn all of this from `beamtime guide datasets`.
- **Confirmed by:** `uv run pytest -q tests/format/test_datacard.py tests/ops/test_datasets.py
  tests/query/test_uses.py tests/remote/test_datasets.py tests/views/test_dataset_views.py tests/serve`. The end-to-end
  test `tests/ops/test_datasets.py::test_request_loop` rebuilds the request's loop: a data root with a `generated`
  card naming a group that exists (→ `resolved`), one naming a missing group (→ `missing`), one of another project
  (→ `elsewhere`), a `derived` card, and runs whose configs reach the generated dataset through a `data/` symlink
  (→ found by `--uses`). It runs once locally and once over a `command`-transport host. In the browser test, the
  dataset page renders the default view and a saved one.
- **Out of scope:** writing, validating or migrating cards (`check-datacards.py` stays the validator); recording
  inputs in the SDK; moving or tracking dataset bytes; notes, proposals or memory on datasets; consumers on another
  filesystem than the data root's; a group page listing datasets by default (the query exists, the built-in group view
  is unchanged).

## Findings

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | 9 of 10 cards' `provenance.beamtime` is `unknown`, and the tenth (`cln-ms`) could not be checked | no reader for cards; agents may not run `beamtime` to check a group | real data | V91 |
| 2 | `consumers:` is kept by hand and goes stale | no link from run configs to dataset folders | real data | Q91 |
| 3 | A run's config often reaches the data through a project's `data/` symlink (`data/cln-ms/traj.trr`) | paths are relative to the run's `cwd` and cross a symlink | real data | Q91 |
| 4 | Views live under a log dir and resolve pages through the index | `views/store.py` `view_dir` (30–36) is `ctx.logdir / path / view`; `serve/api.py` `page_of` (234–250) resolves with the index | code | W91 |
| 5 | `cwd` and `command` are in the index | `index/ingest.py` 109–119 stores the whole `_run.json` as `runs.info` | code | Q91 |
| 6 | Datasets as zero-metric runs would be deleted | `beamtime gc` removes ended runs without metrics (`ops/admin.py` `gc`) | code | — (rejected in the request) |

## Brief

- **Cards** (F91): `src/beamtime/format/datacard.py` (Python 3.10, standard library plus PyYAML) reads
  `datacard.yaml` into `Card`, discovers card folders up to `depth` (default 2) and sums the sizes of the card's
  `files:`. It types the core keys only and keeps every other key in `extra`. A card that isn't a YAML mapping is a
  `Card` with `problems` and is never fatal.
- **Data roots** (K91): a source of kind `datasets` (hosts plan) gets a `Context` with `kind="datasets"` and
  `logdir` = the data root. Operations flagged `datasets=True` in the registry run there and every other one refuses.
  This machine's data roots come from a top-level `sources:` (`sources: {data: {datasets: ~/data}}`) and are the
  routed sources `local:<name>`, answered in-process.
- **Two layers of operations** (O91, V91): routed API methods `dataset_rows` and `dataset_card` answer on a data root
  from its files alone. The user-facing `dataset_list` and `dataset_show` run on the hub (`routed=False`): they
  call the routed methods, then add what needs other sources, namely link states and consumers. CLI `beamtime
  dataset list|show`, MCP `dataset_list`/`dataset_show`.
- **Places** (O91): a dataset's place is its data root plus its folder, `@gpu04:data/cln-ms` or `@local:data/old/x`.
  `ops/answers.py` gets one `Answer` per new kind and names the place fields.
- **Provenance** (V91): `{project, group}` resolves against a source named `project`: the `<name>` of `host:<name>`,
  a one-level remote named so, or this machine when `ctx.root.name == project`. The group is checked with
  `query.resolve`, so moves are followed. States: `resolved`, `missing`, `elsewhere` (no such source, or it is
  unreachable: `reason` says which), `unknown` (`unknown` or absent).
- **Consumers** (Q91): `Selection.uses: str | None`, a dataset place. The hub resolves it to the dataset folder's real
  path and the data root's host, and sends `uses_dir` only to the log-dir sources on that host (and this machine for
  a local root). There, a run matches when a `_config.json` string or a `command` argument, joined to `cwd` when
  relative and passed through `os.path.realpath`, is the folder or lies inside it. A SQL `LIKE '%<folder name>%'` on
  `config` and `info` prefilters.
- **Dataset views** (W91, W92): pages resolve to card folders. A dataset shows its own newest view, else the data
  root's `view/` (the one inheritance in Beamtime, written into `05-views.md`), else the built-in
  `defaults.dataset_view` (`card`, `files`, a run `table` with `uses: .`). The data root's own page shows
  `dataset_list`. Views and library blocks are saved into the data root through the usual `write_version`.

Done, for every ticket: its Done line holds; its Check passes; the spec documents say what the code does; its heading
is marked done in the ticket's own commit.

## How to execute

1. Checks: `uv run ruff check . && uv run ruff format --check . && uv run pytest -q` (4 xdist workers; `-n0`
   serially). Card fixtures are written by a `data_root` fixture in `tests/conftest.py` (F91); remote tests use the
   `command` transport (`tests/remote/conftest.py`). After a ticket touching `cli/`, `settings.py` or
   `ops/registry.py`: `uv run pytest -q -n0 tests/test_budgets.py`. SDK-side code (`format/datacard.py`) also on
   3.10: `UV_PROJECT_ENVIRONMENT=/tmp/bt-venv310 uv run --python 3.10 pytest -q tests/format tests/test_boundaries.py`.
2. Generated files: `docs/reference/cli.md` (`uv run python docs/site/reference.py`) after CLI changes (O91, Q91, T91);
   these run one after another. After any change in `web/`: `cd web && npm ci && npm test && npm run build` and
   commit `src/beamtime/serve/static/` (U91, U92, one after another). Skills after a guide change:
   `uv run python scripts/build-plugin` (G91).
3. Rules: CLAUDE.md's Python style; `format/` stays 3.10 with the standard library plus PyYAML, and PyYAML is
   imported inside functions (`tests/test_boundaries.py`, `tests/test_budgets.py`); every `@` is parsed by `Place`;
   Beamtime never opens a `datacard.yaml` for writing (a test greps for it, F91). Never touch `tests/golden/schema1/`.
4. Spec: the new `docs/design/11-datasets.md` plus the sections S91 changes. S91 writes them first; later deviations
   go back into them in the same commit.
5. Ticket budget: 140k tokens per ticket session; split a ticket that would exceed it.
6. Line numbers are at `84c96a4`, before the hosts plan. The hosts plan changes `remote/`, `serve/stdio.py`,
   `ops/context.py` and `settings.py`, so find symbols by name.
7. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading. The hash stays in git (`ticket.py status`).

## Order

```
S91 ─┬─ F91 ─┐
    └─ K91 ─┴─ O91 ─ V91 ─ Q91 ─ Q92 ─ W91 ─ W92 ─ U91 ─ U92 ─ T91 ─ G91 ─ Z91
F91 and K91 are independent; cli.md: O91, Q91, T91; bundle: U91, U92.
```

What's left runs in this order: S91 F91 K91 O91 V91 Q91 Q92 W91 W92 U91 U92 T91 G91 Z91

## Decisions taken; say if you want otherwise

1. **Read-only cards** (your decision): Beamtime reads `datacard.yaml` and never writes it; no SDK change. Rejected:
   SDK links (`run.uses`) and Beamtime-owned cards.
2. **A minimal core spec** (your decision): `name` (default: the folder), `kind`, `status`, `created`,
   `description`, `provenance.beamtime {project, group}` or `unknown`, `derived_from`, `files`. Beamtime checks
   only their types and keeps every other key. Rejected: enforcing required blocks per kind, which is
   `check-datacards.py`'s job.
3. **Discovery** (your decision): a folder up to `depth` (default 2, set per data root in the settings and the wizard)
   below the root holding `datacard.yaml` is a dataset. The walk stops at a card and skips `.`/`_` names, `view/` and
   `blocks/`. Rejected: a hard-coded `old/`, and an unbounded walk over trajectory folders.
4. **Data roots are sources** (your decision, hosts plan): `@host:data/<folder>`; this machine's are `@local:<name>`.
5. **Provenance in four states** (your decision): `resolved`, `missing`, `elsewhere`, `unknown`; an unreachable
   source gives `elsewhere` with `reason: unreachable` (proposed). The project is matched by source name (your
   decision). Rejected: a `project:` key per source, and `hello` reporting it.
6. **Consumers by resolved paths** (your decision): config strings and `command` arguments, relative to `cwd`,
   through `realpath`, inside the dataset folder. Only runs on the data root's host are checked (proposed; another
   filesystem can't be resolved). The folder-name prefilter (proposed) misses a path that reaches the dataset
   through a symlink with a different name (named in the guide).
7. **`uses` is a selection filter** (your decision) on `Selection`, so `runs`, `series`, `keys` and every run widget
   take it. Rejected: a `consumers` query kind with its own run table.
8. **Size is the card's files** (your decision): the sum of `stat` over the `files:` that exist; missing files are
   counted and named. Rejected: walking the folder.
9. **Dataset pages are views, stored in the data root** (your decision): `<root>/<folder>/view/`, with the root's
   `view/` as the default for all its datasets. Library blocks come from `<root>/blocks/`. Rejected: views in each
   project's log dir.
10. **A `datasets` query kind** (your decision): `{kind: datasets, from: <group>, rel: produced | used}` for group
    views; the built-in group view doesn't use it.
11. **Two layers of operations** (proposed): data roots answer from their files (`dataset_rows`, `dataset_card`); the
    hub adds link states and consumers. Rejected: one routed operation that calls back to the hub, which the
    one-way data flow of `04-remotes.md` forbids.
12. **Size and size errors are never fatal** (proposed): an unreadable file counts as missing; a card with problems
    is listed with them.

## S. Spec

### S91. The design of datasets (sonnet + review) — code

- **Touches:** new `docs/design/11-datasets.md`; `docs/design/00-overview.md` (the layer list); `docs/design/03-index.md`
  (§ Selecting runs 269: `uses`; § Query kinds 308: `dataset`, `datasets`); `docs/design/05-views.md` (§ Built-in
  blocks / Catalog 175: `card`, `files`, `dataset_list`; a § Dataset pages; § Location 565 of library blocks);
  `docs/design/07-web-ui.md` (§ Pages and URLs 164: `/d/...`); `docs/design/08-cli-mcp.md` (§ Reading 29:
  `dataset list|show`); `docs/design/04-remotes.md` (data roots answer `datasets` operations); `docs/design/01-storage.md`
  (§ Settings 63: top-level `sources:`).
- **Read:** this plan's Goal, Brief and Decisions; `docs/plans/v0.4/datasets/beamtime-dataset-request.md`;
  `docs/design/00-overview.md` (to match its layer document style).
- **Check:** `uv run pytest -q tests/test_docs.py`.
- **Done:** `11-datasets.md` specifies decisions 1–12 with the card example of the request; the other documents
  point to it and state their part; no code changes.
- **Risks:** `05-views.md` § Views in storage / `01-storage.md` 156 say "No inheritance"; the data-root default must
  be written as the one exception in both (grep `No inheritance`); the provenance states must read the same in
  `11-datasets.md`, `08-cli-mcp.md` and the guide later (grep `elsewhere`).
- **Stop if:** a decision collides with the hosts plan as it landed (e.g. it named data-root specs differently).

1. `11-datasets.md`, sections: Principles (read-only; files are the truth; never fatal), The card (core table,
   example), Discovery, Data roots (settings, places, `local:`), Operations (two layers, answer shapes),
   Provenance, Consumers (matching rule, host limit, prefilter), Views (storage, default, inheritance exception,
   widgets), Testing, Decisions.
2. The answer shapes, fixed here for O91 and V91:
   `dataset_list` rows `{place, name, kind, status, created, description, size, missing, link: {project, group,
   state, place?, reason?}, problems}`; `dataset_show` `{place, dir, card: {...all keys}, files: [{name, size,
   exists}], parents: [{text, place?}], children: [place], link, problems}`.

## F. Cards

### F91. `format/datacard.py`: read, discover, size (sonnet) — code

- **Touches:** new `src/beamtime/format/datacard.py`, `src/beamtime/format/constants.py` (`CARD = "datacard.yaml"`),
  new `tests/format/test_datacard.py`, `tests/conftest.py` (new `data_root` fixture), `tests/test_boundaries.py`
  (the module in the 3.10 set, and the never-write check).
- **Read:** `docs/design/11-datasets.md` § The card, § Discovery; `src/beamtime/format/io.py` (how other readers
  load YAML and JSON).
- **Check:** `uv run pytest -q tests/format/test_datacard.py tests/test_boundaries.py`; the 3.10 command of How to
  execute.
- **Done:** the request's `cln-ms` card reads with every core field typed and `verification`, `consumers` in
  `extra`; `discover(root, 2)` finds `cln-ms` and `old/ala2-ms` and not a card at depth 3; `size` sums existing
  files and names missing ones.
- **Risks:** a card that is a list or broken YAML → `Card` with `problems`, `name` from the folder
  (`test_broken_card`); `files:` naming `../x` or an absolute path → a problem, not read (`test_files_escape`);
  `created: 2026-10-04` parsed by YAML as a `date` → kept as the ISO string (`test_created_date`); a card folder
  inside a card folder is not a second dataset (`test_no_nested`).

1. `@dataclass(frozen=True, kw_only=True) class Card`: `path: str` (relative to the root, `/`-separated), `name`,
   `kind`, `status`, `created`, `description: str | None`, `provenance: dict[str, str] | Literal["unknown"] | None`,
   `derived_from: list[str]`, `files: dict[str, dict[str, Any]]`, `extra: dict[str, Any]`, `problems: list[str]`.
2. `read_card(root: Path, rel: str) -> Card`; a wrongly typed core key → a problem and the key moves to `extra`.
3. `discover(root: Path, depth: int = 2) -> list[str]`: sorted relative paths; `os.scandir`, no symlinked folders
   followed (a link loop on shared roots).
4. `size(root: Path, card: Card) -> tuple[int, list[str]]`: bytes of the existing files, missing names.
5. `data_root` fixture: writes four cards (generated resolved, generated missing, other project, derived from the
   first) with small files, plus `old/<archived>`.

## K. Data roots

### K91. Data roots answer dataset operations; this machine's data roots (sonnet + review) — code

- **Touches:** `src/beamtime/ops/registry.py` (`Op`: new `datasets: bool = False`), `src/beamtime/serve/stdio.py`
  (the data-root refusal the hosts plan added), `src/beamtime/settings.py` (top-level `sources:` checked; `DEFAULTS`),
  `src/beamtime/remote/sources.py` (`configured`: `local:<name>` specs, transport `here`), `src/beamtime/remote/route.py`
  (`routed`: a `local:` source answered in-process; federation of `datasets` listings over data roots only),
  `src/beamtime/ops/context.py` (`Context.for_data_root(root: Path, *, settings) -> Context`), new
  `tests/remote/test_datasets.py`, `tests/test_settings.py`.
- **Read:** `docs/design/11-datasets.md` § Data roots; `docs/design/04-remotes.md` § Routing and merging.
- **Check:** `uv run pytest -q tests/remote tests/test_settings.py tests/ops/test_registry.py`.
- **Done:** a stub op flagged `datasets=True` (a test-only registry entry, or `hello`) answers on `@local:data` in
  process and on `@box:data` over the connection; a run op on either refuses with the hosts plan's message; a
  `datasets` listing of `.` asks every data root and no log dir; a run listing of `.` asks no data root.
- **Risks:** `sources:` naming a log dir string locally → a settings problem (only data roots locally)
  (`test_local_logdir_refused`); `Place.parse("@local:data")` is not `@local` (`test_local_named_not_local`); a
  `local:` source never opens a process (`test_local_in_process`).

1. Settings: top-level `sources: {<name>: {datasets: <path>, depth: <int>}}`, in either level; `~`, `${VAR}`,
   `{user}` expanded with `expand_path`.
2. `configured()` adds `local:<name>` specs with `transport="here"`; `route.routed` answers them with
   `Context.for_data_root`, never through a client.
3. `Op.datasets`: on a datasets context, ops with it run, others raise the refusal. `stdio` uses the same check.
4. `route.federate`: when the method's op has `datasets=True`, ask data-root sources (and `local:` ones)
   instead of log dirs.

## O. Operations

### O91. `dataset list` and `dataset show` from the files (sonnet + review) — code

- **Touches:** new `src/beamtime/ops/datasets.py` (`rows`, `card`, `dataset_list`, `dataset_show`),
  `src/beamtime/ops/registry.py` (`DatasetListParams`, `DatasetShowParams`, four `Op`s), `src/beamtime/ops/answers.py`
  (entries for `dataset list`, `dataset show`), `src/beamtime/remote/__init__.py` (`TARGETS` 12: add `dataset`),
  `src/beamtime/cli/` (text output of both), new `tests/ops/test_datasets.py`, `tests/ops/test_registry.py`,
  `tests/test_cli.py`, `docs/reference/cli.md` (generated).
- **Read:** `docs/design/11-datasets.md` § Operations; `docs/design/08-cli-mcp.md` § Output; `ops/answers.py`'s
  module docstring and one listing entry (`runs`).
- **Check:** `uv run pytest -q tests/ops tests/test_cli.py tests/remote/test_datasets.py tests/test_docs.py`;
  `uv run pytest -q -n0 tests/test_budgets.py`.
- **Done:** `beamtime dataset list` prints one line per card of every data root, `beamtime dataset show
  @local:data/cln-ms` the card. Both work as MCP tools and over a `command`-transport host. `link.state` is
  `unknown` or `pending` here (V91 resolves it). Parents named by a sibling card's name or path become places, and
  other parents stay text.
- **Risks:** two cards with the same `name` in one root → both listed, `show` by name refuses with both places
  (`test_duplicate_names`); `dataset show cln-ms` without a source resolves when exactly one data root has it
  (`test_show_by_bare_name`); a remote answer's `place` and `parents[].place` come back placed on the source
  (`test_remote_places`).

1. Routed, `datasets=True`: `dataset_rows(ctx, p) -> {kind: "dataset list", rows, meta}` and
   `dataset_card(ctx, p) -> {kind: "dataset show", ...}`, as S91 fixed them, `dir` = `realpath` of the folder.
2. Hub, `routed=False`: `dataset_list(ctx, DatasetListParams(from_=".", where: dict))` calls `dataset_rows` through
   `remote.reach` (federated over data roots), sorts by place; `dataset_show(ctx, DatasetShowParams(dataset: str))`
   resolves a bare name over all data roots, then calls `dataset_card`. Both call `link_states` (V91; here a stub
   that returns rows unchanged).
3. CLI: `beamtime dataset list [--where k=v]` columns `place kind status size link`; `dataset show <dataset>`
   prints the core keys, then `files`, `parents`, `children`, then `extra` as YAML.

## V. Provenance

### V91. Link states against known sources (sonnet + review) — code

- **Touches:** `src/beamtime/ops/datasets.py` (`link_states`, `project_source`), `tests/ops/test_datasets.py`.
- **Read:** `docs/design/11-datasets.md` § Provenance; `src/beamtime/query/resolve.py` (`resolve` 25).
- **Check:** `uv run pytest -q tests/ops/test_datasets.py tests/remote/test_datasets.py`.
- **Done:** the `data_root` fixture's four cards show `resolved` (with `place` of the group), `missing`, `elsewhere`,
  `unknown` locally and with the groups on a `command`-transport host named after the project.
- **Risks:** a group moved with `beamtime mv` resolves to its new place (`test_link_follows_move`); the project's
  source unreachable → `elsewhere`, `reason: unreachable`, no error (`test_link_unreachable`); 20 cards of one project
  cost one call per distinct group, not per card (`test_link_calls_batched`).

1. `project_source(ctx, project: str) -> str | None`: a routed name `host:<project>`, a one-level remote `<project>`,
   or `None` (this machine) when `ctx.root.name == project and ctx.has_local`; else `elsewhere`.
2. `link_states(ctx, rows)`: group the rows by `(source, group)`, one `groups` call with `from` = the group each
   (code 4 → `missing`, `Unreachable` → `elsewhere`/`unreachable`), fill `link.state`, `link.place`.

## Q. Queries

### Q91. `uses`: runs that read a dataset (sonnet + review) — code

- **Touches:** `src/beamtime/query/models.py` (`Selection` 102–107: `uses`, internal `uses_dir`), `src/beamtime/query/select.py`
  (`select_runs` 185: the filter; new `reads_inside(info, config, folder) -> bool`), `src/beamtime/remote/route.py`
  (`with_uses`: resolve, send to the right sources), `src/beamtime/views/model.py` (`Node` 20–37: `uses`),
  `src/beamtime/views/compile.py` (pass `uses` into queries), `src/beamtime/ops/registry.py` (`RunsParams` gets it from
  `q.Runs`), `src/beamtime/cli/` (`--uses`), new `tests/query/test_uses.py`, `tests/remote/test_datasets.py`,
  `docs/reference/cli.md` (generated).
- **Read:** `docs/design/11-datasets.md` § Consumers; `docs/design/03-index.md` § Selecting runs.
- **Check:** `uv run pytest -q tests/query tests/remote/test_datasets.py tests/views`.
- **Done:** `runs --uses @local:data/cln-ms` lists the fixture's runs whose config names `data/cln-ms/traj.trr`
  through a `data` symlink in their `cwd`, and those with the absolute path in `command`. Runs naming another
  dataset are left out. Over a `command`-transport host the same holds, and a log dir on another host is not
  asked (`meta.uses` says so).
- **Risks:** `/data/cln-ms-old/x` must not match `cln-ms` (`test_prefix_not_inside`); a relative path in a run
  without `cwd` (old runs) is skipped (`test_no_cwd`); config strings nested in lists and dicts are all checked
  (`test_nested_config`); `uses` naming no dataset → code 4 with the closest names (`test_unknown_dataset`).

1. `Selection.uses: str | None = None` (a dataset place) and `uses_dir: str | None = None` (set by the hub only;
   from a client it is refused).
2. `route.with_uses(params, ctx)`: `dataset_card` → `dir` and the data root's host key; send the query with
   `uses_dir` to log-dir sources on that host (`local:` root → this machine's log dir) and skip the others,
   adding `meta.uses = {dataset, checked: [sources], skipped: [sources]}`.
3. `select_runs`: with `uses_dir`, add the SQL prefilter on `config` and `info` with the folder's basename, then
   `reads_inside` on each candidate: every string leaf of the config and every `command` argument (also the part
   after `=` in `--data=x`), joined to `info.cwd` when relative, `os.path.realpath`, equal to `uses_dir` or under
   `uses_dir + os.sep`.

### Q92. `dataset` and `datasets` query kinds (sonnet + review) — code

- **Touches:** `src/beamtime/query/models.py` (new `Dataset`, `Datasets`), `src/beamtime/query/kinds.py` (`KINDS`
  730: `dataset_kind`, `datasets_kind`), `src/beamtime/ops/context.py` (`data_roots: dict[str, Path]`: this
  process's data roots), `src/beamtime/serve/stdio.py` (fill `data_roots` from the sibling `--datasets`),
  `src/beamtime/ops/answers.py`, `tests/query/test_uses.py`, `tests/remote/test_datasets.py`.
- **Read:** `docs/design/03-index.md` § Query kinds; `docs/design/11-datasets.md` § Operations.
- **Check:** `uv run pytest -q tests/query tests/remote/test_datasets.py`.
- **Done:** `{kind: dataset}` on a dataset page answers its card and files; `{kind: datasets, from: <group>, rel:
  used}` lists the datasets the group's runs read, as places on the data root; `rel: produced` lists those whose
  link resolves to the group or below; both locally and over a `command`-transport host.
- **Risks:** `used` on a host with two data roots maps each folder to the right root (`test_used_two_roots`);
  `produced` needs link states, so it runs on the hub after V91's call (`test_produced_on_hub`); a group with no
  runs → empty rows, not an error.

1. `Dataset(Struct)`: `from_` only (the page's dataset). `Datasets(Selection)`: `rel: Literal["produced", "used"]`.
2. `used` runs on the group's source: for each selected run, the strings of Q91 resolved, matched against every
   card folder of `ctx.data_roots` (discovered once per call); answer `{rows: [{source_name, path, runs}]}`. The
   hub places them as `@<host>:<source_name>/<path>`.
3. `produced` runs on the hub: `dataset_list` rows with `link.place` under the group.

## W. Views

### W91. Dataset pages and the default dataset view (sonnet + review) — code

- **Touches:** `src/beamtime/serve/api.py` (`page_of` 234–250, `view` 207), `src/beamtime/views/store.py` (`shown`
  156–224: the data-root fallback, no record blocks on datasets), `src/beamtime/views/defaults.py` (new
  `dataset_view`, `data_root_view`), `src/beamtime/views/model.py` (new `Card`, `Files`, `DatasetList` widgets),
  `src/beamtime/views/compile.py` (the three widgets; on a dataset page `uses: .` → the page's dataset),
  `src/beamtime/views/validate.py`, new `tests/views/test_dataset_views.py`.
- **Read:** `docs/design/05-views.md` § Dataset pages, § Built-in blocks; `docs/design/11-datasets.md` § Views.
- **Check:** `uv run pytest -q tests/views tests/serve/test_app.py`.
- **Done:** `view` for `@local:data/cln-ms` compiles the built-in dataset view, or the root's `view/` newest when
  one exists, or the dataset's own; for `@local:data` it compiles `data_root_view` (`dataset_list`); `view show` and
  `view history` work on both; a page for a folder without a card is code 4.
- **Risks:** a run `table` on a dataset page with `from: .` federates over log dirs, never the data root
  (`test_table_from_dot_on_dataset`); a saved root view with `uses: .` shows each dataset's own runs
  (`test_root_view_per_dataset`); notes and memory blocks are not appended on dataset pages (`test_no_record_blocks`).
- **Stop if:** `compile_view` needs the page's source to tell a dataset page from a group page and has no way to get
  it; come back with the smallest change to its signature.

### W92. Saving dataset views and library blocks into a data root (sonnet + review) — code

- **Touches:** `src/beamtime/ops/views.py` (`bundle_group` 310, `bundled` 321, `view_put` 387, `save_draft` 508,
  `write_version` 548), `src/beamtime/ops/blocks.py` (library save to `<root>/blocks/`),
  `src/beamtime/views/library.py` (lookup: the dataset, then the root), `src/beamtime/ops/registry.py` (the view and
  block ops get `datasets=True`), `tests/views/test_dataset_views.py`, `tests/remote/test_views.py`.
- **Read:** `docs/design/04-remotes.md` § Drafts on a remote; `docs/design/05-views.md` § Location.
- **Check:** `uv run pytest -q tests/views tests/remote/test_views.py tests/ops`.
- **Done:** `view new @local:data/cln-ms` → edit → `view save` writes `<root>/cln-ms/view/<id>.yaml` with
  `author`/`user`; `view save @local:data` writes the root default; the same over a `command`-transport host through
  the bundle path; a library block saved for the data root is found from a dataset view.
- **Risks:** a read-only data root → `OpError` naming the folder and `chmod`, no partial file
  (`test_read_only_root`); `datacard.yaml` is never opened for writing (F91's grep test, run here too); a bundle for
  a dataset place resolves by card, not by index (`test_bundle_dataset`).

## U. Web UI

### U91. The `card`, `files` and `dataset_list` blocks (sonnet + review) — code

- **Touches:** new `web/src/blocks/card.ts`, new `web/src/blocks/files.ts`, new `web/src/blocks/datasets.ts`, the block
  registry in `web/src/blocks/`, `web/src/ui/` (config tree reuse for `extra`), new `web/test/datasets.test.ts`,
  `src/beamtime/serve/static/` (rebuilt).
- **Read:** `design/README.md`, `design/components/` (tables, trees, badges); `docs/design/05-views.md` § Dataset
  pages; `web/src/blocks/` of `config` and `table` (closest existing blocks).
- **Check:** `cd web && npm ci && npm test && npm run build`.
- **Done:** `card` shows core fields, the link state as a badge (resolved, missing, elsewhere, unknown) with the
  group's link, parents and children as links, and `extra` as the config tree; `files` shows name, size and a
  missing mark; `dataset_list` is a sortable table linking each dataset; the shell stays under 120 KB compressed.
- **Risks:** an `extra` value that is a long list renders collapsed (`datasets.test.ts`); a missing link place
  renders the group as text, not a dead link.

### U92. Dataset pages, URLs and the sidebar (sonnet + review) — code

- **Touches:** `web/src/router.ts` (`/d/<source>/<path>`), `web/src/shell/page.ts`, `web/src/shell/tree.ts` and
  `sidebar.ts` (the data-root node becomes a link with a count), `web/src/shell/palette.ts` (datasets in ⌘K),
  `web/test/tree.test.ts`, `web/test/router.test.ts` (new in the hosts plan), `src/beamtime/serve/static/` (rebuilt),
  `tests/serve/test_browser.py`.
- **Read:** `docs/design/07-web-ui.md` § Pages and URLs, § Shell, § Navigation.
- **Check:** `cd web && npm ci && npm test && npm run build`; `uv run pytest -q tests/serve`.
- **Done:** `/d/@local:data/cln-ms` shows the dataset's view with the version menu and save, like a group page;
  `/d/@local:data` the data root's; the sidebar's data root links there with its dataset count; ⌘K finds datasets
  by name; the browser test renders both.
- **Risks:** a run link inside a dataset page's table goes to `/r/@host:src/<id>`, not to the data root
  (`router.test.ts`); live updates don't subscribe on data roots (no index there).

## T. Setup

### T91. This machine's data roots in the wizard (sonnet) — code

- **Touches:** `src/beamtime/setup/flow.py`, `src/beamtime/setup/plan.py`, `src/beamtime/setup/scan.py` (count
  cards under a candidate path with `discover`), `tests/setup/test_flow.py`, `tests/setup/test_plan.py`,
  `docs/reference/cli.md` (if a flag is added).
- **Read:** `docs/design/10-setup.md` § Remotes (the hosts plan's data-root step), § Answers, flags and settings.
- **Check:** `uv run pytest -q tests/setup tests/test_docs.py`.
- **Done:** the wizard offers `A data root on this machine?` (path, depth, default 2) and writes top-level
  `sources:`. Next to a data root's path, the scan shows `20 datasets at depth 2` locally, and for a host after its
  probe. Reconfiguring reads it back.
- **Risks:** a path with no cards → shown as `0 datasets` and still accepted (`test_empty_root`); depth changed in
  reconfigure is written (`test_depth_reconfigure`).

## G. Guide

### G91. `beamtime guide datasets` (sonnet) — code

- **Touches:** new `src/beamtime/guide/parts/datasets.md`, `src/beamtime/guide/__init__.py` (`TOPICS` 16), new
  `src/beamtime/guide/examples/dataset.yaml` (a dataset view), `src/beamtime/guide/skills.py`, generated skills
  (`scripts/build-plugin`), `tests/guide/`.
- **Read:** `src/beamtime/guide/parts/overview.md` (tone and length), `docs/design/11-datasets.md`.
- **Check:** `uv run pytest -q tests/guide`; `uv run python scripts/build-plugin`.
- **Done:** the topic explains reading cards, the four link states, `runs --uses` with its limits (same host, folder
  name in the path), the `datasets` query, and saving a dataset view, with the example validating; the overview
  topic links it in one line.

## Z. Close

### Z91. Close (sonnet) — code

- **Touches:** `CHANGELOG.md`, new `docs/guides/datasets.md`, `docs/nav.json`, `docs/guides/settings.md`,
  `CLAUDE.md` (Layout: `format/datacard.py`, `ops/datasets.py`), `docs/plans/v0.4/datasets/beamtime-dataset-request.md`
  (status line: implemented by this plan).
- **Check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`;
  `uv run python scripts/release.py`.
- **Done:** the changelog lists the additions and breaking changes; the user guide shows a data root, `dataset list`,
  `--uses` and a dataset view; the Goal's "Confirmed by" checks pass.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| Views in storage | no inheritance | a dataset without its own view shows its data root's `view/` | none; applies to data roots only |
| Top-level setting `sources:` | unknown key, ignored with a warning | this machine's data roots | none |
| `Selection` / block props | no `uses` | `uses` (and internal `uses_dir`, refused from clients) | none; additive |

## Not verified

- That `os.path.realpath` over hundreds of runs' config strings stays fast on Lustre once the prefilter has cut the
  candidates (Q91; time it in the Docker test with 1000 synth runs).
- That `compile_view` can tell a dataset page from a group page without a signature change (W91 Stop if).
- That the hosts plan landed with `Spec.kind` and the data-root refusal as its Brief says (K91 starts by reading
  `remote/sources.py`).
- How the request's real data root looks with depth 2 (`old/` stubs at depth 2; nothing deeper assumed): check
  with `beamtime dataset list` on gpu04 after O91.
