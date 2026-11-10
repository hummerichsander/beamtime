"""A place: a path on one source, as written in queries, links and the CLI."""

import posixpath
from dataclasses import dataclass

from beamtime.format.ids import is_run_id
from beamtime.format.tree import is_reserved


@dataclass(frozen=True)
class Place:
    """A path on a source; ``source`` is ``None`` for this machine."""

    source: str | None
    path: str

    @classmethod
    def parse(cls, text: str) -> "Place":
        """Read ``path``, ``@source`` or ``@source/path``; it never raises.

        :param text: The place as written; ``@local`` is this machine.
        :return: The normalized place."""
        source = None
        path = text
        if text.startswith("@"):
            name, _, path = text[1:].partition("/")
            source = None if name == "local" else name
        path = posixpath.normpath(path.rstrip("/")) if path.rstrip("/") else "."
        return cls(source, path)

    @property
    def text(self) -> str:
        """The place as written on the wire; ``Place.parse(p.text) == p``."""
        if self.source is None:
            return self.path
        if self.path == ".":
            return f"@{self.source}"
        return f"@{self.source}/{self.path}"

    @property
    def run_id(self) -> str | None:
        """The run id when the last segment is one, else ``None``."""
        last = self.path.rsplit("/", 1)[-1]
        return last if is_run_id(last) else None

    @property
    def reserved(self) -> bool:
        """Whether any segment of the path is a reserved name."""
        return self.path != "." and any(is_reserved(part) for part in self.path.split("/"))

    def on(self, source: str | None) -> "Place":
        """Put the same path on another source.

        :param source: The source name, or ``None`` for this machine.
        :return: The moved place."""
        return Place(source, self.path)
