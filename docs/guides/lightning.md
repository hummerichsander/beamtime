# PyTorch Lightning

```python
from lightning import Trainer
from beamtime.lightning import BeamtimeLogger

logger = BeamtimeLogger(dir="scaling/lr-sweep", config={"lr": 3e-4})
trainer = Trainer(logger=logger, max_epochs=10)
trainer.fit(model, datamodule)
```

`BeamtimeLogger` takes the same arguments as `beamtime.init()`, and works with `lightning` and
`pytorch_lightning`.

- Everything you `self.log(...)` is recorded.
- `self.save_hyperparameters()` fills the run's config.
- Checkpoints go into the run's `checkpoints/` folder and are listed with the run.
- On several GPUs only rank 0 records.
