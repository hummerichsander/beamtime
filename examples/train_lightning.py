"""A small Lightning job that outlives its wall-time limit, for checking a requeue by hand."""

import argparse
import time

import lightning as L
import torch
from torch import Tensor, nn
from torch.utils.data import DataLoader, TensorDataset

from beamtime.lightning import BeamtimeLogger


class Regression(L.LightningModule):
    """Fit a line to noisy points, slowly."""

    def __init__(self, *, lr: float, sleep: float) -> None:
        """Set up the model.

        :param lr: The learning rate.
        :param sleep: Seconds per step, so a job hits its limit."""
        super().__init__()
        self.save_hyperparameters()
        self.net = nn.Linear(1, 1)

    def training_step(self, batch: tuple[Tensor, Tensor], batch_idx: int) -> Tensor:
        """One step of mean squared error.

        :param batch: Inputs and targets.
        :param batch_idx: The batch index.
        :return: The loss."""
        x, y = batch
        loss = nn.functional.mse_loss(self.net(x), y)
        self.log("train/loss", loss)
        time.sleep(self.hparams.sleep)
        return loss

    def configure_optimizers(self) -> torch.optim.Optimizer:
        """Plain SGD.

        :return: The optimizer."""
        return torch.optim.SGD(self.parameters(), lr=self.hparams.lr)


def main() -> None:
    """Train to the end across as many requeued attempts as it takes."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--sleep", type=float, default=0.02, help="seconds per step")
    args = parser.parse_args()

    x = torch.rand(2048, 1)
    loader = DataLoader(TensorDataset(x, 3 * x + 0.1 * torch.randn_like(x)), batch_size=32)
    logger = BeamtimeLogger(dir="slurm-lightning", proposal="SGD finds the slope 3.")
    trainer = L.Trainer(
        max_epochs=args.epochs,
        logger=logger,
        callbacks=[L.pytorch.callbacks.ModelCheckpoint(save_last=True)],
        enable_progress_bar=False,
    )
    # the requeued job's logger continues the same run, so "last" is <run>/checkpoints/last.ckpt.
    trainer.fit(Regression(lr=args.lr, sleep=args.sleep), loader, ckpt_path="last")


if __name__ == "__main__":
    main()
