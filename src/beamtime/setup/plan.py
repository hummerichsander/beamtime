"""What ``beamtime init`` is going to change, as a list of changes."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, kw_only=True)
class Change:
    """One thing the setup writes: where it lands, how it reads in the review, and how to do it."""

    where: Literal["project", "machine", "remote", "import"]
    label: str
    before: str | None
    after: str
    run: Callable[[], str | None]
