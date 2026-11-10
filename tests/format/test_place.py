import pytest

from beamtime.format.place import Place

RUN = "20261024-101532-k3m9xq2a"

CASES = [
    ("a/b", Place(None, "a/b")),
    (".", Place(None, ".")),
    ("", Place(None, ".")),
    ("a/", Place(None, "a")),
    ("a//b/./c/", Place(None, "a/b/c")),
    ("/abs/x", Place(None, "/abs/x")),
    ("@box", Place("box", ".")),
    ("@box/", Place("box", ".")),
    ("@box/a/b", Place("box", "a/b")),
    ("@box/a/", Place("box", "a")),
    ("@local", Place(None, ".")),
    ("@local/a", Place(None, "a")),
    ("a/../..", Place(None, "..")),
    ("@box/../x", Place("box", "../x")),
    ("@", Place("", ".")),
    (f"@box/g/{RUN}", Place("box", f"g/{RUN}")),
]


@pytest.mark.parametrize(("text", "place"), CASES)
def test_parse(text: str, place: Place) -> None:
    """Every case parses to its place, and the place's text parses back to it.

    :param text: The written place.
    :param place: The expected value."""
    assert Place.parse(text) == place
    assert Place.parse(place.text) == place


@pytest.mark.parametrize(
    ("place", "text"),
    [
        (Place(None, "a"), "a"),
        (Place(None, "."), "."),
        (Place("box", "."), "@box"),
        (Place("box", "a/b"), "@box/a/b"),
    ],
)
def test_text(place: Place, text: str) -> None:
    """The wire text leaves out the root path and writes no prefix for this machine.

    :param place: The place.
    :param text: Its wire text."""
    assert place.text == text


def test_bare_source() -> None:
    """A bare source and one with a trailing slash are the same root."""
    assert Place.parse("@box") == Place.parse("@box/") == Place("box", ".")
    assert Place.parse("@box").text == "@box"


def test_local_is_here() -> None:
    """``@local`` is this machine, with or without a path."""
    assert Place.parse("@local") == Place(None, ".")
    assert Place.parse("@local/a") == Place(None, "a")


def test_parse_keeps_escape() -> None:
    """A path that leaves the root keeps its leading dots for the resolver to refuse."""
    assert Place.parse("a/../..").path == ".."
    assert Place.parse("../x").path == "../x"


def test_run_id() -> None:
    """The last segment is the run id when it is one."""
    assert Place.parse(f"@box/g/{RUN}").run_id == RUN
    assert Place.parse("g/name").run_id is None
    assert Place.parse(".").run_id is None


def test_reserved() -> None:
    """A place is reserved when any segment is."""
    assert Place.parse("g/_private").reserved
    assert Place.parse("@box/g/notes/x").reserved
    assert Place.parse("g/.hidden").reserved
    assert not Place.parse("g/h").reserved
    assert not Place.parse(".").reserved
    assert not Place.parse("@box").reserved


def test_on() -> None:
    """``on`` keeps the path and swaps the source."""
    place = Place.parse("@a/g/h")
    assert place.on("b") == Place("b", "g/h")
    assert place.on(None).text == "g/h"
    assert Place.parse("g").on("a").text == "@a/g"


def test_frozen() -> None:
    """A place is a value."""
    with pytest.raises(AttributeError):
        Place(None, "a").path = "b"  # type: ignore[misc]
