# Charts

Rules for every chart, built-in or drawn in code. `view_validate` warns about the ones marked ✓.

## Say what the chart shows

- **Label both axes.** The defaults come from `x` and `y` and are usually right. Set `xlabel` and
  `ylabel` when the name is a code key, or add the unit: `ylabel: "Energy error (eV)"`.
- ✓ **A caption says what the chart shows, never the axes**: the axes say that. Good: "Mean over
  seeds; the dip at step 2k is the learning-rate drop." Bad: "x: step, y: val/acc." A caption starting
  `x:` or over 140 characters gets a warning.
- **Put the setup in the caption** when it is not obvious: what varies, what is held fixed, how many
  runs or seeds. One or two sentences.
- A chart's `title` names the quantity ("Validation accuracy"), not the finding. The finding goes
  into the view's `finding:` or a `text` block.

## Many curves

- ✓ At most eight curves in a chart. Beyond that use `by: [<field>]` (mean and band per value),
  `seeds: config.seed` (seeds merged), or `color: <field>` (one hue per value, a ramp when numeric).
- Many metrics are not many curves: give each prefix its own `section` (`train`, `val`, `grads`), one
  chart per metric, instead of one chart with twenty lines.
- A band (`band: std | stderr | minmax`) needs at least two runs per group; say which in the caption.

## Axes and scales

- Training curves use `x: epoch` when the runs log it; otherwise steps. A clock (`_t`, `_elapsed`)
  is an x axis, not a chart of its own. A metric as x is never interpolated.
- `scale: log` only for values that stay positive (losses, learning rates, errors). For values that
  cross zero use `symlog`, which is linear near zero. Scatter has `x_scale` and `y_scale`.
- Sweeps over several orders of magnitude (`config.lr`) get `x_scale: log`.
- **Small multiples share the y range.** Charts that are compared side by side get the same
  `ymin` and `ymax`, or the eye compares different scales.
- `smooth` hides noise and also spikes: keep it low and keep `raw: true`, so the raw curve stays
  faintly visible.

## Example

```yaml
- section:
    title: validation
    children:
      - grid:
          columns: 2
          children:
            - line:
                y: val/loss
                x: epoch
                scale: log
                by: [config.optimizer]
                ylabel: "Validation loss"
                caption: "Mean and band over seeds; Adam converges first."
            - scatter:
                x: config.lr
                y: metric.val/acc.max
                x_scale: log
                seeds: config.seed
                caption: "Best accuracy per learning rate, mean over seeds."
```

## Colors and colormaps

Colors come from the theme. `color` and `by` pick a hue per value; `colormap` (a matplotlib name such
as `magma`) recolors a numeric or grouped chart, and the viewer can change it per chart. Never
encode meaning in a color alone: the legend and the caption carry it.
