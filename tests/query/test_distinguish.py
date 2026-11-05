from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.query.distinguish import distinguishing


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
