# Layer 7: Web UI

Status: **reviewed; v1 scope per the [overview](00-overview.md#scope)**

The web UI is what `beamtime serve` shows in a browser: locally, on a remote reached by port
forwarding ([layer 4](04-remotes.md)), and later on a self-hosted server ([layer 6](06-server.md)).
It is a reader for views ([layer 5](05-views.md)) and a navigator through groups, runs and notes.

## Principles

1. **Seamless, light, concise.** The UI's feel is a main selling point, held to measurable budgets
   (see [Feel](#feel)).
2. **A fixed, well-designed shell.** The layout of the app doesn't change; the flexibility lives in
   the views. Rearrangeable panels (e.g. with dockview) are deferred until users need them.
3. **The theme colors everything.** The shell, the header, built-in blocks and custom blocks all read
   the same tokens.
4. **Every state has a URL.** Groups, runs, view versions, selections and comparisons can be linked,
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
| Charting code | loaded only when a chart is on screen | uPlot (about 25 KB), the Markdown renderer and KaTeX load lazily and stay cached |
| First view, local, warm cache | < 300 ms to a complete header and visible blocks | rendered from run cards and previews; exact data follows |
| Group to group | < 100 ms | client-side navigation, no page reload; links to groups prefetch their page on hover |
| Selection, hover, toggles | < 50 ms | handled in the page, no server round trip |
| Layout shift | none | blocks reserve their size before data arrives; live updates never move content |
| Spinners | none under 300 ms | content appears in place; a skeleton with the final layout only when it takes longer |

### Light

- **A notebook, not a dashboard.** Pages read like a lab notebook: warm paper, ink, a serif for
  titles and the texts people and agents write, larger type. Sections are separated by whitespace
  and hairlines, not boxes. The top bar and status bar are thin (48 and 30 px); the sidebar collapses
  with one key. Most of the screen is the view.
- **One accent color**, warm neutral surfaces, no gradients; color means data or status
  ([layer 5](05-views.md#the-default-theme)).
- **Typography carries the structure**: serif titles and statements, italic for proposals, bold for
  the numbers that matter, tabular lining figures, a base size of 15 px.
- **Symbols instead of words**: run status, check results, verdicts, research status and note types
  each have an icon, a color and a word (or a tooltip), so color never stands alone.
- **Quiet feedback**: rows, tree items, links and charts answer the pointer with a light tint; icon
  buttons explain themselves in a tooltip; chart tools appear on hover.
- **Motion is rare and fast**: 120–150 ms ease-out, only for changes of state (opening the drawer,
  expanding a section, moving between groups), never decorative, and off when the system asks for
  reduced motion.

### Concise

- **The header fits in three lines**: breadcrumb and title with the research status, the proposal's
  statement with a symbol per prediction, the plan's progress and the verdict, and one line of facts
  (runs by status, notes, the best value of the main metric and which run reached it). Details are
  in tooltips and the context drawer.
- **Texts written by agents fold away**: notes show one line each and open on click; the memory
  starts folded.
- **Empty things disappear.** A group without a proposal shows no proposal row; a section without
  data collapses into one line.
- **Numbers are compact** (`3e-4`, `93.1 %`, `12.4k steps`, `4h 12m`), with full values in tooltips.
- **No redundant labels**: a chart says what it shows in a short note beside its title ("seed mean");
  table headers name the metric, not "last".
- **No modal dialogs for navigation, no notification toasts** for things that went right. Errors are
  shown where they happen.

### Seamless

- **Back and forward restore everything**: scroll position, selection, open drawer, chart zoom.
- **Live data arrives without flicker** ([Live updates](#live-updates)).
- **Remote latency is hidden**: remote run cards and previews are cached, so remote groups open as
  fast as local ones and refine when fresh data arrives. Losing a connection shows a quiet marker on
  the source, not a blocking message.
- **Writes feel instant**: a note appears immediately and is confirmed in the background; a failed
  write is shown in place.
- **Links always work**: every URL opens in a new tab with the same state.

### Keeping it that way

- **Deterministic budgets are tested in CI**: the bundle sizes, and the import time of the CLI
  ([overview](00-overview.md#testing-strategy)). A change that breaks one fails.
- **Timing budgets are measured before each release**, on log dirs from the evaluation harness
  generator ([layer 5](05-views.md#evaluation-harness)), because timings on shared CI machines are too
  noisy to gate on.
- **A UI review checklist** for every UI change: does it add chrome, a click, a spinner, a dialog or
  a dependency? Each needs a reason.

## Shell

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ top bar:   project · search (⌘K) · sources · theme · settings                │
├──────────────┬─────────────────────────────────────────────┬─────────────────┤
│ sidebar      │ header: breadcrumb · title · status ·       │ context drawer  │
│              │         statement · predictions · facts     │ (toggle)        │
│ group tree   ├─────────────────────────────────────────────┤                 │
│ per source:  │                                             │ selected runs:  │
│  local       │ view body                                   │ run card,       │
│  @cluster    │ (built-in blocks, custom blocks)            │ config, notes,  │
│              │                                             │ output tail     │
│ status marks │                                             │                 │
│ run counts   │                                             │ or: group       │
│              │                                             │ notes, timeline │
├──────────────┴─────────────────────────────────────────────┴─────────────────┤
│ status bar: live · updated · running · failed · indexer · selection · pause  │
└──────────────────────────────────────────────────────────────────────────────┘
```

- **Top bar**: project name, the command palette (⌘K), the state of each source (local, connected or
  unreachable remotes), a light/dark/theme switch, settings.
- **Sidebar**: the group tree, one top-level entry per source ([layer 4](04-remotes.md#naming-remote-groups)),
  with run counts and status dots (running, failed, lost). It loads lazily and can be filtered.
- **Header**, owned by Beamtime and identical on every view:
  - a small breadcrumb, the group's name as title and its research status (`open`, `proposed`,
    `running`, `evaluable`, `concluded`; [research record](09-research-record.md#group-status));
  - the proposal's statement, with a symbol per prediction (effect and interval on hover), the
    plan's progress and the current verdict;
  - the facts: run counts by status, notes, the best value of the main metric with the run and
    config that reached it; and the view's `finding`.

  A run's header shows its name and status, steps, duration and start, its best value, and the
  proposals it belongs to; id, host, commit and job are in a tooltip.
- **View body**: the group's view, inherited or its own.
- **Context drawer**, opened on demand: for selected runs their run card, config, latest notes and
  output tail; with no selection, the group's notes and timeline.
- **Status bar**: whether the page is live and when data last changed, the running runs and the runs
  that failed since the last visit (each opens the palette filtered to them), indexer lag and
  unreadable runs, remote connections, the selection, and the pause switch.

On narrow screens the sidebar and drawer collapse into overlays; phones get a read-only layout with
the header and the view.

## Pages and URLs

| URL | Page |
|---|---|
| `/f/<source>/<path>` | a group with its view (`/f/local/scaling/lr-sweep`, `/f/@cluster/scaling`) |
| `/r/<run-id>` | a run, by id; redirects to its group URL, so links survive moves |
| `/f/...?v=<version>` | a specific saved version of the group's view |
| `/f/.../history` | the view's version list; any two versions side by side with their YAML diff and screenshots |
| `/compare?runs=<a>,<b>` | two runs side by side: config diff, card values, curves (v1.1 with the `compare` block) |
| `/search?q=…` | groups, runs, notes and blocks matching the query |
| `/settings/...` | appearance (themes), blocks, remotes, about |

Selections live in the URL (`?sel=<ids>`) once linked blocks arrive
([layer 5](05-views.md#linking-blocks-wave-2)). `beamtime status` and the CLI print these URLs, so agents
can hand users a link to exactly the view or run they talk about.

## Navigation

- **Command palette (⌘K)**: groups, runs by name or id, notes by description, library blocks, and
  commands (switch theme, export, copy link).
- **Keyboard**: arrow keys in the tree, `[`/`]` for previous and next sibling group, `Esc` clears the
  selection, `?` lists shortcuts.
- **Breadcrumb** in the header for moving up.

## Rendering stack

**Frontend**

- **Preact with `htm`**, the same library custom blocks use, plus the `bt` kit. The shell is written
  in TypeScript and bundled with esbuild when Beamtime is released; users never build anything.
- **Built-in blocks render in the page**; **custom blocks** in sandboxed iframes ([layer 5](05-views.md#sandbox)).
- **Charts on uPlot** with the theme's colors and fonts ([layer 5](05-views.md#charts)).
- **Markdown** for notes and memory through `marked`, with raw HTML shown as text and KaTeX for
  math; both load on first use.
- **Lazy rendering**: blocks render when they scroll into view; custom-block iframes are created
  then too.

**Backend**

- `serve` uses **Starlette on uvicorn**: small and asynchronous, with streaming responses for live
  updates. Validation and serialization use msgspec, so no FastAPI is needed.
  These dependencies live in `beamtime[serve]`, not in the SDK.
- The browser talks to the same API as remotes and agents ([layer 4](04-remotes.md#protocol)):
  `POST /api/<method>`, the operations of [layer 8](08-cli-mcp.md#operations).
- Static assets (the bundled frontend, uPlot, the Markdown renderer, KaTeX and its fonts, D3,
  Preact) are served from the installed package.

## Live updates

Nothing is reloaded when data changes, neither the page nor the view:

1. **The page subscribes** to the queries of its visible blocks over **server-sent events**
   (`/api/subscribe`), a one-way stream that passes proxies easily.
2. **The server names only affected queries.** When a run's files change, `serve` determines which
   subscribed queries depend on that run and sends their ids, at most once per second per query.
3. **The page refetches those queries.** Answers come from previews, cards and the index and are small.
4. **Only the affected blocks re-render.** `bt.useData` re-renders the one component that uses the
   query, and Preact patches only the DOM elements whose content changed.
5. **Charts update in place.** uPlot receives new data through `setData`; zoom, hidden runs and
   hover are kept.
6. **Custom blocks** receive the new results over the `postMessage` bridge; their iframe is never
   reloaded, so their own state survives.

For the reader, scroll position, selection and zoom stay where they are, blocks keep their size, and a
running curve simply grows. A **pause** switch in the status bar stops refetching while reading.
Values of running runs are marked as still changing.

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
same frontend in headless Chromium through Playwright. The renderer is a client
([layer 3](03-index.md#freshness-the-daemon)): it uses the running `serve` if there is one, and
otherwise serves the frontend and the needed query answers itself for the duration of the render,
without indexing or watching anything. A small pool of browser pages is kept warm, so repeated renders in the agent loop
take a second or two, not a browser start each time. Playwright and its Chromium are part of
`beamtime[serve]`; the browser is downloaded on first use. Where Chromium cannot run (login nodes
often lack its system libraries), rendering reports that it was skipped and validation stays static.

## Static export

```sh
beamtime export scaling/lr-sweep --html out/                # a self-contained HTML snapshot
beamtime export scaling/lr-sweep --html out/ --points all   # with exact, full-resolution curves
beamtime export scaling/lr-sweep --figures figs/            # one figure per block
```

- **HTML**: one folder with an `index.html`, the frontend, libraries, and every block's query results
  frozen as JSON. It opens from disk without a server, keeps interaction within blocks over the
  frozen data, and states when it was taken. Placeholder queries are answered for the values present
  in the snapshot. Browsers don't load ES modules from `file://`, so the export bundles each custom
  block as a classic script inlined into its iframe (`srcdoc`).
- **`--points`** sets how many points per curve the export stores: a number of buckets (default
  1000), or `all` for every logged point. The export states which it used.
- **Figures**: each block on its own at paper sizes (3.3 × 2.5 in single-column, 6.9 × 2.5 in
  double-column) in the light theme. Charts draw on canvas and export as high-resolution PNG (and
  their data as CSV); custom blocks export as SVG if they draw SVG, otherwise as PNG. For vector
  figures in a paper, plot the exported CSV with matplotlib.

A PDF report and a dedicated print theme come later.

## Security

- The UI always requires the token of [layer 4](04-remotes.md#mode-2-port-forwarding), locally too,
  since `serve` cannot tell a laptop from a shared login node; it binds to `localhost` only. The
  bundled static JavaScript is public and served without the token, so sandboxed custom blocks,
  which have no origin, can load it; data and everything else require the token.
- A strict content security policy on every page: scripts and styles only from `serve`, no outside
  requests. Custom blocks are additionally sandboxed. Charts load no data of their own: everything
  comes from declared queries ([layer 5](05-views.md#charts)).
- **Writes from the page** go through the same operations as the CLI, as the local account
  ([Writing from the UI](#writing-from-the-ui)); a page cannot write anything the operations don't.

## Writing from the UI

The texts agents and people write are edited where they stand, without a dialog: click the text,
change it, and it saves on Enter (⌘Enter in longer texts) or when the field loses focus; Esc puts
it back. Files are never changed ([layer 1](01-storage.md)), so every edit is a new file:

| Text | An edit writes |
|---|---|
| a note's title or body | a new note that `supersedes` it, with its typed fields carried over (what it resolves, completes, cites and judges); a verdict takes a fresh check snapshot, as every note records the check at the time it is written |
| the memory | a new memory version |
| a proposal's statement | a new proposal version, but only while no run has recorded it; a frozen statement is locked and says how to supersede it |

New notes (observation, idea, question, decision) are added from the Notes heading. Superseded notes
are hidden; `beamtime notes --current` does the same for agents. The author is the local account;
agents keep writing through the CLI and MCP with their model id. A save shows at once, is confirmed
when the refetched answer arrives, and a failed save reopens the field with the error.

Saving a chart layout as a view comes with authored views (M6): "Save as view" writes the current
panels as a new view version. Until then chart settings stay with each viewer
([Charts](#charts)).

## Charts

Line charts behave like W&B's panels:

- **Hover**: a crosshair synced across the view; the tooltip lists every curve at that step, sorted,
  with its color; hovering a curve dims the others, and the run under the pointer is highlighted in
  every block (table rows, legends, other charts).
- **Legend**: click hides or shows a curve, shift-click shows only it; the run table's color dots do
  the same for runs. Hidden runs apply to every chart of the view.
- **Zoom**: drag zooms one chart's x axis and refetches that step window for exact points;
  double-click or the reset button zooms out. Live data keeps the zoom.
- **Settings per chart**: the metrics shown, x axis (step, wall time, elapsed time), smoothing
  (TensorBoard's debiased EMA, computed in the page over the curve, with the raw curve faint behind),
  log scale, an outlier-robust y range (1st to 99th percentile), aggregation over seeds or by a
  varying config key, and the band (min to max, ± std, ± std error, none).
- **View-wide**: a bar above the charts sets smoothing, x axis, aggregation and outliers for every
  chart (a chart's own setting wins), shows hidden runs again, and adds a chart for another metric.
- **Tools on hover**: download as PNG or CSV, and expand into a large dialog.

Settings, added charts and hidden runs are kept per viewer in the browser, by group; "reset" returns
to the view's defaults.

## Accessibility

Keyboard navigation everywhere, visible focus rings (`focus` token), the default theme's contrast,
and reduced motion when the system asks for it. Theme validation and a high-contrast pair come later.

## Later

- Rearrangeable panels (dockview), if users need side-by-side work beyond the context drawer and
  `compare`.
- PDF export and a print theme.
- Packages contributing panels or pages, like VS Code extensions.
- Zooming time axes with an exact refetch (the server's window is in steps today).
- Wording fixes on frozen proposals, if they turn out to be needed: today a frozen statement is
  locked, because a new version would leave its runs behind.
- The community gallery pages in settings ([layer 5](05-views.md#later)).

## Implementation notes

Decided while building the shell (milestone M5):

- **The token** is created once per root (`serve.token` in the cache, mode 0600) and reused, so a
  browser stays signed in across restarts. The printed URL carries it once; the server answers with
  an HttpOnly, `SameSite=Strict` cookie named after the port (cookies ignore ports) and drops the
  token from the URL. API clients may send `Authorization: Bearer <token>` instead.
- **The API** is `POST /api/<method>` for every operation that isn't user-only, under its MCP tool
  name (`runs`, `card`, `note_add`, …), with the same parameters and answers as `--json`; non-finite
  numbers are `null`. The web UI is a caller of its own (`view`): its answers use the view defaults
  of [layer 3](03-index.md#implementation-notes) and are never cut at the token budget. Three methods
  serve the shell only: `meta` (project, version, the resolved theme pair), `view` (the view of a
  group or run, with a run id resolved to its path) and `watch`. Logged images come from
  `GET /api/file/<run-id>/<path>`, confined to the run's directory.
- **Live updates**: the page opens one `EventSource` on `/api/subscribe?client=<id>` and tells the
  server with `watch` which calls it shows, each with its scope (a group or run path). The daemon
  reports changed run and group paths after every poll; a call is stale when the changed path is its
  scope, lies below it, or lies above it (a group's notes and proposal reach the runs below). The
  stream sends `stale` events with call ids, at most one a second per page; the page refetches those
  calls, keeps the old answer on screen while it does, and updates charts through uPlot's
  `setData`. After a reconnect it refetches everything on screen.
- **The built-in default view** is built on the server as a block tree (`{block, id, props, data,
  children}`, where `data` names API calls), the same tree authored views will compile to in M6. A
  group with runs of its own gets at most four essential charts (validation and test metrics, then
  training losses; averaged over `config.seed` beyond eight runs) and the rest under a folded "More
  metrics", the run table (name, status, varying config, the main metric, a sparkline), its memory
  and its latest notes. A group whose runs all live in subgroups gets its groups and the recent runs
  (with group and start time) instead. A run gets its charts, logged images and text, and its output
  (open when it failed). The header covers the proposal, so there is no proposal block or stat
  tile in the default view.
- **URLs**: `/f/local/<path>` for groups and runs (a run's path ends in its id), `?run=<id>` for the
  run open in the drawer, `?drawer=1` for the group's notes and timeline, `/r/<id>` resolving to the
  run's path, `/settings/appearance`. `?v=`, `/history`, `/search` and `/compare` come with the
  milestones that add views and comparisons.
- **Keyboard**: ⌘K or `/` for the palette, arrows in the tree, `[` and `]` for siblings, `i` for the
  drawer, ⌘B or `b` for the sidebar, `p` to pause live updates, `Esc` to clear the selection and close
  the drawer, `?` for the list.
- **The frontend** lives in `web/` (Preact 10, htm, uPlot, lucide icons, marked and KaTeX,
  TypeScript checked by `tsc`, bundled by esbuild). The bundle in `src/beamtime/serve/static/` is
  committed, so installs from git need no Node; CI rebuilds it and fails when it differs. The shell
  is about 41 KB compressed; uPlot (about 25 KB), the Markdown renderer (15 KB) and KaTeX (77 KB,
  woff2 fonts only) are lazy chunks.
- **API methods for the shell**: besides `meta`, `view` and `watch`, `summary` answers the main
  metric's best run for the header, apart from the view so both load in parallel.
- **Modern platform features**: the palette, help and expanded charts are `<dialog>`s
  (`closedby="any"` with a fallback for Safari); popover panels use the `popover` attribute and are
  placed from script, since anchor positioning isn't everywhere yet; one small tooltip serves every
  `data-tip` (shown after a delay, hoverable, Escape dismisses), since interest invokers are
  Chromium-only; page changes cross-fade with view transitions (only the page, never the shell),
  and focus moves to the new heading unless it stayed in the tree; inline editors grow with
  `field-sizing: content`; Enter that confirms an IME composition doesn't save.
- **Measured** on the generator's scale-M log dir (495 runs, 352 in one sweep, `bench/web/timing.py`,
  local, warm cache): first view median 136–151 ms (budget 300 ms), group to group median 80 ms
  (budget 100 ms; slowest about 115 ms), the longest pointer event while sweeping a chart median
  16 ms (budget 50 ms).
- **Not yet**: custom-block iframes and the `postMessage` bridge, the headless renderer and static
  export (M6), remote sources in the tree and status bar (M7), D3.

## Decisions

- The UI must feel seamless, light and concise, with budgets: shell ≤ 120 KB, first view < 300 ms,
  navigation < 100 ms, interactions < 50 ms, no layout shift, no spinners under 300 ms. Bundle size
  is tested in CI; timings are measured before releases.
- A fixed shell: top bar, sidebar with the group tree per source, header and view, a context drawer,
  a status bar. The header is defined here.
- A notebook-like look: warm paper, a serif for titles and written texts, larger type, symbols
  instead of words, whitespace instead of boxes, quiet hover feedback.
- Charts are uPlot everywhere, with W&B-like interactions; chart settings stay with each viewer
  until views can be saved from the UI (M6).
- Texts written by agents and people are edited in place; each edit is a new file (a superseding
  note, a new memory or proposal version); frozen proposals are not edited.
- The theme colors the whole app; shell tokens follow VS Code's workbench colors.
- Every state has a URL, including view versions.
- Preact with `htm` and the `bt` kit in the browser, built with esbuild at release; Starlette on
  uvicorn behind `serve`.
- Live updates: server-sent notifications of affected queries, refetch, in-place chart updates, no
  reloads.
- One renderer for the browser, screenshots and exports, run headless through Playwright; it is a
  client and degrades to static validation without Chromium.
- Static export as self-contained HTML and per-block figures; `--points` sets the curve resolution.
- View history is a version list with YAML diff and screenshots of two versions.
