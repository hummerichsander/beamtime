# Type in custom blocks and views

**The family says who wrote the text.** No exceptions:

- **Serif** (`prose`, `caption`) only for sentences a person or an agent wrote: an explanation, a
  note shown in a block. `statement` is for proposals, never in blocks.
- **Sans** (`body`, `small`, `number`, `heading`) for everything the block names, labels, counts or
  states: axis titles, ticks, legends, run, group and metric names, status and verdict words,
  numbers. A name stays sans even when a person chose it.
- **Mono** (`code`) as an accent for keys, ids, paths and values as logged. Never a sentence.

## Custom code

Never set a font family, size, the `font` shorthand or a line height: not in inline styles, not in
d3 `.attr` or `.style`, not in SVG attributes, not in a `<style>`. Put a type class on the element;
the frame loads the app's stylesheet. `view_validate` reports every font literal as an error.

| Class | Font | Use |
|---|---|---|
| `body` | sans 15 | the frame's default: controls, cells, facts |
| `heading` | sans 17, 600 | a title inside a block, only through `bt.ui.Section` |
| `small` | sans 12.5 | axis ticks and titles, legends, table headers, meta, status words |
| `num` | tabular figures | every number in a column or on an axis, together with `small` or `body` |
| `number` | sans 24, 700 | one headline value; prefer `bt.ui.Stat` |
| `prose` | serif 15.5 | sentences inside a block |
| `caption` | serif italic 14 | a figure's caption; prefer the block's `caption` |
| `code` | mono 13 | run ids, metric and config keys, paths, values as logged |
| `title` | sans 35 | never in blocks |

```js
html`<span class="small num">${bt.fmt.value(v)}</span> <span class="code">${key}</span>`
```

- **SVG text:** `class="small num"` for ticks, `class="small"` for axis titles, and
  `fill="var(--muted)"`. Downloads keep the look: the snapshot copies the computed font.
- **Canvas:** `ctx.font = bt.theme.tokens.font`, the only font string code uses.
- **Emphasis:** bold (`<b>`) only for the one value that matters. No italic of your own (italic
  means proposed or live), no uppercase, no letter-spacing.

## Views

- `title` is plain text. One or two lowercase words become the section label, in mono above the
  block or in its collapse toggle; a longer title is a sans `heading`.
- `caption` is plain text in the serif italic: one sentence, keys as logged, no backticks.
- Markdown fields (`markdown` blocks, notes, memory) render as `prose`: keys, ids and values in
  backticks (`code`), math as `$…$` (KaTeX), raw HTML shows as text. A `##` renders as a bold
  serif heading, not the sans `heading`: use a section title instead.
