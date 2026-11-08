# Predictions

An automatic prediction is checked in four steps: select the runs, reduce each run to one number,
merge seeds, test. Results: `pass`, `fail`, `inconclusive`, `insufficient`, `pending`.

## Fields

- `reduce: {metric, stat, steps}`: `stat` is `first`, `last`, `min`, `max` or `mean`; `steps: [a, b]`
  is a window, `null` leaves an end open (`[100, null]`).
- `where`: narrows the runs, in the condition syntax of queries (`guide queries`).
- `seeds: config.seed`: runs that agree on everything else form one point with repetitions.
- `test`: `each` (default) or `compare`. (`trend` and `best` are planned and rejected today.)
- `op` (`<`, `<=`, `>`, `>=`), `value` or `ref: {run: <id>}`, and `margin`.
- `kind: manual` with a `description`: a claim no query can compute; it stays `pending` until a
  verdict decides it.

## each: every point meets a bound

```yaml
predictions:
  - name: converges
    reduce: {metric: val/acc, stat: max}
    seeds: config.seed
    op: ">"
    value: 0.9
```

With seeds, each point gets a t-interval of its mean. The point passes when the whole interval is
above 0.9, fails when it is all below, and is `inconclusive` otherwise. Without `seeds` the values
decide directly and the result says that no uncertainty was taken into account.

## compare: a beats b

```yaml
predictions:
  - name: warmup-better
    test: compare
    a: {config.warmup: {gt: 0}}
    b: {config.warmup: 0}
    reduce: {metric: val/acc, stat: max}
    seeds: config.seed
    pair_by: [config.lr]
    op: ">"
    margin: 0.01
```

A Welch interval for the difference of the means of `a` and `b` (a paired t-interval with `pair_by`).
`a > b + margin` passes when the interval's lower end exceeds the margin, fails when its upper end is
below it. The margin is the size of the claim: "better" without one is rarely worth testing.

A ratio such as "2.7x the cost per step" is not a difference: log the ratio as a metric
(`cost/ratio`) and use `each` with `value: 2.7`, or compare log-costs with a margin of `log(2.7)`.

## Statistics, honestly

- Two to five seeds are the norm; with three the t multiplier is 4.3, so only clear effects pass.
  That is intended: add seeds rather than loosening the claim.
- Fewer than two repetitions per point (or per side of a compare) give `insufficient`.
- `significance: 0.99` raises the level; `significance: none` decides on the values and says so.
- Pick the window deliberately: `steps: [100, 200]` for a spike, no window for a final value.
- A metric that is not logged yet makes the prediction `pending`, not failed.
