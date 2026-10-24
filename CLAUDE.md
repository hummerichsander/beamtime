# Beamtime

Agents-first experiment logging, an alternative to W&B and TensorBoard. ML researchers and their coding
agents log runs (each with a hypothesis and a result) from local machines and HPC clusters, and
agents build custom report pages from Beamtime's widget library.

- **Python**: 3.11
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

**Status: design phase.** The architecture below is agreed on, but is being designed layer by layer
before implementation. Do not implement a layer whose design is not settled.

### Decisions so far

- **Design docs live in `docs/design/`**, one file per layer. They are the spec; keep code and docs
  in sync.
- **Files are the source of truth.** A run is a plain directory (see `docs/design/01-storage.md`).
  The SQLite index is a derived cache that can be rebuilt from the files at any time.
- **Every file has exactly one writer.** State that several parties change (results, notes) is
  stored as new immutable files, latest wins. Sync is a union of files.
- **Beamtime records experiments, it never runs them.** No job launching, sweep scheduling or
  hyperparameter search.
- **The root is the user's repo**, like TensorBoard. Runs live in user-chosen folders under log
  dirs (default `beamtime/`) and are found by their `run.json`. Folders are the only hierarchy:
  directions and sweeps are just groups of runs.
- **`output.log` is always captured**; there is no off switch.
- **Every run has a hypothesis**, possibly blank, with optional machine-checkable predictions. It
  freezes once the first metric is logged; results and notes can be added at any time.
- **Local and HPC are equally supported.** Runs write files only; compute nodes need no network.
  `beamtime serve` pulls configured remotes via rsync over ssh from the login node and merges them
  with local runs. SLURM metadata (job id, array index, node) is captured from the environment, and
  a heartbeat file lets runs that died silently show up as `lost`.
- **Never put SQLite on cluster filesystems** (Lustre/GPFS). The index cache lives in
  `~/.cache/beamtime/`, never in the repo or a log dir.
- **Report pages are YAML widget trees**, not markdown. Prose is limited to short `note`, `callout`
  and `caption` fields. Widgets reference data through queries (runs, sweeps, `derived/` tables)
  rather than embedding values. Widgets are Pydantic models, which give schema, validation and the
  JSON schema served to agents.
- **Charts render with Vega-Lite** in the browser, using Beamtime's theme. The matplotlib/scienceplots
  rules above apply to static figure export, not to the web UI.
- **Frontends share one core library:** Python SDK, CLI, MCP server, web UI. MCP outputs must be
  token-efficient (summaries, downsampled curves, diffs).

### Layout

- `src/beamtime/`: package (`cli.py` is the `beamtime` entry point)
- `tests/`: pytest suite
- Run checks with `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`
