# Layer 7: Web UI

Status: **draft, under discussion**

The web UI is what `beamtime serve` shows in a browser: locally, on a remote reached by port
forwarding ([layer 4](04-remotes.md)), and later on a self-hosted server ([layer 6](06-server.md)).
It is a reader for views ([layer 5](05-views.md)) and a navigator through folders, runs and notes.

## Principles

1. **Seamless, light, concise.** The UI's feel is a main selling point, held to measurable budgets
   (see [Feel](#feel)).
2. **A fixed, well-designed shell.** The layout of the app doesn't change; the flexibility lives in
   the views. Rearrangeable panels (e.g. with dockview) are deferred until users need them.
3. **The theme colors everything.** The shell, the frame, built-in blocks and custom blocks all read
   the same tokens.
4. **Every state has a URL.** Folders, runs, view versions, selections and comparisons can be linked,
   so people and agents can point at exactly what they mean.
5. **Fast first, exact on demand.** Pages render from run cards and previews; exact data loads when a
   block needs it.
6. **One renderer.** The browser, `view_render` screenshots and static exports use the same frontend,
   so what agents check is what readers see.
7. **Offline and self-contained.** All assets ship with Beamtime; the UI makes no requests outside
   `serve`.

## Feel

The UI should feel **seamless, light and concise**; it is one of Beamtime's main selling points.
These qualities are made concrete as budgets and rules, and checked like correctness.

### Budgets

| Measure | Budget | How it is met |
|---|---|---|
| Shell JavaScript | ≤ 120 KB compressed | Preact and `htm` instead of a large framework; no UI kit dependency |
| Charting code | loaded only when a chart is on screen | Vega/Vega-Lite (the largest libraries) and uPlot load lazily and stay cached |
| First view, local, warm cache | < 300 ms to a complete frame and visible blocks | rendered from run cards and previews; exact data follows |
| Folder to folder | < 100 ms | client-side navigation, no page reload; the tree prefetches folders on hover |
| Selection, hover, toggles | < 50 ms | handled in the page, no server round trip |
| Layout shift | none | blocks reserve their size before data arrives; live updates never move content |
| Spinners | none under 300 ms | content appears in place; a skeleton with the final layout only when it takes longer |

### Light

- **Content first.** The top bar and status bar are thin (about 40 and 24 px); the sidebar collapses
  with one key. Most of the screen is the view.
- **One accent color**, neutral surfaces, no shadows or gradients; color means data or status
  ([layer 5](05-views.md#the-default-theme)).
- **Typography carries the structure**: a small type scale, tabular figures for numbers, generous
  but not loose spacing, in the density of GitHub or VS Code.
- **Motion is rare and fast**: 120–150 ms ease-out, only for changes of state (opening the drawer,
  expanding a section), never decorative, and off when the system asks for reduced motion.

### Concise

- **The frame fits in two or three lines**: breadcrumb, proposal with check badges, verdict and run
  counts, finding. Details open in the context drawer.
- **Empty things disappear.** A folder without a proposal shows no proposal row; a section without
  data collapses into one line.
- **Numbers are compact** (`3e-4`, `93.1 %`, `12.4k steps`, `4h 12m`), with full values in tooltips.
- **No redundant labels**: a chart's caption replaces a title that would only repeat the axes.
- **No modal dialogs for navigation, no notification toasts** for things that went right. Errors are
  shown where they happen.

### Seamless

- **Back and forward restore everything**: scroll position, selection, open drawer, chart zoom.
- **Live data arrives without flicker** ([Live updates](#live-updates)).
- **Remote latency is hidden**: remote run cards and previews are cached, so remote folders open as
  fast as local ones and refine when fresh data arrives. Losing a connection shows a quiet marker on
  the source, not a blocking message.
- **Writes feel instant**: a note appears immediately and is confirmed in the background; a failed
  write is shown in place.
- **Links always work**: every URL opens in a new tab with the same state.

### Keeping it that way

- **Budgets are tested**: bundle sizes and the timing budgets are measured in CI with Playwright, on
  log dirs from the evaluation harness generator ([layer 5](05-views.md#evaluation-harness)). A
  change that breaks a budget fails.
- **Visual regression**: screenshots of the shell and the example views in light and dark are
  compared on every change.
- **A UI review checklist** for every UI change: does it add chrome, a click, a spinner, a dialog or
  a dependency? Each needs a reason.

## Shell

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ top bar:   project · search (⌘K) · sources · theme · settings                │
├──────────────┬─────────────────────────────────────────────┬─────────────────┤
│ sidebar      │ frame:  breadcrumb · proposal and check ·   │ context drawer  │
│              │         verdict · run status · finding      │ (toggle)        │
│ folder tree  ├─────────────────────────────────────────────┤                 │
│ per source:  │                                             │ selected runs:  │
│  local       │ view body                                   │ run card,       │
│  @cluster    │ (built-in blocks, custom blocks)            │ config, notes,  │
│              │                                             │ output tail     │
│ status dots  │                                             │                 │
│ run counts   │                                             │ or: folder      │
│              │                                             │ notes, timeline │
├──────────────┴─────────────────────────────────────────────┴─────────────────┤
│ status bar: daemon and indexer · freshness · remotes · selection             │
└──────────────────────────────────────────────────────────────────────────────┘
```

- **Top bar**: project name, the command palette (⌘K), the state of each source (local, connected or
  unreachable remotes), a light/dark/theme switch, settings.
- **Sidebar**: the folder tree, one top-level entry per source ([layer 4](04-remotes.md#naming-remote-folders)),
  with run counts and status dots (running, failed, lost). It loads lazily and can be filtered.
- **Frame** ([layer 1](01-storage.md#structure)): breadcrumb, the proposal with a badge per
  prediction, the current verdict, run counts by status, and the view's `finding`. Below it, small
  view metadata: author, when saved, outdated block pins.
- **View body**: the folder's view, inherited or its own.
- **Context drawer**, opened on demand: for selected runs their run card, config, latest notes and
  output tail; with no selection, the folder's notes and timeline.
- **Status bar**: whether the daemon runs, how fresh the data is, remote connections, and how many
  runs are selected.

On narrow screens the sidebar and drawer collapse into overlays; phones get a read-only layout with
the frame and the view.

## Pages and URLs

| URL | Page |
|---|---|
| `/f/<source>/<path>` | a folder with its view (`/f/local/scaling/lr-sweep`, `/f/@cluster/scaling`) |
| `/r/<run-id>` | a run, by id; redirects to its folder URL, so links survive moves |
| `/f/...?v=<version>` | a specific saved version of the folder's view |
| `/f/.../history` | the view's version list; any two versions side by side with their YAML diff and screenshots |
| `/compare?runs=<a>,<b>` | two runs or groups side by side (the `compare` block, full page) |
| `/search?q=…` | folders, runs, notes and blocks matching the query |
| `/settings/...` | appearance (themes), blocks and packages, remotes, about |

Selections live in the URL (`?sel=<ids>`), as defined for linked blocks
([layer 5](05-views.md#linking-blocks)). `beamtime status` and the CLI print these URLs, so agents
can hand users a link to exactly the view or run they talk about.

## Navigation

- **Command palette (⌘K)**: folders, runs by name or id, notes by description, library blocks, and
  commands (switch theme, export, copy link).
- **Keyboard**: arrow keys in the tree, `[`/`]` for previous and next sibling folder, `Esc` clears the
  selection, `?` lists shortcuts.
- **Breadcrumb** in the frame for moving up.

## Rendering stack

**Frontend**

- **Preact with `htm`**, the same library custom blocks use, plus the `bt` kit. The shell is written
  in TypeScript and bundled with esbuild when Beamtime is released; users never build anything.
- **Built-in blocks render in the page**; **custom blocks** in sandboxed iframes ([layer 5](05-views.md#sandbox)).
- **Vega-Lite** through `vega-embed`, with the theme's generated `config`.
- **Lazy rendering**: blocks render when they scroll into view; custom-block iframes are created
  then too.

**Backend**

- `serve` uses **Starlette on uvicorn**: small, asynchronous, with streaming responses for live
  updates and for MCP over HTTP. Validation and serialization use msgspec, so no FastAPI is needed.
  These dependencies live in `beamtime[serve]`, not in the SDK.
- The browser talks to the same API as remotes and agents ([layer 4](04-remotes.md#protocol)):
  `POST /api/<method>`.
- Static assets (the bundled frontend, Vega, D3, uPlot, KaTeX, Preact) are served from the installed
  package.

## Live updates

Nothing is reloaded when data changes, neither the page nor the view. Updates are granular down to
single DOM elements and chart data points:

1. **The page subscribes** to the queries of its visible blocks over **server-sent events**
   (`/api/subscribe`), a one-way stream that is simpler than WebSockets and passes proxies easily.
2. **The server sends only affected queries.** When new lines arrive in a run's files, `serve`
   determines which subscribed queries depend on that run and notifies only those.
3. **Updates are deltas.** Run files are append-only and downsampled curves have fixed bucket edges
   ([layer 1](01-storage.md#_previewjson), [layer 3](03-index.md#recommendation)), so for a running
   run only the last bucket changes and new buckets are appended. The server sends just these, with a
   cursor; run tables receive changed rows keyed by run id.
4. **Only the affected blocks re-render.** `bt.useData` re-renders the one component that uses the
   query, and Preact patches only the DOM elements whose content changed.
5. **Charts update in place.** Vega-Lite views receive new data through Vega's data API
   (`view.change`), uPlot through `setData`, so zoom, hover and selection are kept.
6. **Custom blocks** receive deltas over the `postMessage` bridge; their iframe is never reloaded, so
   their own state (an open detail panel, a selected run) survives.

For the reader, scroll position, selection, open tabs and zoom stay where they are, blocks keep their
size so the layout doesn't jump, and a running curve simply grows. Updates are coalesced to at most
one per second per block. A **pause** switch in the status bar freezes the page while reading;
resuming applies the accumulated deltas. Values of running runs are marked as still changing.

## Theme in the UI

The theme tokens of [layer 5](05-views.md#tokens) gain a group for the shell, modelled on VS Code's
workbench colors so imported VS Code themes map almost one to one:

| Beamtime token | Used for | VS Code color it is imported from |
|---|---|---|
| `sidebar.bg`, `sidebar.fg` | sidebar | `sideBar.background`, `sideBar.foreground` |
| `topbar.bg` | top bar | `titleBar.activeBackground` |
| `statusbar.bg`, `statusbar.fg` | status bar | `statusBar.background`, `statusBar.foreground` |
| `list.active`, `list.hover` | selected and hovered tree items | `list.activeSelectionBackground`, `list.hoverBackground` |
| `input.bg`, `input.border` | search and form fields | `input.background`, `input.border` |
| `button.bg`, `button.fg` | buttons | `button.background`, `button.foreground` |
| `badge.bg`, `badge.fg` | counts and status badges | `badge.background`, `badge.foreground` |
| `focus` | focus rings | `focusBorder` |
| `tooltip.bg` | tooltips | `editorHoverWidget.background` |
| `scrollbar` | scrollbars | `scrollbarSlider.background` |

Missing shell tokens fall back to the surface and text tokens, so a theme that defines only the core
colors still produces a consistent shell.

## Screenshots and the headless renderer

`view_render` and the render stage of `view_validate` ([layer 5](05-views.md#validation)) load the
same frontend in headless Chromium through Playwright, pointed at a local `serve` (started in-process
if none runs). A small pool of browser pages is kept warm, so repeated renders in the agent loop
take a second or two, not a browser start each time. Playwright and its Chromium are part of
`beamtime[serve]`; the browser is downloaded on first use.

## Static export

```sh
beamtime export scaling/lr-sweep --html out/        # a self-contained HTML snapshot
beamtime export scaling/lr-sweep --html out/ --points all   # with exact, full-resolution curves
beamtime export scaling/lr-sweep --pdf report.pdf   # a printable report
beamtime export scaling/lr-sweep --figures figs/    # one figure per block
```

- **HTML**: one folder with an `index.html`, the frontend, libraries, and every block's query results
  frozen as JSON. It opens without a server, keeps interaction within blocks (selection, hover,
  click-to-detail over the frozen data) and states when it was taken. Placeholder queries are
  answered for the values present in the snapshot.
- **`--points`** sets how many points per curve the export stores: a number of buckets (default
  1000, as in the browser), or `all` for every logged point. Downsampled exports stay small;
  `--points all` keeps exact numbers at the cost of size. The export states which it used.
- **PDF**: the view rendered with the **print** theme ([layer 5](05-views.md#the-default-theme)) in
  headless Chromium, with page breaks between sections and interactive blocks in their default
  state.
- **Figures**: each block on its own at paper sizes (3.3 × 2.5 in single-column, 6.9 × 2.5 in
  double-column) in the print theme. Vega-Lite blocks export as vector PDF or SVG; custom blocks as
  SVG if they draw SVG, otherwise as high-resolution PNG.

## Security

- On a shared machine the UI requires the token of [layer 4](04-remotes.md#mode-2-port-forwarding);
  locally it binds to `localhost` only.
- A strict content security policy on every page: scripts and styles only from `serve`, no outside
  requests. Custom blocks are additionally sandboxed.

## Accessibility

Keyboard navigation everywhere, visible focus rings (`focus` token), contrast guaranteed by
`beamtime theme validate`, the high-contrast theme pair, and reduced motion when the system asks
for it.

## Later

- Rearrangeable panels (dockview), if users need side-by-side work beyond the context drawer and
  `compare`.
- Packages contributing panels or pages, like VS Code extensions.
- The community gallery pages in settings ([layer 5](05-views.md#later)).

## Decisions

- The UI must feel seamless, light and concise, with tested budgets: shell ≤ 120 KB, first view
  < 300 ms, navigation < 100 ms, interactions < 50 ms, no layout shift, no spinners under 300 ms.
- A fixed shell: top bar, sidebar with the folder tree per source, frame and view, a context drawer,
  a status bar. View layouts stay agent-authored.
- The theme colors the whole app; shell tokens follow VS Code's workbench colors.
- Every state has a URL, including view versions and selections.
- Preact with `htm` and the `bt` kit in the browser, built with esbuild at release; Starlette on
  uvicorn behind `serve`; live updates over server-sent events.
- One renderer for the browser, screenshots and exports, run headless through Playwright.
- Static export as self-contained HTML, PDF in the print theme, and per-block figures at paper sizes;
  `--points` sets the curve resolution of an export, up to `all`.
- View history is a version list with YAML diff and screenshots of two versions.
- Live updates are granular: affected queries only, deltas with a cursor, in-place chart updates, no
  reloads.
