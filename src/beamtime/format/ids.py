"""Run ids and version ids: UTC time plus random base32 characters."""

import random
import re
from datetime import datetime, timezone

ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"

_TIME = r"\d{8}-\d{6}"
_RUN_ID = re.compile(rf"{_TIME}-[{ALPHABET}]{{8}}")
_VERSION_ID = re.compile(rf"{_TIME}-[{ALPHABET}]{{4}}")


def _new_id(n: int, *, now: datetime | None, rng: random.Random | None) -> str:
    """Make an id from a time and ``n`` random characters.

    :param n: Number of random characters.
    :param now: The time; defaults to the current UTC time.
    :param rng: The random source; defaults to the system's.
    :return: The id."""
    now = now or datetime.now(timezone.utc)
    rng = rng or random.SystemRandom()
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{''.join(rng.choice(ALPHABET) for _ in range(n))}"


def new_run_id(*, now: datetime | None = None, rng: random.Random | None = None) -> str:
    """Make a run id such as ``20261024-101532-k3m9xq2a``.

    :param now: The start time; defaults to the current UTC time.
    :param rng: The random source; defaults to the system's.
    :return: The run id."""
    return _new_id(8, now=now, rng=rng)


def new_version_id(
    *, now: datetime | None = None, rng: random.Random | None = None
) -> str:
    """Make a version id for an authored file, such as ``20261025-091200-x8k2``.

    :param now: The save time; defaults to the current UTC time.
    :param rng: The random source; defaults to the system's.
    :return: The version id."""
    return _new_id(4, now=now, rng=rng)


def is_run_id(text: str) -> bool:
    """Tell whether a string is a run id.

    :param text: The string.
    :return: Whether it is a run id."""
    return _RUN_ID.fullmatch(text) is not None


def is_version_id(text: str) -> bool:
    """Tell whether a string is a version id.

    :param text: The string.
    :return: Whether it is a version id."""
    return _VERSION_ID.fullmatch(text) is not None


def id_time(text: str) -> datetime:
    """Read the UTC time an id was made.

    :param text: A run or version id.
    :return: The time, timezone-aware."""
    return datetime.strptime(text[:15], "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
