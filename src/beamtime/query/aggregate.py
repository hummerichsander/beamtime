"""Grouping selected runs and summarizing values over a group: seeds, ``by`` fields, sorting."""

import json
import math
from typing import Any

from beamtime.query.distinguish import distinguishing, flatten, is_seed
from beamtime.query.fields import parse_field
from beamtime.query.models import QueryError
from beamtime.record.stats import mean, variance


def seed_groups(
    runs: list[dict[str, Any]], seeds: str
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    """Group runs that agree on every field that distinguishes them, apart from the seed.

    Unlike the full remaining config, this ignores aliases and incidental noise (a timestamped
    path varies on its own and would otherwise put every run in its own group).

    :param runs: Selected runs with ``_config``.
    :param seeds: The seed field, e.g. ``config.seed``.
    :return: ``(distinguishing config apart from the seed, runs)`` per group."""
    seed = parse_field(seeds)
    if seed.ns != "config" or len(seed.path) != 1:
        raise QueryError(f"seeds: {seeds!r} must be a top-level config field like config.seed")
    per_run = [flatten(json.loads(r["_config"] or "{}")) for r in runs]
    distinct = distinguishing(per_run)
    canon = distinct.aliases.get(seeds, seeds)
    # with one run per arm the seed splits the runs exactly as the arm does; the arm stays then.
    seed_like = canon == seeds or is_seed(canon.removeprefix("config."))
    by = [k.removeprefix("config.") for k in distinct.varying if not (seed_like and k == canon)]
    groups: dict[str, tuple[dict[str, Any], list]] = {}
    for r, cfg in zip(runs, per_run, strict=True):
        label = {k: cfg.get(k) for k in by}
        key = json.dumps(label, sort_keys=True)
        groups.setdefault(key, (label, []))[1].append(r)
    return list(groups.values())


def group_by(
    runs: list[dict[str, Any]], fields: list[str]
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    """Group runs by the values of fields.

    :param runs: The selected runs with the fields' values.
    :param fields: The grouping fields.
    :return: ``(field values, runs)`` per group."""
    groups: dict[str, tuple[dict[str, Any], list]] = {}
    for r in runs:
        label = {f: r.get(f) for f in fields}
        groups.setdefault(json.dumps(label, sort_keys=True), (label, []))[1].append(r)
    return list(groups.values())


def aggregate(values: list[Any]) -> Any:
    """Summarize a column over the seeds of a group.

    :param values: The values of the group's runs.
    :return: The common value, ``{mean, std, n}`` for differing numbers, or ``None``."""
    distinct = {json.dumps(v, sort_keys=True) for v in values}
    if len(distinct) == 1:
        return values[0]
    nums = [
        v
        for v in values
        if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    ]
    if nums and len(nums) == len([v for v in values if v is not None]):
        mu, std = spread(nums)
        return {"mean": mu, "std": std, "n": len(nums)}
    return None


def sort_rows(rows: list[dict[str, Any]], sort: list[str]) -> None:
    """Sort rows in place by several fields; missing values go last either way.

    :param rows: The rows, field name to value.
    :param sort: Fields, a leading ``-`` for descending."""

    def key(v: Any) -> Any:
        if isinstance(v, dict) and "mean" in v:
            v = v["mean"]
        return (0, v) if isinstance(v, (int, float)) and not isinstance(v, bool) else (1, str(v))

    for spec in reversed(sort):
        desc = spec.startswith("-")
        name = spec.lstrip("-")
        present = [r for r in rows if r.get(name) is not None]
        missing = [r for r in rows if r.get(name) is None]
        present.sort(key=lambda r: key(r[name]), reverse=desc)
        rows[:] = present + missing


def spread(values: list[float]) -> tuple[float, float]:
    """Give the mean and the sample standard deviation.

    :param values: The values, at least one.
    :return: ``(mean, std)``; the std of one value is 0."""
    return mean(values), math.sqrt(variance(values)) if len(values) > 1 else 0.0
