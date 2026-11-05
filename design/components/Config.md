# Config

A nested config to read: branches that open and close, what varies between runs marked, a filter, and long values cut.

- A chain of single children reads as one name (`hparams.egnn.vector_channels`); the full key is in the tooltip.
- Keys that differ between runs get a small accent dot (`config-varies`), and "only what varies" hides the rest. The toggle appears only where the runs are known.
- Values: scalars as `value` shows them, an object as `{3 keys}`, a list of up to five as itself and a longer one as `[22 items]`. The tooltip holds the whole value; strings past 48 characters are cut, with a button to copy them.
- A small tree starts open, a large one closed; typing a filter opens every branch that matches.

## Markup

```html
<div class="config-tree" style="max-inline-size:520px"><div class="config-tools small"><span class="input"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><path d="m21 21-4.34-4.34"/><circle cx="11" cy="11" r="8"/></svg><input type="search" placeholder="Filter keys and values" aria-label="Filter the config"></span><label class="config-only"><input type="checkbox">only what varies</label></div><ul class="config-list"><li class="config-leaf small"><span class="config-key">arm</span><span class="config-value">large</span><span class="config-varies"></span></li><li class="config-leaf small"><span class="config-key">hparams.egnn.vector_channels</span><span class="config-value num">32</span><span class="config-varies"></span></li><li class="config-branch"><button type="button" class="config-toggle small" aria-expanded="true"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg><span class="config-key">hydrantic</span><span class="muted">3</span></button><ul class="config-list"><li class="config-leaf small"><span class="config-key">trainer.max_epochs</span><span class="config-value num">5</span></li><li class="config-leaf small"><span class="config-key">trainer.default_root_dir</span><span class="config-value">/scratch/synth/lightning/2026-10-20_09-4…</span></li><li class="config-leaf small"><span class="config-key">model.egnn</span><span class="config-value">{1 key}</span></li></ul></li><li class="config-branch"><button type="button" class="config-toggle small" aria-expanded="false"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg><span class="config-key">optimizer</span><span class="muted">6</span></button></li></ul></div>
```

## In the app

`ConfigTree` in `web/src/ui/config.ts` (the tree itself in `web/src/bt/configtree.ts`), used by the run drawer and the `config` block (`web/src/blocks/config.ts`), and in custom blocks as `bt.ui.Config`.
