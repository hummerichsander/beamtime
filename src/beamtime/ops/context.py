"""What every operation runs against: root, settings, log dir and caller."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from beamtime.settings import Settings, load

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

    @classmethod
    def make(cls, *, root: str | Path | None = None, caller: Caller = "cli") -> "Context":
        """Resolve the project from ``--root`` or the working directory.

        :param root: An explicit root, or ``None`` to search like the SDK does.
        :param caller: ``cli``, ``mcp`` or ``view`` (the web UI); sets answer defaults.
        :return: The context."""
        from beamtime.sdk.paths import find_root

        if root is not None:
            resolved, reason = Path(root).expanduser().resolve(), "--root"
        else:
            resolved, warnings = find_root(Path.cwd())
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
