# Beamtime

Agents-first experiment logging, an alternative to W&B and TensorBoard. ML researchers and their coding
agents log runs (each with a proposal and a verdict) from local machines and HPC clusters, and
agents build custom views from Beamtime's building blocks.

- **Python**: 3.11 for the CLI and `serve`; 3.10+ for the SDK modules
- **Package manager**: `uv`
- **Linter/formatter**: `ruff` (configured in `pyproject.toml`)

# Philosophy

**Write lean scientific code with an object-oriented approach. Do not overengineer. Code must be
readable and simple.**

# Python style

### Imports

Group imports in this order, separated by blank lines:
1. Standard library (`from typing import ...`, `from abc import ...`, `logging`, `os`)
2. Third-party (`torch`, `numpy`, `sklearn`, …)
3. Internal (`from mypackage.utils...`, `from mypackage.models...`)

Import frequently used names explicitly rather than accessing them through the module:

```python
from typing import Any, Literal
import logging

import torch
from torch import Tensor, nn
```

### Type annotations

- Use Python 3.10+ union syntax: `str | None`, never `Optional[str]`
- Use lowercase built-in generics: `dict[str, Tensor]`, `list[int]`, `tuple[Tensor, ...]`, never
  `Dict`, `List`, `Tuple`
- Annotate every public function signature (parameters and return type)
- Use `Literal[...]` for string-valued enum parameters

### Docstrings

Every public class, method and function gets a docstring:

```python
def foo(self, x: Tensor, t: Tensor) -> tuple[Tensor, Tensor]:
    """Short one-line description.

    :param x: Description of x.
    :param t: Description of t.
    :return: Description of the return value."""
```

- One-line summary first, then a blank line, then `:param`/`:return:` lines
- The closing `"""` goes on the last text line
- Always end sentences with a period
- Class docstrings: one short line is enough

### Naming

- `snake_case` for variables, functions and modules
- Single uppercase letters for matrices: `M`, `R`, `Q`
- Short tensor names in local scope are fine: `B`, `N`, `d`, `b`, `n`

### Class structure

- Define config/hparams classes directly before the class that uses them
- `__init__` first, then core methods (`forward`, `training_step`, …), then helpers and properties
- Keyword-only constructors
- Use `@property` for computed read-only attributes
- Use `ABC` + `@abstractmethod` for base classes; abstract methods raise `NotImplementedError`
- Keep methods flat and self-contained rather than routing shared logic through a private
  dict-bundling helper that branches on its caller; when several call sites genuinely share a
  computation, factor it into its own plainly named method and call that from each

### Modern idioms

- Walrus operator for conditional assignments:
  ```python
  if (value := some_dict.get("key")) is not None:
      ...
  ```
- `match`/`case` for dispatching on string literals, always with a `case _: raise ValueError`
  default
- f-strings for all string formatting

### Comments

Write comments only when the *why* is non-obvious: a hidden constraint, a numerical workaround, or
a subtle invariant. One short line is enough, no multi-line blocks.

```python
# clamp before sampling — numerical solvers can return tiny negative values.
w = torch.clamp(w, min=0.0)
```

Never use comments to separate logical blocks of code, not even in `__init__`. Use a blank line
instead.

### Notebooks

No prose in notebooks unless explicitly asked for: no markdown cells and no docstrings, only code
cells. Short code comments under the rules above are fine; explanations go in the chat reply.

### PyTorch

- Prefer `torch.cat` / `torch.einsum` / `torch.stack` over manual loops
- Use `nn.Sequential` for MLPs, `nn.ModuleList` for variable-depth layer stacks
- Use `einops.rearrange` / `einops.repeat` for readable shape manipulation

# Testing

- Use `pytest` with fixtures in `conftest.py`
- Fixture and test-class docstrings follow the same `:param`/`:return:` format
- Test implementations of abstract classes are self-contained in the test file
- Run `ruff check . && ruff format --check . && pytest -q` before committing

# Tooling

- `ruff` is configured in `pyproject.toml` and excludes `tests/` and `.venv/`
- `uv` manages the environment (no conda): `uv sync`, `uv run <cmd>`, `uv add <pkg>`

