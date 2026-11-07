from dataclasses import dataclass

from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.query.progress import progress
from beamtime.views import model as m
from beamtime.views.defaults import default_view

BENCH = "realistic/egnn-bench"


@dataclass
class Col:
    """A column with steps and values."""

    steps: list[int]
    values: list[float]


class Cols:
    """Columns by key, as ``progress`` reads them."""

    def __init__(self, **cols: Col) -> None:
        """Hold the columns.

        :param cols: Key to column."""
        self.cols = cols

    def get(self, key: str) -> Col | None:
        """Return a column.

        :param key: The key.
        :return: The column or ``None``."""
        return self.cols.get(key)


def lightning(steps: int, every: int = 50, per_epoch: int = 100) -> Cols:
    """Make columns of a run logging ``epoch`` every ``every`` steps.

    :param steps: The number of steps run.
    :param every: Steps between ``epoch`` points.
    :param per_epoch: Steps per epoch.
    :return: The columns, with ``_t`` at every 10 steps."""
    at = list(range(0, steps, every))
    return Cols(
        epoch=Col(at, [float(s // per_epoch) for s in at]),
        _t=Col(list(range(0, steps, 10)), [float(s) for s in range(0, steps, 10)]),
    )


def test_steps_per_epoch_come_from_change_points() -> None:
    """An epoch logged every 50 steps with 100 steps per epoch gives 100, not 50."""
    p = progress(lightning(250), {"trainer": {"max_epochs": 5}})
    assert p == {
        "epoch": 3,
        "in_epoch": 40,
        "steps_per_epoch": 100,
        "total": 5,
        "fraction": (2 + 0.4) / 5,
    }


def test_without_a_total_or_a_second_change_there_is_no_fraction_or_length() -> None:
    """The fraction needs ``max_epochs``; the epoch length needs two changes."""
    assert progress(lightning(250), {})["fraction"] is None
    p = progress(lightning(90), {"max_epochs": 4})
    assert p["steps_per_epoch"] is None and p["fraction"] == 0.0


def test_no_epoch_metric_gives_nothing() -> None:
    """A run without an ``epoch`` metric has no progress."""
    assert progress(Cols(_t=Col([0, 10], [0.0, 1.0])), {"max_epochs": 5}) is None


def test_epochs_logged_from_one_are_not_shifted() -> None:
    """Epochs that start at 1 count as logged, and the fraction stays at most 1."""
    cols = Cols(epoch=Col([0, 100, 200], [1.0, 2.0, 3.0]))
    p = progress(cols, {"max_epochs": 3})
    assert p["epoch"] == 3 and p["fraction"] == 2 / 3
    assert progress(cols, {"max_epochs": 2})["fraction"] == 1.0
    assert progress(cols, {"max_epochs": -1})["total"] is None


def test_card_progress_of_a_killed_and_a_finished_run(ctx: Context, roles: dict[str, str]) -> None:
    """The card reads the fraction from the epoch stair; a run without epochs has none."""
    killed = call("card", {"run": roles["realistic_killed"]}, ctx)["progress"]
    assert killed["epoch"] == 2 and killed["steps_per_epoch"] == 100 and killed["total"] == 5
    assert abs(killed["fraction"] - 1.9 / 5) < 1e-9
    done = call("card", {"run": roles["realistic_dirty"]}, ctx)
    assert done["progress"]["epoch"] == 5 and abs(done["progress"]["fraction"] - 0.98) < 1e-9
    assert done["run"]["steps_per_s"] > 0
    assert call("card", {"run": roles["diverging"]}, ctx)["progress"] is None


def test_run_epoch_and_progress_fields(ctx: Context) -> None:
    """``run.epoch`` and ``run.progress`` come from the card and the config; others get null."""
    select = ["run.epoch", "run.progress"]

    def pairs(group: str) -> set[tuple[float | None, float | None]]:
        answer = call("runs", {"from": group, "select": select, "limit": 20}, ctx)
        i = [answer["columns"].index(c) for c in select]
        return {(r[i[0]], r[i[1]] and round(r[i[1]], 3)) for r in answer["rows"]}

    assert pairs(BENCH) == {(2, 0.2), (5, 0.8)}
    assert pairs("realistic/lr-scan") == {(3, None)}
    assert pairs("scaling") == {(None, None)}


def test_default_view_draws_no_chart_of_a_clock(ctx: Context) -> None:
    """The epoch stair is no chart in the default view; the losses still are."""
    view = default_view(ctx, BENCH)
    charts = [b.y for b in walk(view.body) if isinstance(b, m.Line)]
    assert "epoch" not in charts and "validation/loss" in charts


def walk(blocks: list[m.Block]) -> list[m.Block]:
    """List blocks and their descendants.

    :param blocks: The blocks.
    :return: All of them."""
    out = []
    for b in blocks:
        out.append(b)
        out += walk(getattr(b, "children", None) or [])
    return out
