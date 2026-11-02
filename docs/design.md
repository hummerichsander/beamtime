# Design

The rules every piece of Beamtime's interface follows. Read this before UI work.

Beamtime keeps track of numerical experiments for a person and their coding agent. It should read
like a lab notebook: warm paper, ink, a serif for what people write, one blue accent, and color only
where it means something.

## Where the system lives

| File | What it is |
|---|---|
| `src/beamtime/views/tokens.json` | The source of truth: colors, type, spacing, radius, layout, dashes, strokes. Also read by `serve`. |
| `web/src/styles/tokens.css` | Generated from it by `npm run tokens`. Never edit by hand; `npm test` fails when it is stale. |
| `web/src/styles/bundle.css` | The components' stylesheet: the design system's own, changed here from now on. |
| `web/src/styles/base.css`, `shell.css`, `blocks.css` | What the design system doesn't cover, on its tokens and type classes. |
| `web/src/styles/fonts/` | The fonts and their licenses, copied to `serve/static/fonts/` by the build. No CDN. |
| `src/beamtime/views/colormaps.json` | Colormaps sampled from matplotlib by `scripts/colormaps.py`. |

The original export is the "Beamtime" design system artifact, version `1793565179-4959`. This repo is
now the source of truth, and it has moved on from that export: see [Differences](#differences-from-the-export).

## Voice

- Plain and short. Say what a thing is or does: "Copy the run id", "No groups below." No exclamation
  marks, no emoji.
- States and data in lowercase, exactly as logged: `running`, `val/loss`, `lr-sweep`.
- Compact numbers (`3e-4`, `12.4k steps`, `2h ago`), the full value in the tooltip.
- Quiet: no toasts for success; errors where they happen, in `bad`. Empty things disappear.

## The proposal comes first

Every group page leads with its hypothesis, in its own Section labelled `proposal` right after the
header: the statement, one line of check pills, and the verdict with who gave it. It comes before any
numbers.

## Look

- **Color.** `paper` and `surface` for the page, `ink` and `muted` for text, `line` for hairlines,
  `border` for the edges of controls. `accent` is the only brand color: links, focus, selection,
  running. `good`, `bad` and `warn` are for states, always with an icon and a word. `line` is a
  separator only: never the only edge of a control.
- **Runs.** Run n is drawn in `data-n` with line style `dash-n` (solid, dashed, dotted, dash-dot, short
  dashes, long dashes), in charts, legends and table swatches alike, so runs stay apart in grayscale
  and for color-blind readers. Name the run beside its color. Beyond six, group runs instead of adding
  colors. A run's slot comes from a hash of its id, so it keeps its color and line style on every page.
- **Type.** XCharter (`serif`) for what people read: `heading`, `statement` (italic means proposed),
  `prose`, `caption`. IBM Plex Sans (`sans`) for the page name (`title`) and the interface: `body`,
  `small`, `number`. IBM Plex Mono for `code`, ids and margin labels. Put the style's class on the
  element; **the stylesheet never sets a size**. Numbers in tabular figures; bold the one that matters.
- **Rules.** Rules give the page its structure, never boxes or cards. A page is a column of Sections
  separated by `line` hairlines, each with a short mono label in the `margin` column behind a thin
  vertical rule. Table rows are separated by hairlines. Tables and figures get a numbered `caption`:
  the label ("**Fig. 1.**", "**Table 1.**") in the sans at 600, the caption itself in the serif italic.
- **Space.** `space-1` to `space-4` (4, 8, 16, 32px), and `gutter` (24px) around a Section's content.
  Prose at most `measure` wide, statements `measure-short`. A hover tint never touches its text: the
  content is inset from the tint, and the tint overhangs the column, so text still lines up down the page.
- **Page.** With room (a main area of 860px or more), the content column is centered in the main area,
  with the labels left of it and an equally wide empty column on the right.
- **Shape.** `radius` (6px) for buttons, fields and tints; `radius-pill` for tags. Flat: no shadows
  except on floating panels.
- **Motion.** Rare and fast (120–150ms), only for changes of state, off under reduced motion.
- **Icons.** Lucide shapes drawn hard, like the rules: `stroke-icon` (1.5px), square caps, mitred
  joins, in `currentColor`, usually `muted`; 14–16px. Render them with class `icon`. No emoji, no
  filled icons, and never as the only sign of a state.

## Themes and colormaps

The layout, type and spacing are fixed. A **theme file** recolors them: any color token above, in
`themes/` next to `beamtime.yaml` or in `~/.config/beamtime/themes/`
([Settings](guides/settings.md#themes)). Colors only ever change through tokens, so a theme reaches
everything. **Colormaps** are matplotlib's, chosen in the settings; they color numeric groups and
heatmaps, never individual runs.

## Components

Use the markup below, type classes included. `Section`, `Button`, `IconButton`, `Field` and `Tag` are in
`web/src/ui/primitives.ts`, `Sym` and `Icon` in `web/src/ui/icons.ts`, `Notice` in `web/src/blocks/common.ts`.

### Section

`<div class="sections"><section class="section"><div class="section-label code">runs</div><div>…</div></section></div>`

- The consumer provides the label and the content. Labels are one or two words, or a time and author,
  in `code` `muted`: `group`, `readings`, `runs`, `14:20 claude`.
- Every block of a page (header, stats, tables, charts, notes) sits in a section. Don't nest or box them.
- Under 640px the margin folds away and the label sits above the content.
- In a view, each top-level block gets a Section, labelled from its kind (`web/src/bt/labels.ts`). A
  title that only repeats the label isn't shown again.

### Header

`<nav class="crumbs small">`, `<h1 class="page-title title">` with its status as a Sym,
`<p class="facts">` with the numbers in `<b>`.

- Crumbs in `small` `muted`; the name in `title` with its status; facts in `muted` with the numbers in `ink`.
- The proposal is not part of the header: it follows in its own Section.

### Proposal

`<div class="proposal">`: `<p class="statement">`, `<div class="checks">` of `<span class="check small tone-good">`,
`<p class="verdict-line">`.

- The statement in `statement`, at most `measure-short` wide. Italic means proposed.
- The checks in one line of pills: the prediction's name in `small` 600 with its result's icon, tinted in
  the result's tone (pass `good`, fail `bad`, inconclusive `warn`, pending `muted`). Hovering or focusing
  a pill shows the result and what the check found; the same text is its accessible name. The line ends
  in plain `small` text, not a pill: `provisional` in `warn` while the plan is incomplete, and its
  progress in `muted`.
- The verdict below, as plain text: its icon and word in 600 in its tone, then "verdict by sander · 1h
  ago" in `small` `muted`. Before a verdict: `no verdict yet` in `muted`.
- Result and verdict are never color alone: the icon shape and the tooltip carry them too.

### Table

`<table class="runs">`, `<thead><tr class="small">`, `<span class="swatch run-1"></span>`,
`<td class="num best">`, `<p class="caption"><b>Table 1.</b> …</p>`.

- Hairlines between rows, a light accent tint on hover, the selected run tinted stronger.
- The first column is the run with its swatch: its color and line style, as in the charts. Numbers
  right-aligned in tabular figures; the best value per column bold.
- Headers in `small` `muted`, naming the metric (`val/loss`), not the aggregate.
- A numbered `caption` below. The number comes from a CSS counter; write `<b></b>`.

### Chart

`<figure class="chart">`: `<div class="chart-head"><b>val/loss</b><span class="small muted">seed mean</span></div>`,
the plot, `<div class="legend small">`, `<figcaption class="caption"><b></b> …</figcaption>`.

- A line chart without a frame. Run n is drawn in `data-n` with `dash-n` at `stroke-data`. Grid lines in
  `line`, axis labels in `small` `muted`.
- A run keeps its color and line style everywhere: chart, legend, table swatch. Name the run beside it.
- Beyond six runs, group them (seeds, a config value) rather than adding colors.

### Note

`<article class="note">`: `<div class="note-line">` with chevron, Sym, `<span class="heading">`,
`<span class="note-meta small">`; `<div class="note-body prose">`.

- The line: chevron, the note type as a Sym, the title in `heading`, `author · ago` in `small` `muted`.
- The body in `prose`, at most `measure` wide. Notes stay closed until clicked.

### Stat

`<div class="stats"><div><div class="stat-label small">runs</div><div class="number">12</div></div></div>`

- One number with a small label, no box. Value in `number`; add `live` while a run is still changing it.
- Compact numbers, the full value in the tooltip.

### Sym

`<span class="sym tone-accent"><svg class="icon"/><span class="small">running</span></span>`

- A state as an icon in its tone plus its word in `small`, so color never stands alone.
- Run: running, finished, failed, killed, lost. Check: pass, fail, inconclusive, pending. Verdict:
  confirmed, refuted. Note: observation, decision, idea, question.
- In dense rows the word may move to the tooltip, never disappear.

### Tag

`<span class="tag small tone-warn">provisional</span>`

- A one- or two-word qualifier next to a title or statement. Tones: `good`, `bad`, `warn`, `accent`,
  `muted`. Not for status (use Sym) or counts.

### Button

`<button class="button body"><svg class="icon"/>Save as view</button>`, with `danger` or `quiet`.

- An icon and a short label in `body` at 600, no fill: `accent` text, a thin edge in the text color on
  hover. `danger` is `bad` (inside a confirmation); `quiet` is `muted` for cancel and secondary actions.
- The icon leads and says what kind of action it is; the label says what happens.
- Where the icon alone is clear, use an IconButton.
- Few buttons: most actions are links, IconButtons or inline editing. One accent button per place.

### IconButton

`<button class="icon-button" aria-label="Copy the run id" data-tip="Copy the run id"><svg class="icon"/></button>`

- A square button that is only an icon (16px). The label says what happens and is both `aria-label` and
  tooltip. The app's tooltip is `data-tip` (`web/src/ui/tip.ts`), not the native `title`.
- `muted` at rest; on hover `ink` with a `border` edge. Pressed toggles are `accent`.

### Field

`<label class="field small"><span class="field-label">Filter runs</span><span class="input body"><input/></span><span class="field-hint error">…</span></label>`

- A label in `small` `muted` above an input with a `border` edge; `accent` while focused; an error below
  in `bad`.
- Search fields lead with the search icon. Placeholders say what can be typed, not "Search…".
- Errors say what is wrong, right under the field.

### Notice

`<p class="notice body warning"><svg class="icon tone-warn"/><span>…</span></p>`, or `error`, or no kind.

- A message where something happened: an empty state, a warning or an error, marked by a short rule in
  the margin rather than a box.
- Text in `muted`; the rule in `line` (info), `warn` or `bad`, with the matching icon.
- No notices for things that went right.

## Not in the design system

These parts have no component in the design system: top bar, sidebar and tree, status bar, drawer,
palette and dialogs, popover, tooltip, segmented control, tabs, multi-select, menu list, key-value
tables, disclosure, skeleton, Markdown, inline editing, log output, images, group list, add-chart,
cell tools, timeline, history and diff, chart settings. They follow the rules above with the tokens and
type classes above, and get no new looks of their own. When one needs more, extend this document first.

## Differences from the export

| Where | Export | Here | Why |
|---|---|---|---|
| `serif` family | `XCharter, Charter, 'Iowan Old Style', Georgia, serif` | `XCharter` | no system-font fallbacks for Charter |
| `tokens.css` | no rule before `data-theme` is set | a `prefers-color-scheme` block | no flash of light on dark systems |
| Tooltips in previews | `title=` | `data-tip=` | the app's own tooltip; both would show twice |
| `accent` usage note | "the primary button" | "the text of buttons" | buttons have no fill |
| Scales | none | matplotlib colormaps | heatmaps and numeric groups need ramps |
| Spacing | Sections in `space-3`, table cells flush left | `gutter`, cells inset | less cramped; hover tints clear their text |
