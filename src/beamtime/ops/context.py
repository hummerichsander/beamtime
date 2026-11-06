"""What every operation runs against: root, settings, log dir and caller."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from beamtime.settings import Settings, load

if TYPE_CHECKING:
    from beamtime.remote.sources import Sources

Caller = Literal["cli", "mcp", "view"]


class OpError(Exception):
    """An operation that can't be done; the message says what to do instead."""

    def __init__(self, message: str, *, code: int = 1) -> None:
        """Create the error.

        :param message: What went wrong and what to do.
        :param code: The exit code: 1 error, 2 wrong usage, 3 invalid, 4 not found."""
        super().__init__(message)
        self.code = code


@dataclass(kw_only=True)
class Context:
    """The project an operation works on."""

    root: Path
    root_reason: str
    settings: Settings
    logdir: Path
    caller: Caller = "cli"
    # listings of "." merge every source; the web UI's pages of this machine ask for it only here.
    merge: bool = True
    # the remotes a running serve holds connections to; a one-shot call has none.
    sources: "Sources | None" = None
    # the time run status is judged at: now, or a snapshot's time.
    now: float | None = None

    @property
    def has_local(self) -> bool:
        """Tell whether this machine is a source: the log dir exists, and either no remotes
        are configured or it already holds a run.

        Checked fresh every time (never cached), since a first local run can appear while a
        ``serve`` with remotes is already running.

        :return: Whether local runs are a source here."""
        if not self.logdir.is_dir():
            return False
        if not self.settings.get("remotes"):
            return True
        from beamtime.format.tree import iter_runs

        return next(iter_runs(self.logdir), None) is not None

    @property
    def default_source(self) -> str | None:
        """The source an unprefixed path means, when this machine isn't one.

        :return: The sole remote's name, if there is no local source and exactly one remote
            is configured; else ``None`` (local means it, or it would be ambiguous)."""
        if self.has_local:
            return None
        remotes = self.settings.get("remotes") or {}
        return next(iter(remotes)) if len(remotes) == 1 else None

    @classmethod
    def make(cls, *, root: str | Path | None = None, caller: Caller = "cli") -> "Context":
        """Resolve the project from ``--root`` or the working directory.

        :param root: An explicit root, or ``None`` to search from the working directory.
        :param caller: ``cli``, ``mcp`` or ``view`` (the web UI); sets answer defaults.
        :return: The context."""
        from beamtime.sdk.paths import find_root

        if root is not None:
            resolved, reason = Path(root).expanduser().resolve(), "--root"
        else:
            # never the script fallback: here __main__ is beamtime's own entry point (or a test
            # runner's), not a user's training script, so it says nothing about their project.
            resolved, warnings = find_root(Path.cwd(), script=False)
            reason = (
                "working directory (no beamtime.yaml or git repository)"
                if warnings
                else (
                    "beamtime.yaml" if (resolved / "beamtime.yaml").is_file() else "git repository"
                )
            )
        settings = load(resolved)
        if env := os.environ.get("BEAMTIME_LOGDIR"):
            logdir = Path(env).expanduser().resolve()
        else:
            logdir = (resolved / Path(settings.get("logdir")).expanduser()).resolve()
        return cls(
            root=resolved,
            root_reason=reason,
            settings=settings,
            logdir=logdir,
            caller=caller,
        )
