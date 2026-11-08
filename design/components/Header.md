# Header

The top of every page: where you are, the name with its status, one line of facts.

- Crumbs in `small` `muted`; the name in `title` with its status; facts in `muted` with the numbers in `ink`.
- The proposal is not part of the header: it follows in its own Section, labelled `proposal`, right below.

## Markup

```html
<nav class="crumbs small"><a href="#">local</a> / <a href="#">scaling</a></nav><h1 class="page-title title">warmup <span class="sym tone-accent"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="icon " aria-hidden="true"><circle cx="12" cy="12" r="1"/><circle cx="12" cy="12" r="10"/></svg><span class=small>running</span></span></h1><p class="facts"><span><b>12</b> runs</span><span><b>3</b> running</span><span><b>8</b> finished</span><span>best <b>val/loss 0.412</b> · <a href="#">warmup-500</a></span></p>
```

## In the app

`Header` in `web/src/shell/header.ts`.

- A group's facts add "N code versions" (git-commit icon, tooltip: versions by run count) only when its runs ran on different code.
- A run's details popover is a `table.kv` of what is known (code, copied from, checkpoints) with a collapsed "Uncommitted changes" disclosure below; a missing checkpoint gets a warn `Tag` "missing" and its reason, never a link.
- Run pages use `div.facts`: the line holds a popover, which a `p` can't.
- The view's source and links follow below the facts, in `.view-source small`.
