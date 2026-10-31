"""Times as Beamtime writes them: ISO 8601 in UTC, and compact stamps for ids and the trash."""

from datetime import datetime, timezone


def iso(t: float, *, ms: bool = False) -> str:
    """Format a unix time as ISO 8601 UTC.

    :param t: The time.
    :param ms: Whether to keep milliseconds, as run files do.
    :return: E.g. ``2026-10-24T10:15:32Z`` or ``2026-10-24T10:15:32.104Z``."""
    when = datetime.fromtimestamp(t, timezone.utc)
    if ms:
        return when.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text: str) -> float:
    """Read an ISO 8601 date or time; one without a zone is UTC.

    :param text: E.g. ``2026-10-01``, ``2026-10-01T12:00:00Z`` or with an offset.
    :return: Unix time.
    :raises ValueError: If the text is not a date."""
    # Python 3.10 reads no trailing Z.
    t = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    return (t if t.tzinfo else t.replace(tzinfo=timezone.utc)).timestamp()


def stamp(now: datetime | None = None) -> str:
    """Format a time compactly, as ids and trash folders start.

    :param now: The time; defaults to the current one.
    :return: E.g. ``20261024-101532``."""
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%d-%H%M%S")
