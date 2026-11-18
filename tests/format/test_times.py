import pytest

from beamtime.format.times import age_text


@pytest.mark.parametrize(
    ("seconds", "text"),
    [
        (0, "0 s"),
        (89, "89 s"),
        (90, "2 min"),
        (420, "7 min"),
        (90 * 60 - 1, "90 min"),
        (90 * 60, "2 h"),
        (3 * 3600, "3 h"),
        (36 * 3600 - 1, "36 h"),
        (36 * 3600, "2 d"),
        (5 * 86400, "5 d"),
    ],
)
def test_age_text(seconds: float, text: str) -> None:
    """The unit changes at 90 seconds, 90 minutes and 36 hours."""
    assert age_text(seconds) == text
