// Figures for an export (`beamtime export --figures`): the renderer takes each block's downloads by
// its id, at a paper size, with the downloads captured instead of saved.

import { figures } from "../router.ts";
import { paper, type Background } from "./export.ts";
import { host, setHost } from "./host.ts";

export type Exporter = { png: (background: Background) => unknown; csv?: () => unknown; pdf?: () => unknown };
type Taken = { png?: string; svg?: string; csv?: string; pdf?: Record<string, unknown> };

const exporters = new Map<string, Exporter>();

// a block's downloads, kept while the renderer takes figures.
export function register(id: string | undefined, e: Exporter): void {
  if (figures && id) exporters.set(id, e);
}

export function install(): void {
  (window as any).__btFigures = () => [...exporters.keys()];
  (window as any).__btFigure = take;
}

async function take(id: string, size: { width: number; height: number }): Promise<Taken | null> {
  const e = exporters.get(id);
  if (!e) return null;
  const out: Taken = {};
  const own = host();
  paper.size = size;
  setHost({
    ...own,
    download: (href, name) => {
      if (name.endsWith(".csv")) out.csv = href;
      else if (name.endsWith(".svg")) out.svg = href;
      else out.png = href;
    },
    figure: async (spec) => {
      out.pdf = spec;
    },
  });
  try {
    await e.png("white");
    await e.csv?.();
    await e.pdf?.();
    // a custom block answers over its frame's bridge, a moment later.
    for (let i = 0; i < 50 && !out.png && !out.svg; i++) await new Promise((r) => setTimeout(r, 100));
  } finally {
    setHost(own);
    paper.size = null;
  }
  for (const k of ["png", "svg", "csv"] as const) if (out[k]) out[k] = await dataUrl(out[k]!);
  return out;
}

// a blob: URL read into a data: URL, so the renderer can take it out of the page.
async function dataUrl(href: string): Promise<string> {
  if (href.startsWith("data:")) return href;
  const blob = await (await fetch(href)).blob();
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.readAsDataURL(blob);
  });
}
