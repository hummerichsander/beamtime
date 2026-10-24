### t01
```yaml
where:
  run.status: finished
```

### t02
```yaml
where:
  config.lr: {lt: 1.0e-3}
```

### t03
```yaml
where:
  config.lr: {ge: 1.0e-4, le: 1.0e-3}
```

### t04
```yaml
where:
  config.warmup: {in: [500, 1000]}
```

### t05
```yaml
where:
  run.tags: {has: baseline}
```

### t06
```yaml
where:
  not:
    run.tags: {has: baseline}
```

### t07
```yaml
where:
  run.status: finished
  metric.val/acc.max: {ge: 0.92}
```

### t08
```yaml
where:
  run.status: {in: [failed, killed]}
```

### t09
```yaml
where:
  config.optimizer.name: adam
  config.lr: {in: [3.0e-4, 1.0e-3]}
```

### t10
```yaml
where:
  run.name: {glob: "boosted*"}
```

### t11
```yaml
where:
  metric.train/loss.nonfinite: {gt: 0}
```

### t12
```yaml
where:
  "metric.val/loss.mean[1000:2000]": {lt: 0.5}
```

### t13
```yaml
where:
  config.optimizer.weight_decay: {exists: true}
```

### t14
```yaml
where:
  proposal.check: fail
  proposal.verdict: confirmed
```

### t15
```yaml
where:
  config.model.n_layers: {in: [12, 24, 48]}
  config.model.dropout: {ne: 0}
```

### t16
```yaml
where:
  config.batch_size: {ge: 256}
  config.lr: {le: 2.0e-3}
  run.status: {ne: failed}
```

### t17
```yaml
where:
  config.seed: 0
  any:
    - metric.train/loss.ema_last: {lt: 1.5}
    - metric.val/acc.max: {gt: 0.9}
```

### t18
```yaml
where:
  'config["mixup.alpha"]': {gt: 0.2}
```

### t19
```yaml
where:
  config.scheduler: "cosine with restarts"
```

### t20
```yaml
where:
  not:
    any:
      - run.status: lost
      - run.status: running
        run.steps: {lt: 1000}
```
