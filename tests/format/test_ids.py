import random
from datetime import datetime, timezone

from beamtime.format.ids import (
    ALPHABET,
    id_time,
    is_run_id,
    is_version_id,
    new_run_id,
    new_version_id,
)
from beamtime.format.names import random_name

T = datetime(2026, 10, 24, 10, 15, 32, tzinfo=timezone.utc)


def test_alphabet_is_crockford_lowercase() -> None:
    """The alphabet has 32 characters without i, l, o and u."""
    assert len(set(ALPHABET)) == 32
    assert not set("ilou") & set(ALPHABET)


def test_run_id_shape_and_time() -> None:
    """Run ids carry the UTC start time and 8 random characters."""
    rid = new_run_id(now=T, rng=random.Random(0))
    assert rid.startswith("20261024-101532-") and len(rid) == 24
    assert is_run_id(rid) and not is_version_id(rid)
    assert id_time(rid) == T


def test_version_id_shape() -> None:
    """Version ids carry 4 random characters."""
    vid = new_version_id(now=T)
    assert is_version_id(vid) and not is_run_id(vid)
    assert is_version_id("20261025-091200-x8k2")
    assert not is_version_id("20261025-091200-x8ki")


def test_ids_sort_chronologically() -> None:
    """Later ids sort after earlier ones."""
    a = new_run_id(now=T)
    b = new_run_id(now=T.replace(second=33))
    assert a < b


def test_ids_are_deterministic_with_a_seeded_rng() -> None:
    """Equal seeds give equal ids and names."""
    assert new_run_id(now=T, rng=random.Random(1)) == new_run_id(
        now=T, rng=random.Random(1)
    )
    assert random_name(random.Random(1)) == random_name(random.Random(1))
    assert random_name(random.Random(1)).count("-") == 2
