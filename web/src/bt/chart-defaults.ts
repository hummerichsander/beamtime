// Beamtime: generated from views/settings.py by scripts/build-chart-defaults. Do not edit by hand.
export const SEEDS_FIELD = "config.seed";
export const LOWER_IS_BETTER = ["loss", "losses", "err", "error", "errors", "ppl", "perplexity", "nll", "mse", "rmse", "mae", "wer", "cer"];
export const DEFAULTS = {
  line: {
    band: "minmax",
    by: null,
    color: null,
    colormap: null,
    legend: true,
    outliers: false,
    raw: true,
    scale: null,
    smooth: 0.0,
    steps: null,
    x: "_step",
    ymax: null,
    ymin: null,
  },
} as const;
