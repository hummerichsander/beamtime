# Proposal

The hypothesis of a group with its checks and its verdict: the centre of every group page, in its own Section labelled `proposal`, right after the header.

- The statement in `statement`, at most `measure-short` wide. Italic means proposed.
- The checks in one line of pills: each pill is the prediction's name in `small` 600 with its result's icon, tinted in the result's tone (pass `good`, fail `bad`, inconclusive `warn`, pending `muted`). Hovering or focusing a pill shows the result and what the check found ("pass: max grad-norm < 10 … 9 of 9"); the same text is its accessible name. The line ends in plain `small` text, not a pill: `provisional` in `warn` while the plan is incomplete, and its progress in `muted`.
- The verdict below, as plain text: its icon and word in 600 in its tone (confirmed, refuted, inconclusive), then "verdict by sander · 1h ago" in `small` `muted`. Before a verdict: `no verdict yet` in `muted`.
- Result and verdict are never color alone: the icon shape and the tooltip carry them too.

## Markup

```html
<div class="proposal"><p class="statement">Warmup shortens the time to a stable loss.</p><div class="checks"><span class="check small tone-good" title="pass: max grad-norm &lt; 10 in every run with warmup ≥ 300 · 9 of 9" aria-label="no-spikes: pass. max grad-norm &lt; 10 in every run with warmup ≥ 300 · 9 of 9" tabindex="0"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>no-spikes</span><span class="check small tone-warn" title="inconclusive: steps to loss &lt; 0.5: 3.1k vs 3.4k, intervals overlap" aria-label="faster: inconclusive. steps to loss &lt; 0.5: 3.1k vs 3.4k, intervals overlap" tabindex="0"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon" aria-hidden="true"><path d="M5 12h14"/></svg>faster</span><span class="check small tone-muted" title="pending: waits for 3 running runs" aria-label="same-final: pending. waits for 3 running runs" tabindex="0"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon" aria-hidden="true"><path d="M5 22h14"/><path d="M5 2h14"/><path d="M17 22v-4.172a2 2 0 0 0-.586-1.414L12 12l-4.414 4.414A2 2 0 0 0 7 17.828V22"/><path d="M7 2v4.172a2 2 0 0 0 .586 1.414L12 12l4.414-4.414A2 2 0 0 0 17 6.172V2"/></svg>same-final</span><span class="small"><span class="tone-warn">provisional</span><span class="muted"> · 8 of 12 runs</span></span></div><p class="verdict-line"><span class="sym tone-good"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m16 9-5.5 5.5L8 12"/></svg><span class="verdict-word">confirmed</span></span><span class="small muted">verdict by sander · 1h ago</span></p></div>
```

## In the app

`ProposalSection` in `web/src/shell/header.ts`.

- The statement is `div.statement`, because it edits in place.
- Tooltips are `data-tip`, not `title`. Rationale and per-prediction numbers stay in the `proposal` block, labelled `predictions`.
