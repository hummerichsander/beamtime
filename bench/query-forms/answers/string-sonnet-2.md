### t01
```yaml
where: "run.status == finished"
```

### t02
```yaml
where: "config.lr < 1e-3"
```

### t03
```yaml
where: "config.lr >= 1e-4 and config.lr <= 1e-3"
```

### t04
```yaml
where: "config.warmup in [500, 1000]"
```

### t05
```yaml
where: "run.tags has baseline"
```

### t06
```yaml
where: "not run.tags has baseline"
```

### t07
```yaml
where: "run.status == finished and metric.val/acc.max >= 0.92"
```

### t08
```yaml
where: "run.status in [failed, killed]"
```

### t09
```yaml
where: "config.optimizer.name == adam and config.lr in [3e-4, 1e-3]"
```

### t10
```yaml
where: "run.name ~ 'boosted*'"
```

### t11
```yaml
where: "metric.train/loss.nonfinite >= 1"
```

### t12
```yaml
where: "metric.val/loss.mean[1000:2000] < 0.5"
```

### t13
```yaml
where: "config.optimizer.weight_decay exists"
```

### t14
```yaml
where: "proposal.check == fail and proposal.verdict == confirmed"
```

### t15
```yaml
where: "config.model.n_layers in [12, 24, 48] and config.model.dropout != 0"
```

### t16
```yaml
where: "config.batch_size >= 256 and config.lr <= 2e-3 and run.status != failed"
```

### t17
```yaml
where: "config.seed == 0 and (metric.train/loss.ema_last < 1.5 or metric.val/acc.max > 0.9)"
```

### t18
```yaml
where: "config['mixup.alpha'] > 0.2"
```

### t19
```yaml
where: "config.scheduler == 'cosine with restarts'"
```

### t20
```yaml
where: "not (run.status == lost or (run.status == running and run.steps < 1000))"
```
