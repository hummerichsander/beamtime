// Logged data: `images` and `text` of a data key, from the run's files.

import { html } from "htm/preact";

import { useContext, useEffect, useMemo, useRef, useState } from "preact/hooks";

import { type Call, useCall } from "../api.ts";
import { useData, ViewCtx, type Node, type ViewContext } from "../bt/index.ts";
import { ChartFrame, type DownloadSet } from "../bt/frame.ts";
import { step } from "../bt/fmt.ts";
import { host } from "../bt/host.ts";
import {
  clockAt, hasClock, indexAt, latestOf, nearest, scrubLabel, shownAt, stopsOf, type By, type Entry, type Meta, type Stops, type Tile,
} from "../bt/scrub.ts";
import { transform, useZoom } from "../bt/zoom.ts";
import { recording, rendering, sourcedRun } from "../router.ts";
import { EXPORTED, fileUrl } from "../snapshot.ts";
import { Store, useStore } from "../state.ts";
import { IconButton } from "../ui/primitives.ts";
import { Notice, Panel } from "./common.ts";

// where a viewer scrubbed an images block to; `step` null follows the newest logging. Kept for the
// session, so back and forward and the page's dialog find it again.
type Scrub = { step: number | null; by: By };
const scrubs = new Map<string, Store<Scrub>>();

function scrubOf(key: string, start: number | null): Store<Scrub> {
  if (!scrubs.has(key)) scrubs.set(key, new Store<Scrub>({ step: start, by: "step" }));
  return scrubs.get(key)!;
}

// a value that follows its input after it has been still for a moment.
function useSettled<T>(value: T, ms: number): T {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setSettled(value), ms);
    return () => clearTimeout(t);
  }, [value]);
  return settled;
}

// what the inline block and its dialog share: the stops, the figure of each run at the scrubbed stop
// and the scrubber's moves.
function useImages(node: Node) {
  const view = useContext(ViewCtx);
  const main = node.data!.main;
  const asked = main.params.step;
  const key = `${view.path}\0${node.id}`;
  const store = scrubOf(key, typeof asked === "number" ? asked : null);
  const state = useStore(store);
  const base = useCall(main);
  const meta: Meta | undefined = base.data?.meta;
  const by: By = state.by === "clock" && hasClock(meta) ? "clock" : "step";
  const stops: Stops = useMemo(() => stopsOf(meta, by), [meta, by]);
  const follows = state.step === null;
  const ranged = !(rendering || EXPORTED) && (asked === "last" || typeof asked === "number") && stops.steps.length > 1;
  const i = follows ? stops.steps.length - 1 : indexAt(stops, state.step!);
  const at = stops.steps[i] ?? 0;
  // the old figures stay until the new ones are there.
  const keep = useRef<{ entries: Entry[]; at: number } | null>(null);
  // fast scrubbing asks for the stop it rests on, not for every one it passes; with nothing shown yet, at once.
  const settled = useSettled(at, 120);
  const asking = keep.current ? settled : at;
  // the block's own answer holds the asked step, the newest logging only when the view asks for the last.
  const windowed = ranged && (!follows || asked !== "last");
  const call: Call | null = windowed ? { ...main, params: { ...main.params, step: ["last", asking], limit: 2000 } } : null;
  const result = useCall(call);
  const fresh = windowed ? result.data : base.data;
  if (fresh) keep.current = { entries: fresh.entries, at: windowed ? asking : Infinity };
  const plain = asked !== "last" && typeof asked !== "number";
  const tiles: Tile[] = !keep.current
    ? []
    : plain
      ? keep.current.entries.map((entry) => ({ entry, earlier: false }))
      : shownAt(keep.current.entries, keep.current.at);
  const clock = (main.params.clock as string | undefined) ?? null;
  const move = (to: number) => {
    const j = Math.min(stops.steps.length - 1, Math.max(0, to));
    store.set({ ...state, step: j === stops.steps.length - 1 ? null : stops.steps[j] });
  };
  return {
    view, base, error: result.status === "error" ? String(result.error) : null, tiles, stops, i, ranged, by, move, clock,
    label: scrubLabel(clock, clockAt(meta, at), at),
    clocked: hasClock(meta),
    setBy: (next: By) => store.set({ step: follows ? null : at, by: next }),
  };
}

type Shown = ReturnType<typeof useImages>;

function fileOf(view: ViewContext, e: Entry, title: string): [string, string] {
  const ext = e.path.split(".").at(-1);
  return [fileUrl(sourcedRun(e.run, view.path), e.path), `${e.run}-${title.replace(/[^\w.-]+/g, "_")}-step${e.step}.${ext}`];
}

function saveFiles(view: ViewContext, tiles: Tile[], title: string): void {
  for (const { entry } of tiles) host().download(...fileOf(view, entry, title));
}

// the two downloads of an images block: one image (the latest shown, or the dialog's), or every shown one.
function downloads(s: Shown, title: string, one: Tile | undefined, label: string): DownloadSet {
  return {
    files: [
      { label, save: () => one && saveFiles(s.view, [one], title) },
      { label: `All images (${s.tiles.length})`, save: () => saveFiles(s.view, s.tiles, title) },
    ],
  };
}

function Scrubber({ s }: { s: Shown }) {
  if (!s.ranged) return null;
  const { values } = s.stops;
  const keys: Record<string, number> = { ArrowLeft: s.i - 1, ArrowDown: s.i - 1, ArrowRight: s.i + 1, ArrowUp: s.i + 1, Home: 0, End: values.length - 1 };
  return html`<div class="scrubber">
    <input type="range" min=${values[0]} max=${values.at(-1)} step="any" value=${values[s.i]} aria-label="Step" aria-valuetext=${s.label}
      onInput=${(e: Event) => {
        const input = e.target as HTMLInputElement;
        const j = nearest(values, Number(input.value));
        input.value = String(values[j]);
        s.move(j);
      }}
      onKeyDown=${(e: KeyboardEvent) => {
        if (!(e.key in keys)) return;
        e.preventDefault();
        s.move(keys[e.key]);
      }} />
    <span class="small scrub-label">${s.label}</span>
  </div>`;
}

