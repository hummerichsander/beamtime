# Benchmark plan: notes

Working notes behind [benchmark-plan.md](benchmark-plan.md), 2026-11-15, base `fb352bd`.

## What the existing harness gives

- `bench/agents/run.py`: one fresh project per task × model × rep, synth seed 7, Beamtime's MCP
  server, tools `Read,Write,Edit,Glob,Grep`, `claude -p --output-format stream-json`, 900 s limit,
  `summary()` reads the tool calls, turns, `usage` and cost from the transcript. Broken since A12 (the
  rules block moved to `beamtime.guide.rules`; Finding 1).
- `score.py`: graders by kind; `ask()` is the judge (reusable); analysis facts are regexes fixed to
  seed 7.
- `report.py`: per-run rows and means per kind and model; `--base/--new` deltas.
- Last full batch `runs/20261108-213034` (156 runs, haiku and sonnet).

## Measured costs (sonnet, Beamtime over MCP, batch 20261108-213034)

| kind | sessions | input | cache write | cache read | output | seconds | USD |
|---|---|---|---|---|---|---|---|
| analysis | 33 | 5 | 12,750 | 54,783 | 683 | 12.0 | 0.063 |
| verdict | 3 | 8 | 12,749 | 91,732 | 1,428 | 13.1 | 0.074 |
| view | 33 | 21 | 23,745 | 336,128 | 3,318 | 40.0 | 0.162 |

The floor of about 50k tokens per session is the system prompt, CLAUDE.md and 48 tool schemas, cached.

## Cost of one full run (estimate)

96 agent sessions (8 tasks × 4 setups × 3 seeds) and 12 judge calls (the chart task outside a
timeout). Per-session guesses, sonnet; the baselines are guesses, the pilot replaces them:

| setup | tokens / session | USD / session | seconds | 24 sessions |
|---|---|---|---|---|
| Beamtime MCP | ~90k | ~0.10 | ~30 | ~2.2M tokens, ~$2.4 |
| Beamtime CLI | ~120k | ~0.13 | ~40 | ~2.9M, ~$3.1 |
| plain files | ~350k | ~0.35 | ~120 | ~8.4M, ~$8.4 |
| TensorBoard | ~500k | ~0.50 | ~180 | ~12M, ~$12 |

Total about 26M tokens (over 90 % cache reads) and about $26 at list price, plus about $0.6 of judge
calls, so roughly **$25–35** or the equivalent subscription usage; the pilot (seed 7, 32 sessions) is a
third of that. Serial wall time about 2.5 h; with 3 in parallel about 50 min. Disk: about 25 MB per
project (11 MB log dir plus exports) while a session runs; projects are deleted after grading.

Assumptions: the chart task costs about twice an analysis task; baselines take 4–8× the turns of
Beamtime because the agent first reads the layout and writes pandas scripts; nobody hits the time
limits; no retries.

## W&B

Offline mode (`WANDB_MODE=offline`) writes `wandb/offline-run-*/run-*.wandb` for a later
`wandb sync`. The public API (`wandb.Api`) reads only from a W&B server: the cloud, or W&B Server
(`wandb/local`), which needs a license key tied to an account. Reading the `.wandb` protobuf files
directly is an internal, unsupported path no researcher uses. So no fully offline setup; out. Not run.

## Seeds and the planted effects (reproduced)

Final val/acc in scaling/lr-sweep, completed runs only, Welch 95 % for best vs runner-up:

| seed | best | runner-up | difference | CI | significant | 3e-4 mean with the killed run |
|---|---|---|---|---|---|---|
| 7 | 3e-4 | 1e-3 | 0.0079 | [-0.0002, 0.0160] | no | 0.910 (runner-up 0.920) |
| 8 | 3e-4 | 1e-3 | 0.0025 | [-0.0172, 0.0222] | no | 0.910 (0.923) |
| 9 | 3e-4 | 1e-3 | 0.0066 | [0.0011, 0.0122] | yes | 0.911 (0.922) |
| 10 | 3e-4 | 1e-3 | 0.0129 | [0.0048, 0.0210] | yes | 0.915 (0.918) |
| 11 | 3e-4 | 1e-3 | 0.0120 | [0.0008, 0.0233] | yes | 0.911 (0.917) |

TensorBoard 2.21.0 (scratch env, no TensorFlow): `EventFileWriter` + `summary_v2.hparams_pb` write,
`EventAccumulator` reads back `[(0, 1.0), (1, 0.5), (2, nan)]`.
