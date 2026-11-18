import json

from beamtime.format import constants as c
from beamtime.format.io import write_replaced
from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.query.aggregate import seed_groups
from beamtime.query.distinguish import distinguishing, flatten, is_seed, seed_key
from tests.query.test_code import make_run


def test_grid_of_lr_and_depth_keeps_both() -> None:
    """Two crossed sweeps both distinguish runs; neither explains the other."""
    per_run = [
        {"lr": lr, "depth": depth} for lr in (1e-3, 1e-2) for depth in (2, 4)
    ]
    assert distinguishing(per_run).varying == ["config.depth", "config.lr"]


def test_random_search_with_unique_lr_keeps_all() -> None:
    """A fully unique numeric field isn't noise: it stays, unlike a unique path or timestamp."""
    per_run = [{"lr": lr} for lr in (1e-4, 3e-4, 7e-4, 2e-3, 5e-3)]
    assert distinguishing(per_run).varying == ["config.lr"]


def test_twelve_values_count_as_varying() -> None:
    """A sweep above the display's 10-value cutoff still distinguishes runs."""
    per_run = [{"lr": lr} for lr in range(12)]
    assert distinguishing(per_run).varying == ["config.lr"]


def test_timestamped_path_unique_to_every_run_is_dropped() -> None:
    """A path-like field that happens to differ on every run is noise, not a sweep."""
    per_run = [
        {"arm": arm, "run_dir": f"/scratch/{arm}/2026-10-2{i}_12-00-00"}
        for i, arm in enumerate(["a", "b", "c", "a", "b", "c"])
    ]
    assert distinguishing(per_run).varying == ["config.arm"]


def test_seed_never_acts_as_a_reducer() -> None:
    """Even when the seed refines the arm, the seed never explains the arm away."""
    per_run = [
        {"arm": "A", "seed": 0},
        {"arm": "A", "seed": 0},
        {"arm": "A", "seed": 1},
        {"arm": "B", "seed": 2},
        {"arm": "B", "seed": 3},
    ]
    assert distinguishing(per_run).varying == ["config.arm", "config.seed"]


def test_exact_aliases_are_folded_and_the_shortest_kept() -> None:
    """Two keys inducing the same split are one alias group; the fewest-dots name wins."""
    per_run = [{"a": i % 2, "x.y.a": i % 2} for i in range(4)]
    distinct = distinguishing(per_run)
    assert distinct.varying == ["config.a"]
    assert distinct.aliases == {"config.x.y.a": "config.a"}


def test_realistic_group_gives_arm_and_seed(ctx: Context) -> None:
    """The egnn-bench group's varying config is exactly the arm and the seed, nothing nested."""
    keys = call("keys", {"from": "realistic/egnn-bench"}, ctx)
    assert keys["config"]["varying"] == ["config.arm", "config.seed"]
    assert keys["config"]["aliases"]["config.hydrantic.seed"] == "config.seed"


def test_seed_means_over_realistic_give_one_curve_per_arm(ctx: Context) -> None:
    """Averaging by config.seed now groups by the arm, not by the timestamped run dir."""
    answer = call(
        "series",
        {"from": "realistic/egnn-bench", "y": ["training/loss"], "seeds": "config.seed"},
        ctx,
    )
    curves = answer["curves"]
    assert len(curves) == 3
    assert {c["by"]["arm"] for c in curves} == {"small", "medium", "large"}


def test_seed_means_keep_arms_apart_with_one_run_per_arm() -> None:
    """With one seed per arm the seed aliases the arm; merging seeds must not merge the arms."""
    runs = [{"_config": f'{{"arm": "{arm}", "seed": {i}}}'} for i, arm in enumerate("abc")]
    groups = seed_groups(runs, "config.seed")
    assert sorted(label["arm"] for label, _ in groups) == ["a", "b", "c"]


def test_seed_leaves() -> None:
    """``seed``, ``random_seed`` and ``rng_seed`` name a seed; ``data_seed`` does not."""
    assert all(is_seed(k) for k in ("seed", "trainer.seed", "random_seed", "model.rng_seed"))
    assert not any(is_seed(k) for k in ("data_seed", "seeds", "lr"))


def test_seed_key_is_the_one_varying_seed() -> None:
    """A nested seed is found; two seed-like keys, or none, give no key."""
    assert seed_key(["config.arm", "config.trainer.seed"]) == "config.trainer.seed"
    assert seed_key(["config.random_seed"]) == "config.random_seed"
    assert seed_key(["config.seed", "config.rng_seed"]) is None
    assert seed_key(["config.arm"]) is None


def test_data_seed_is_no_seed() -> None:
    """A varying ``data_seed`` stays a hyperparameter, so no key is found."""
    per_run = [{"data_seed": i, "arm": "a"} for i in range(4)]
    assert seed_key(distinguishing(per_run).varying) is None


def test_constant_seed() -> None:
    """A seed that never varies is not a seed key: nothing merges."""
    per_run = [{"arm": a, "seed": 0} for a in "ab"]
    assert seed_key(distinguishing(per_run).varying) is None


def test_nested_seed_field() -> None:
    """``seeds`` takes any config field, including a nested or a quoted one."""
    arms = [(arm, i) for arm in "ab" for i in range(3)]
    nested = [{"_config": json.dumps({"arm": a, "trainer": {"seed": i}})} for a, i in arms]
    groups = seed_groups(nested, "config.trainer.seed")
    assert sorted(label["arm"] for label, _ in groups) == ["a", "b"]
    assert [len(rs) for _, rs in groups] == [3, 3]
    quoted = [{"_config": json.dumps({"arm": a, "a.b": {"seed": i}})} for a, i in arms]
    assert len(seed_groups(quoted, 'config["a.b"].seed')) == 2
    assert list(flatten({"a.b": {"seed": 1}})) == ['["a.b"].seed']


def test_keys_names_the_seed_and_a_nested_seed_aggregates(ctx: Context) -> None:
    """``keys`` reports ``config.seed``; an aggregate over it merges the seeds of each arm."""
    for arm in "ab":
        for i in range(3):
            run_dir = make_run(ctx.logdir, "nested", git={}, proposals={})
            write_replaced(
                run_dir / c.CONFIG, {"schema": 1, "arm": arm, "trainer": {"seed": i}}
            )
    keys = call("keys", {"from": "nested"}, ctx)
    assert keys["config"]["seed"] == "config.trainer.seed"
    answer = call("series", {"from": "nested", "y": ["x"], "seeds": "config.trainer.seed"}, ctx)
    assert {curve["by"]["arm"] for curve in answer["curves"]} == {"a", "b"}
