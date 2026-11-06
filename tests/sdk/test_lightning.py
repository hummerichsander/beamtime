from pathlib import Path

import pytest

from beamtime.format.run import (
    read_artifacts,
    read_config,
    read_effective_metrics,
    read_events,
    read_run_info,
)
from tests.sdk.conftest import Script, only_run

pytest.importorskip("torch")
pytest.importorskip("lightning")


def test_trainer_fit_and_test(script: Script, logdir: Path) -> None:
    """A Lightning fit and test record metrics, hyperparameters and checkpoints."""
    proc = script(
        """
        import torch, lightning as L
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset
        from beamtime.lightning import BeamtimeLogger

        class Model(L.LightningModule):
            def __init__(self, lr=0.1):
                super().__init__()
                self.save_hyperparameters()
                self.net = nn.Linear(4, 1)
            def training_step(self, batch, _):
                x, y = batch
                loss = nn.functional.mse_loss(self.net(x), y)
                self.log("train/loss", loss)
                return loss
            def validation_step(self, batch, _):
                x, y = batch
                self.log("val/loss", nn.functional.mse_loss(self.net(x), y))
            def test_step(self, batch, _):
                x, y = batch
                self.log("test/loss", nn.functional.mse_loss(self.net(x), y))
            def configure_optimizers(self):
                return torch.optim.SGD(self.parameters(), lr=self.hparams.lr)

        data = TensorDataset(torch.randn(64, 4), torch.randn(64, 1))
        loader = DataLoader(data, batch_size=8)
        logger = BeamtimeLogger(dir="lightning", proposal="Linear fits noise badly.")
        trainer = L.Trainer(max_epochs=3, logger=logger, log_every_n_steps=2,
                            enable_progress_bar=False, enable_model_summary=False,
                            accelerator="cpu")
        trainer.fit(Model(), loader, loader)
        trainer.test(ckpt_path="best", dataloaders=loader)
        print("checkpoints in", trainer.checkpoint_callback.dirpath)
        """,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr.decode()[-3000:]
    run = only_run(logdir / "lightning")
    assert read_run_info(run).status == "finished"
    assert read_config(run) == {"lr": 0.1}
    keys = {k for r in read_effective_metrics(run) for k in r}
    assert {"train/loss", "val/loss", "test/loss", "epoch"} <= keys
    ckpts = [a for a in read_artifacts(run) if a.kind == "checkpoint"]
    assert ckpts and all(Path(a.uri).parent == run / "checkpoints" for a in ckpts)
    assert ckpts[0].uri and (run / "checkpoints").is_dir()
    assert [e.kind for e in read_events(run)][-1] == "finished"


def test_lightning_handles_the_requeue_signal(script: Script, logdir: Path, tmp_path: Path) -> None:
    """With ``BeamtimeLogger`` created first, Lightning still installs its SLURM requeue handler:
    ``SIGUSR1`` saves its HPC checkpoint, and the run goes on to finish."""
    slurm = {
        "SLURM_JOB_ID": "42",
        "SLURM_JOB_NAME": "train",
        "SLURM_NTASKS": "1",
        "SLURM_NTASKS_PER_NODE": "1",
        "SLURM_PROCID": "0",
        "SLURM_LOCALID": "0",
        "SLURM_NODEID": "0",
    }
    proc = script(
        """
        import os, signal
        import torch, lightning as L
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset
        from beamtime.lightning import BeamtimeLogger

        class Model(L.LightningModule):
            def __init__(self):
                super().__init__()
                self.net = nn.Linear(4, 1)
            def training_step(self, batch, i):
                if self.current_epoch == 0 and i == 2:
                    os.kill(os.getpid(), signal.SIGUSR1)
                x, y = batch
                loss = nn.functional.mse_loss(self.net(x), y)
                self.log("train/loss", loss)
                return loss
            def configure_optimizers(self):
                return torch.optim.SGD(self.parameters(), lr=0.1)

        loader = DataLoader(TensorDataset(torch.randn(64, 4), torch.randn(64, 1)), batch_size=8)
        logger = BeamtimeLogger(dir="lightning")
        trainer = L.Trainer(max_epochs=2, logger=logger, enable_progress_bar=False,
                            enable_model_summary=False, accelerator="cpu", devices=1)
        trainer.fit(Model(), loader)
        """,
        env=slurm,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr.decode()[-3000:]
    assert list(tmp_path.glob("hpc_ckpt_*.ckpt")), proc.stderr.decode()[-3000:]
    assert read_run_info(only_run(logdir / "lightning")).status == "finished"
