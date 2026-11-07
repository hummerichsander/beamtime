"""Progress through epochs: an epoch metric is a clock, so a run reads its fraction from it."""

import math
from typing import Any

TOTAL_KEY = "max_epochs"


def progress(cols: Any, config: dict[str, Any]) -> dict[str, Any] | None:
    """Read a run's epoch, how far it is into it and how much of the planned epochs are done.

    The epoch numbers count from 1 when the first logged value is 0 (Lightning), else as logged.
    The epoch length is the step distance between the last two changes, so an ``epoch`` logged
    every 50 steps with 100 steps per epoch gives 100.

    :param cols: The run's columns.
    :param config: The run's config.
    :return: ``epoch``, ``in_epoch`` and ``steps_per_epoch`` (``None`` before a second change),
        ``total`` (from a config key ``max_epochs``, else ``None``) and ``fraction`` (``None``
        without a total); ``None`` without an ``epoch`` metric."""
    if (col := cols.get("epoch")) is None or not len(col.steps):
        return None

    steps, values = col.steps, col.values
    changes = [steps[0]] + [steps[i] for i in range(1, len(steps)) if values[i] != values[i - 1]]
    if not math.isfinite(last := values[len(values) - 1]):
        return None
    epoch = int(last) + (1 if values[0] == 0 else 0)
    steps_per_epoch = changes[-1] - changes[-2] if len(changes) > 1 else None
    current = cols.get("_t")
    now = max(steps[-1], current.steps[-1] if current is not None and len(current.steps) else 0)
    in_epoch = now - changes[-1] if steps_per_epoch else None

    total = find_total(config)
    fraction = None
    if total is not None:
        done = epoch - 1 + (min(in_epoch / steps_per_epoch, 1.0) if in_epoch is not None else 0.0)
        fraction = min(max(done / total, 0.0), 1.0)
    return {
        "epoch": epoch,
        "in_epoch": in_epoch,
        "steps_per_epoch": steps_per_epoch,
        "total": total,
        "fraction": fraction,
    }


def find_total(config: dict[str, Any]) -> int | None:
    """Find the planned number of epochs: the first positive ``max_epochs`` at any depth.

    :param config: The nested config.
    :return: The number, or ``None`` (Lightning's -1 means no limit)."""
    for key, value in config.items():
        if key == TOTAL_KEY and isinstance(value, int | float) and not isinstance(value, bool):
            if value > 0:
                return int(value)
        elif isinstance(value, dict) and (found := find_total(value)) is not None:
            return found
    return None