function ByTool({ s }: { s: Shown }) {
  if (!s.ranged || !s.clocked) return null;
  const name = s.clock?.split(/[/.]/).at(-1) ?? "clock";
  return html`<button type="button" class="small tool-toggle" aria-pressed=${s.by === "clock"} data-tip=${`Space the stops by ${name}`}
    onClick=${() => s.setBy(s.by === "clock" ? "step" : "clock")}>by ${name}</button>`;
}

export function Images({ node }: { node: Node }) {
  const s = useImages(node);
  const title = String(node.props.title ?? node.data!.main.params.key);
  if (node.props.expanded) return html`<${ImagesDialog} node=${node} s=${s} title=${title} />`;
  const open = (run?: string) => host().expand({ ...node, props: { ...node.props, run: run ?? s.tiles[0]?.entry.run } }, s.view);
  return html`<div class="block chart-block images-block">
    <${ChartFrame} id=${node.id} title=${title} caption=${node.props.caption}
      tools=${html`<${ByTool} s=${s} />`}
      downloads=${downloads(s, title, latestOf(s.tiles), "Latest image")} onExpand=${() => open()}>
      ${s.base.status === "error" ? html`<${Notice} kind="error">${s.base.error}<//>` : null}
      ${s.error ? html`<${Notice} kind="error">${s.error}<//>` : null}
      ${s.base.data && !s.tiles.length ? html`<${Notice}>No images logged.<//>` : null}
      <div class="images">
        ${s.tiles.map(
          ({ entry: e, earlier }) => html`<figure key=${`${e.run}/${e.path}`} class=${earlier ? "earlier" : ""} data-tip=${s.view.names.get(e.run) ?? e.run}>
            <button type="button" class="image-open" aria-label="Open larger" onClick=${() => open(e.run)}>
              <img src=${fileUrl(sourcedRun(e.run, s.view.path), e.path)} alt=${e.caption ?? title} loading=${recording ? "eager" : "lazy"} />
            </button>
            <figcaption class="small">step ${step(e.step)}${e.caption ? ` · ${e.caption}` : ""}</figcaption>
          </figure>`,
        )}
      </div>
      <${Scrubber} s=${s} />
    <//>
  </div>`;
}

// the page's dialog for logged images: one image as large as the dialog allows, zoomed and panned,
// with the scrubber below and the neighbours one click away.
function ImagesDialog({ node, s, title }: { node: Node; s: Shown; title: string }) {
  const { tiles } = s;
  // the chosen image is a run's, so scrubbing keeps it on that run.
  const [chosen, choose] = useState<string>(node.props.run);
  const z = useZoom();
  const index = Math.max(0, tiles.findIndex((t) => t.entry.run === chosen));
  const shown = tiles[index];
  const src = shown ? fileUrl(sourcedRun(shown.entry.run, s.view.path), shown.entry.path) : "";
  // another image or another step starts fitted.
  useEffect(() => z.fit(), [src]);
  const go = (by: number) => choose(tiles[(index + by + tiles.length) % tiles.length].entry.run);
  const keys: Record<string, () => void> = { "+": () => z.zoomBy(1.5), "=": () => z.zoomBy(1.5), "-": () => z.zoomBy(1 / 1.5), "0": z.fit };
  const tools = html`
    ${tiles.length > 1 ? html`<${IconButton} icon="chevron-left" label="Previous image" onClick=${() => go(-1)} /><${IconButton} icon="chevron-right" label="Next image" onClick=${() => go(1)} />` : null}
    <${IconButton} icon="minus" label="Zoom out (−)" onClick=${() => z.zoomBy(1 / 1.5)} />
    <${IconButton} icon="plus" label="Zoom in (+)" onClick=${() => z.zoomBy(1.5)} />
    <${IconButton} icon="reset" label="Fit (double-click, 0)" onClick=${z.fit} />
    <${ByTool} s=${s} />`;
  return html`<div class="block chart-block images-block">
    <${ChartFrame} id=${node.id} title=${title} expanded
      notes=${shown ? [s.view.names.get(shown.entry.run) ?? shown.entry.run, `step ${step(shown.entry.step)}`] : []}
      tools=${tools} downloads=${downloads(s, title, shown, "This image")}>
      <div class="zoom-box" ref=${z.box} tabindex="0" style=${{ touchAction: "none" }} ...${z.handlers}
        onKeyDown=${(e: KeyboardEvent) => keys[e.key]?.()}>
        ${shown ? html`<img class="zoom-img" src=${src} alt=${shown.entry.caption ?? title} draggable=${false} style=${{ transform: transform(z.pose) }} />` : null}
      </div>
      <${Scrubber} s=${s} />
    <//>
  </div>`;
}

export function Text({ node }: { node: Node }) {
  const result = useData("main");
  const entries: any[] = result.data?.entries ?? [];
  return html`<${Panel} title=${node.props.title} caption=${node.props.caption} result=${result}>
    ${result.data && !entries.length ? html`<${Notice}>No text logged.<//>` : null}
    ${entries.map(
      (e) => html`<div class="text-entry" key=${`${e.run}/${e.step}`}>
        <div class="muted small">step ${step(e.step)}${e.caption ? ` · ${e.caption}` : ""}</div>
        <pre class="code">${e.text ?? ""}</pre>
      </div>`,
    )}
  <//>`;
}
