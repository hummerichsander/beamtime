"""PyTorch Lightning integration: ``BeamtimeLogger``."""

import argparse
from pathlib import Path
from typing import Any

try:
    from lightning.pytorch.loggers.logger import Logger, rank_zero_experiment
    from lightning.pytorch.utilities import rank_zero_only
except ImportError:
    from pytorch_lightning.loggers.logger import Logger, rank_zero_experiment
    from pytorch_lightning.utilities import rank_zero_only

from beamtime.sdk.run import NullRun, Run, init


class BeamtimeLogger(Logger):
    """A Lightning logger that records the trainer's run with Beamtime."""

    def __init__(self, **kwargs: Any) -> None:
        """Start the run on every rank; other ranks get a ``NullRun``.

        :param kwargs: The arguments of ``beamtime.init``."""
        super().__init__()
        self.run: Run | NullRun = init(**kwargs)
        self.checkpoints: set[str] = set()

    @property
    @rank_zero_experiment
    def experiment(self) -> Run | NullRun:
        """The Beamtime run, for logging data that is not a scalar."""
        return self.run

    @property
    def name(self) -> str:
        """An empty name, so checkpoints land in ``<run>/checkpoints/``."""
        return ""

    @property
    def version(self) -> str:
        """The run id, or an empty string on other ranks."""
        return self.run.id or ""

    @property
    def save_dir(self) -> str | None:
        """The folder holding the run directory."""
        return str(self.run.dir.parent) if self.run.dir is not None else None

    @property
    def root_dir(self) -> str | None:
        """The folder holding the run directory."""
        return self.save_dir

    @property
    def log_dir(self) -> str | None:
        """The run directory."""
        return str(self.run.dir) if self.run.dir is not None else None

    @rank_zero_only
    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Log the trainer's metrics at its global step.

        :param metrics: Metric name to value.
        :param step: The global step."""
        self.run.log(metrics, step=step)

    @rank_zero_only
    def log_hyperparams(self, params: Any, *args: Any, **kwargs: Any) -> None:
        """Add hyperparameters to the run's config.

        :param params: A dict or ``argparse.Namespace``.
        :param args: Ignored.
        :param kwargs: Ignored."""
        if isinstance(params, argparse.Namespace):
            params = vars(params)
        self.run.config.update(dict(params or {}))

    def after_save_checkpoint(self, checkpoint_callback: Any) -> None:
        """Record new checkpoint files by reference, with the monitored score.

        :param checkpoint_callback: Lightning's ``ModelCheckpoint``."""
        paths = (
            getattr(checkpoint_callback, "best_model_path", ""),
            getattr(checkpoint_callback, "last_model_path", ""),
        )
        score = getattr(checkpoint_callback, "best_model_score", None)
        for path in paths:
            if path and path not in self.checkpoints and Path(path).exists():
                self.checkpoints.add(path)
                self.run.artifact(
                    path,
                    kind="checkpoint",
                    copy=False,
                    monitor=getattr(checkpoint_callback, "monitor", None),
                    score=float(score) if score is not None else None,
                )

    def finalize(self, status: str) -> None:
        """Lightning calls this after every fit, validate and test; the run goes on.

        :param status: ``success``, ``failed`` or ``finished``."""
        if isinstance(self.run, Run):
            if status == "failed":
                self.run.event("trainer failed", status=status)
            self.run.guard("finalize", self.run.flush)
