"""Finding the root, the log dir and runs below it."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from beamtime.format.ids import is_run_id
from beamtime.format.tree import is_reserved, iter_runs

SETTINGS = "beamtime.yaml"
DEFAULT_LOGDIR = "beamtime"


@dataclass(kw_only=True, frozen=True)
class Location:
    """Where a new run goes: the log dir and a folder below it."""

    logdir: Path
    folder: Path
    warnings: list[str] = field(default_factory=list)

    @property
    def relative(self) -> str:
        """The folder relative to the log dir, ``.`` for the log dir itself."""
        return self.folder.relative_to(self.logdir).as_posix()


def find_up(start: Path, name: str) -> Path | None:
    """Find the nearest directory at or above ``start`` that contains ``name``.

    :param start: The directory to start from.
    :param name: A file or directory name, e.g. ``beamtime.yaml`` or ``.git``.
    :return: That directory, or ``None``."""
    for d in (start, *start.parents):
        if (d / name).exists():
            return d
    return None


def script_dir() -> Path | None:
    """Find the directory of the running script, if there is one.

    :return: The directory of ``__main__.__file__``, or ``None`` in a REPL."""
    main = sys.modules.get("__main__")
    if (file := getattr(main, "__file__", None)) is None:
        return None
    return Path(file).resolve().parent


def logdir_of(root: Path) -> Path:
    """Read the log dir of a root from its ``beamtime.yaml``.

    :param root: The root.
    :return: The absolute log dir; ``beamtime/`` unless the settings name another."""
    name = DEFAULT_LOGDIR
    if (settings := root / SETTINGS).is_file():
        import yaml

        data = yaml.safe_load(settings.read_text()) or {}
        name = data.get("logdir") or DEFAULT_LOGDIR
    return (root / Path(name).expanduser()).resolve()


def find_root(cwd: Path, *, script: bool = True) -> tuple[Path, list[str]]:
    """Find the root: ``beamtime.yaml`` above the working directory or the script, then
    the git root, then the working directory itself.

    :param cwd: The working directory.
    :param script: Whether to also look above the running script's own directory, for a training
        script launched from elsewhere. The CLI and ops layer turn this off, since their own
        ``__main__`` is Beamtime's (or a test runner's), never the user's project.
    :return: The root and any warnings."""
    starts = (cwd, script_dir()) if script else (cwd,)
    for start in starts:
        if start is not None and (root := find_up(start, SETTINGS)) is not None:
            return root, []
    for start in starts:
        if start is not None and (root := find_up(start, ".git")) is not None:
            return root, []
    return cwd, [
        f"no beamtime.yaml or git repository found; using the working directory {cwd} as the root"
    ]


def check_folder(folder: str) -> Path:
    """Check a folder given relative to the log dir.

    :param folder: E.g. ``scaling/lr-sweep``.
    :return: The folder as a relative path."""
    rel = Path(folder)
    for part in rel.parts:
        if part == ".." or is_reserved(part) or is_run_id(part):
            raise ValueError(
                f"dir {folder!r}: {part!r} is not allowed below the log dir "
                "(no '..', no reserved names such as 'notes' or '_trash', no run ids)"
            )
    return rel


def locate(dir: str | Path | None = None) -> Location:
    """Resolve where a new run goes.

    The order follows the storage layer: an absolute ``dir``, ``BEAMTIME_LOGDIR``, then
    the root found by ``find_root`` with its configured log dir.

    :param dir: The folder below the log dir, or an absolute path.
    :return: The log dir and the folder."""
    cwd = Path.cwd()
    if dir is not None and Path(dir).expanduser().is_absolute():
        target = Path(dir).expanduser().resolve()
        root, _ = find_root(target)
        logdir = logdir_of(root)
        if target != logdir and logdir not in target.parents:
            logdir = target
        check_folder(target.relative_to(logdir).as_posix())
        return Location(logdir=logdir, folder=target)
    rel = check_folder(str(dir or "."))
    if env := os.environ.get("BEAMTIME_LOGDIR"):
        logdir = Path(env).expanduser().resolve()
        return Location(logdir=logdir, folder=logdir / rel)
    root, warnings = find_root(cwd)
    logdir = logdir_of(root)
    return Location(logdir=logdir, folder=logdir / rel, warnings=warnings)


def find_run(logdir: Path, run_id: str) -> Path | None:
    """Find a run by id anywhere below the log dir.

    :param logdir: The log dir.
    :param run_id: The run id.
    :return: The run directory, or ``None``."""
    return next((p for p in iter_runs(logdir) if p.name == run_id), None)