### uv pitfalls

- `uv sync` failing with `The wheel is invalid: Missing .dist-info directory` or
  `does not appear to be a Python project` usually means a corrupt cache entry, not a real build
  failure. `uv cache clean <package>` fixes it; `uv sync --no-cache` is the fallback.
- `[tool.uv.sources]` redirects a package only where the project requires it *directly*; left
  transitive it re-resolves from PyPI. A wheel that must come from a custom index therefore has to
  be listed in `[project.dependencies]` even if only a dependency imports it. After any `uv lock`,
  grep `uv.lock` to confirm the pinned build.
- A path dependency's own `[tool.uv.sources]` loses to the parent's entry, so overriding a git
  branch from a nested project is silently ignored.

# Visualization

Use matplotlib with the scienceplots theme:

```python
import matplotlib.pyplot as plt
import scienceplots

plt.style.use(["science", "nature"])
```

The `science` style renders all text through LaTeX. On machines without LaTeX (e.g. cluster nodes)
append `no-latex`:

```python
plt.style.use(["science", "nature", "no-latex"])
```

- Use the rc params exactly as scienceplots sets them. Do not override them, neither through
  `rcParams`/`rc_context` nor through per-call keyword arguments that shadow an rc param
  (`fontsize`, `color` on text, `linewidth`, `cmap`, ...). Deviate only when the figure cannot work
  otherwise, and then as locally as possible.
- Plot densities as filled contours (`contourf`), not as `imshow`, `pcolormesh` or `hist2d` images.
- Figure sizes: 3.3 x 2.5 inches single-column, 6.9 x 2.5 inches double-column.
- Save as pdf with `bbox_inches="tight"`; use `dpi=400` when parts are rasterized.

# Data

- Large data, trajectories and checkpoints live outside the repo and are never committed. Expose
  their location through a configurable data root (an environment variable or CLI option) or a
  symlink.
- Large artifacts another project already holds are symlinked, not copied.

# Git

Work in the current checkout by default. A small change (a fix, a config tweak, a few lines in one
or two files, a doc edit) does not get a worktree. Only a larger change can justify one (a
multi-file refactor, a feature spanning several modules, work that could collide with uncommitted
changes). **Never create a worktree on your own:** when one might be the better choice, ask first
and say why.

# Project specifics

**Status: implementation.** M0 (foundations), M1 (SDK), M2 (index and queries), M3 (CLI and
MCP), M4 (research record), M5 (web UI shell), the UI refactor, M6 (views), M7 (custom blocks and
the library) and M8 (remotes; tested on Docker, a real cluster run pending) are done; milestones follow
`docs/implementation-plan.md`.
Each milestone implements the design sections it names; a deviation is decided and written back into
the design before the code lands.

### Decisions so far

Start with `docs/design/00-overview.md`: canonical names, the v1 scope, platform and dependencies,
cross-cutting rules and the testing strategy. The layer documents are the spec; keep code and docs in
sync.

- **Files are the source of truth; every file has one writer.** A run is a plain directory
  (`docs/design/01-storage.md`); the SQLite index is a cache. State that several parties change
  (notes, views, proposals, memory) is stored as new immutable files; the newest counts.
- **Beamtime records experiments, it never runs them.**
- **The root is the user's repo**, like TensorBoard; runs live in user-chosen folders under one log
  dir (default `beamtime/`) and are found by their `_run.json`. Folders are the only hierarchy.
- **Machine-written files start with `_`**; authored files live in `proposal/`, `notes/`, `view/`,
  `memory/` and `blocks/`. Every file carries `schema`; readers accept every version forever; there
  is no migration.
- **The SDK** (`docs/design/02-sdk.md`) needs Python 3.10+, the standard library and PyYAML, runs on
  Linux, macOS and Windows, never breaks or blocks training, records proposal membership in
  `_run.json`, and captures output through a bounded pipe. CLI and `serve` need Python 3.11+.
- **Runs record data, views present it.** The run card and `_preview.json` make run tables and
  overviews cheap without an index.
