"""Which flattened config keys actually distinguish runs: enough to group and label by, dropping
aliases of the same split and noise that happens to be unique to every run."""

import json
import re
from dataclasses import dataclass
from typing import Any

PATH_OR_DATE = re.compile(r"[/\\]|^\d{4}-\d{2}-\d{2}")
MISSING = "\0missing"


@dataclass(kw_only=True, frozen=True)
class Distinct:
    """The config keys that distinguish runs, and which keys are aliases of which."""

    varying: list[str]
    aliases: dict[str, str]


def distinguishing(per_run: list[dict[str, Any]]) -> Distinct:
    """Find the flattened config keys worth showing: real splits, not aliases or path noise.

    :param per_run: Each run's flattened config, dotted key to value.
    :return: ``varying`` keys (``config.``-prefixed) and each alias's canonical key."""
    n = len(per_run)
    keys = sorted({k for cfg in per_run for k in cfg})
    sig = {k: signature(per_run, k) for k in keys}
    candidates = [k for k in keys if len(set(sig[k])) > 1 and not noisy(per_run, k, sig[k], n)]

    groups: dict[tuple[int, ...], list[str]] = {}
    for k in candidates:
        groups.setdefault(sig[k], []).append(k)
    aliases: dict[str, str] = {}
    kept: list[str] = []
    for members in groups.values():
        canon, *rest = sorted(members, key=lambda k: (k.count("."), k))
        kept.append(canon)
        aliases.update(dict.fromkeys(rest, canon))

    # a sweep's seed is always the finest split; letting it "explain" another key would
    # collapse that key's curves into one, averaging arms that only differ in their seeds.
    seeds = {k for k in kept if is_seed(k)}
    reducers = {k: sig[k] for k in kept if k not in seeds and len(set(sig[k])) < n}
    dropped = {
        k
        for k in kept
        if k not in seeds and any(a != k and determines(s, sig[k]) for a, s in reducers.items())
    }
    varying = sorted(f"config.{k}" for k in kept if k not in dropped)
    return Distinct(
        varying=varying, aliases={f"config.{k}": f"config.{c}" for k, c in aliases.items()}
    )


def signature(per_run: list[dict[str, Any]], key: str) -> tuple[int, ...]:
    """Map each run to a small int, the same int for runs that share the key's value.

    :param per_run: Each run's flattened config.
    :param key: The key.
    :return: One class id per run, in order."""
    seen: dict[str, int] = {}
    return tuple(
        seen.setdefault(json.dumps(cfg.get(key, MISSING), sort_keys=True), len(seen))
        for cfg in per_run
    )


def noisy(per_run: list[dict[str, Any]], key: str, sig: tuple[int, ...], n: int) -> bool:
    """Whether a key is a path or a timestamp unique to every run, not a real sweep.

    :param per_run: Each run's flattened config.
    :param key: The candidate key.
    :param sig: The key's per-run classes.
    :param n: The number of runs.
    :return: Whether to drop it as noise."""
    if n <= 2 or len(set(sig)) != n:
        return False
    values = [cfg.get(key, MISSING) for cfg in per_run]
    if not all(isinstance(v, str) for v in values):
        return False
    return all(PATH_OR_DATE.search(v) for v in values)


def determines(a: tuple[int, ...], b: tuple[int, ...]) -> bool:
    """Whether runs sharing a value of one key always share a value of another.

    :param a: The first key's per-run classes.
    :param b: The second key's per-run classes.
    :return: Whether ``a``'s partition refines ``b``'s."""
    seen: dict[int, int] = {}
    return all(seen.setdefault(x, y) == y for x, y in zip(a, b, strict=True))


def is_seed(key: str) -> bool:
    """Whether a flattened key names a run's seed, by its last segment.

    :param key: The flattened key.
    :return: Whether it is named, or nested under, ``seed``."""
    leaf = re.sub(r'^\["|"\]$', "", key.rsplit(".", 1)[-1])
    return leaf.lower() == "seed"


def flatten(config: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested config into dotted keys (keys with dots are quoted).

    :param config: The config.
    :param prefix: The path so far.
    :return: Dotted key to leaf value."""
    out = {}
    for k, v in config.items():
        name = f'["{k}"]' if "." in k else (f".{k}" if prefix else k)
        path = f"{prefix}{name}"
        if isinstance(v, dict) and v:
            out |= flatten(v, path)
        else:
            out[path] = v
    return out
