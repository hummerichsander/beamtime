# PyTorch Lightning

Pass Beamtime's logger to the `Trainer`:

```python
from lightning import Trainer
from beamtime.lightning import BeamtimeLogger

logger = BeamtimeLogger(dir="scaling/lr-sweep", config={"lr": 3e-4})
trainer = Trainer(logger=logger, max_epochs=10)
trainer.fit(model, datamodule)
```

`BeamtimeLogger` takes the same arguments as `beamtime.init()`.

- Everything you `self.log(...)` in your `LightningModule` is recorded.
- `self.save_hyperparameters()` fills the run's config.
- Checkpoints are written into the run's folder (`checkpoints/`) and listed with the run.
- On several GPUs only rank 0 records; nothing else is needed.

Both `lightning` and the older `pytorch_lightning` package work.