- **The research record** (`docs/design/09-research-record.md`): versioned proposals frozen once a run
  records them, optional plans, named predictions (`each`, `compare`) checked with t-intervals,
  immutable typed notes with per-prediction verdicts, a derived group status, and a versioned
  compressed memory.
- **The index** (`docs/design/03-index.md`): SQLite for metadata plus raw column files, one pure-Python
  read path with `math.fsum` everywhere, discovery by walking only the queried subtree, one
  `beamtime serve` per root. Keep NumPy and other heavy imports off the CLI path; the import time is
  checked in CI.
- **Remotes** (`docs/design/04-remotes.md`): the remote is the source of truth and data flows one way.
  The local `serve` queries `serve --stdio` over ssh; listings are federated, aggregates computed per
  source. Port forwarding with a token and read-only pulls are the other modes.
- **Settings have two levels, like VS Code**: `~/.config/beamtime/settings.yaml`, then the project's
  `beamtime.yaml`, then command-line flags.
- **Never put SQLite on cluster filesystems.** The index cache lives in `~/.cache/beamtime/`.
- **Views** (`docs/design/05-views.md`) are YAML trees built by agents from declarative widgets and
  custom code blocks (ES modules in sandboxed iframes on the `bt` kit with Preact/htm). All data comes
  through declared queries. Validation is static, plus one headless render where Chromium exists.
  Library blocks in `blocks/` are pinned by views. Themes are token files. Queries and widgets are
  msgspec structs.
- **Agent instructions come from `beamtime guide`**, which marks its defaults as defaults; users
  override them in their own instruction files.
- **The web UI** (`docs/design/07-web-ui.md`) is a fixed shell that must feel seamless, light and
  concise; every state has a URL; live updates are server-sent notifications plus refetch; browser,
  screenshots and exports share one renderer.
- **Charts render with uPlot** using Beamtime's theme (no Vega-Lite); written texts are edited in
  the UI as new versions. The matplotlib/scienceplots rules above
  apply to code that produces figures with matplotlib, not to the web UI.
- **CLI and MCP** (`docs/design/08-cli-mcp.md`) are frontends of one operation set; MCP tool names
  follow the CLI path (`beamtime note add` ↔ `note_add`). Agent writes are additive; agents never run
  user-only commands (setup, serving, settings, moving, deleting) and hand the user the command.
- **The self-hosted server is post-v1** (`docs/design/06-server.md`); v1 keeps only its hooks: no
  network code in the SDK, `author` and `user` on authored files, a sandbox built for untrusted views.

### Layout

- `src/beamtime/`: one subpackage per layer (`docs/implementation-plan.md#package-layout`); `cli/` is the
  `beamtime` entry point
- `src/beamtime/format/`: file names, ids, the write protocol and readers for every file kind
- `src/beamtime/synth/`: the seeded log-dir generator with planted effects; tests use it as fixture
  source (`synth` fixture in `tests/conftest.py`)
- `sdk/`, `format/` and `synth/` stay Python 3.10 with the standard library and PyYAML only
  (`tests/test_boundaries.py`)
- `src/beamtime/sdk/`: the SDK; tests that call `init` run scripts in subprocesses (`script` fixture in
  `tests/sdk/conftest.py`), so hooks and fd capture never touch pytest
- `src/beamtime/index/`: the cache (SQLite + column files), ingest, discovery, locks, the daemon loop
- `src/beamtime/query/`: the query language; `beamtime.query.run(query, logdir=...)` answers any kind
  (`kinds.py`); `select.py` resolves scopes and selects runs, `aggregate.py` groups and summarizes,
  `files.py` reads view data files; `read.py` is the one read path every number goes through
- `src/beamtime/record/`: the research record: proposal models and membership (`Target`), the check
  (`check.py`), t-intervals in pure Python (`stats.py`), plans, notes, group status and memory;
  tests in `tests/record/`, the done criterion in `test_end_to_end.py`
- `src/beamtime/ops/`: the operation set; `registry.py` lists every operation (CLI path, msgspec
  params, summary, user-only flag) and is the single source for CLI flags and MCP tools
- `src/beamtime/cli/` (argparse, condition strings, text format) and `src/beamtime/mcp/` (stdio
  server, prompts; needs the `serve` extra)
