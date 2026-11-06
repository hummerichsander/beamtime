# Design

The rules every piece of Beamtime's interface follows. Read this before UI work; each component's rules
and markup are in [components/](components/), its icons in [icons.md](icons.md), and
[gallery.html](gallery.html) shows them all on one page.

Beamtime keeps track of numerical experiments for a person and their coding agent. It should read
like a lab notebook: warm paper, ink, a serif for what people write, one blue accent, and color only
where it means something.

## Where the system lives

| File | What it is |
|---|---|
| `tokens.json` | The single source of all values: colors per theme, type, spacing, radius, layout, dashes, strokes. Change values here only. The build copies it to `serve/static/`, because `serve` reads it to resolve themes. |
| `tokens.css` | Generated from it by `scripts/build-tokens`. Never edit by hand; CI fails when it is stale. |
| `components.css` | The components' stylesheet. |
| `fonts/` | The fonts and their licenses (XCharter: Bitstream Charter license; IBM Plex: SIL OFL 1.1). The build copies them to `serve/static/fonts/`. No CDN. |
| `web/src/styles/base.css`, `shell.css`, `blocks.css` | What the design system doesn't cover, on its tokens and type classes. CI fails on raw hex colors and pixel font sizes there. |
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
([Settings](../docs/guides/settings.md#themes)). Colors only ever change through tokens, so a theme reaches
everything. **Colormaps** are matplotlib's, chosen in the settings; they color numeric groups and
heatmaps, never individual runs.

## Components

Use the markup on each component's page, type classes included. Component CSS sets layout, color and
weight only; font sizes come only from the type classes.

- Page: [Section](components/Section.md), [Header](components/Header.md), [Proposal](components/Proposal.md)
- Data: [Table](components/Table.md), [Chart](components/Chart.md), [Note](components/Note.md), [Stat](components/Stat.md),
  [Config](components/Config.md)
- Controls: [Sym](components/Sym.md), [Tag](components/Tag.md), [Button](components/Button.md),
  [IconButton](components/IconButton.md), [Field](components/Field.md), [Notice](components/Notice.md)

## Not in the design system

These parts have no component in the design system: top bar, sidebar and tree, status bar, drawer,
palette and dialogs, popover, tooltip, segmented control, tabs, multi-select, key-value
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
| Chart axis font | `small` (12.5px) | 13px, in `src/beamtime/views/theme.py` | uPlot only scales whole-pixel fonts |