- `src/beamtime/settings.py`: built-in, user and project settings with provenance
- `src/beamtime/remote/`: remote sources: the ssh client (`client.py`), sources from settings and
  arguments (`sources.py`), routing by `@source/...` and merging (`route.py`), CLI/MCP calls through a
  running serve (`via_serve.py`), snapshots (`pull.py`); the remote end is `serve --stdio`
  (`serve/stdio.py`), sharing the API dispatch (`serve/api.py`); tests in `tests/remote/`
  (`test_docker.py` over real ssh, opt-in with `BEAMTIME_DOCKER=1`)
- `src/beamtime/serve/`: `beamtime serve` (Starlette on uvicorn): the API (`app.py`), the token and
  CSP (`auth.py`), live updates (`live.py`), the command (`server.py`) and the committed frontend
  bundle in `static/`; tests in `tests/serve/` (`test_browser.py` runs headless Chromium, skipped
  without it)
- `src/beamtime/views/`: themes (`theme.py`, built-in pair in `themes/`), the built-in default view
  as a view built from what a page logged (`defaults.py`), the view format as msgspec structs
  (`model.py`), compiling views to block trees (`compile.py`), folding viewer settings back
  (`prefs.py`), saved versions and drafts in `.beamtime/drafts/` (`store.py`), static validation (`validate.py`) and the headless renderer
  (`render.py`, an installed browser only), lexical checks of custom-block code (`code.py`) and library
  blocks (`library.py`: definitions, lookup from a group up to the root, params); tests in
  `tests/views/` and `tests/serve/test_render.py`
- `src/beamtime/ops/authored.py`: what every authored write shares (target, author, new version,
  answer); `src/beamtime/ops/views.py`: the `view` operations; `src/beamtime/ops/blocks.py`: the `block`
  operations (drafts in `.beamtime/drafts/blocks/`, export and import, also from git);
  `src/beamtime/guide/`: the agent guide (Markdown parts and five example views with
  `{{placeholders}}` filled from a group's keys; the custom example's code in `examples/code/`)
- `web/`: the frontend in TypeScript (Preact + htm, uPlot, lucide, marked + KaTeX): `src/shell/` the
  app, `src/bt/` the kit (charts, curves, preferences, writes), `src/blocks/` the built-in blocks
  (`custom.ts` hosts custom blocks), `src/kit/` the custom-block frame (`frame.ts`, its own entry
  `kit.js`; `window.bt`; the bridge protocol),
  `src/ui/` primitives (icons and symbols, tooltip, popovers, inline editing, Markdown),
  `src/styles/` the stylesheets. After any change in `web/`, run
  `cd web && npm ci && npm test && npm run build` and commit the rebuilt `src/beamtime/serve/static/`
  with it (CI fails when the bundle is stale; the shell must stay under 120 KB compressed)
- `bench/web/timing.py`: the UI's timing budgets on a scale-M log dir (first view, group to group)
- Keep the CLI path light: no module-level imports of PyYAML, NumPy or `importlib.metadata` in
  modules a plain `beamtime runs` loads (`tests/test_budgets.py`)
- Tests never touch `~/.cache`: `tests/conftest.py` points `BEAMTIME_CACHE` at a temporary directory
- `examples/`: toy training script and SLURM job for checking the SDK by hand
- `tests/golden/schema1/`: frozen, byte-exact reader fixtures; never regenerate or reformat them
- `.github/workflows/ci.yml`: lint, tests on 3.11–3.13 and macOS, SDK tests on 3.10 and Windows, budgets,
  the web build and the browser test
- Run checks with `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`
- SDK side on 3.10, without touching `.venv`:
  `UV_PROJECT_ENVIRONMENT=/tmp/bt-venv310 uv run --python 3.10 pytest -q tests/sdk tests/format tests/synth tests/test_boundaries.py tests/test_cli.py`
- Lightning tests, in a throwaway env (downloads PyTorch):
  `UV_PROJECT_ENVIRONMENT=/tmp/bt-venv-lightning uv run --with lightning --with torch pytest -q tests/sdk/test_lightning.py`
