// Build the documentation site: docs/**/*.md (the pages docs/nav.json lists) into ../site, in
// Beamtime's look, light and dark. Links and images are checked; a broken one fails the build.
// Every page gets the app's top bar with search (⌘K), and search.json indexes every section.

import { existsSync } from "node:fs";
import { readdir, readFile, writeFile, mkdir, rm, copyFile } from "node:fs/promises";
import { dirname, join, normalize, relative } from "node:path";
import { Marked } from "marked";


const docs = "../docs";
const out = "../site";
const repo = "https://github.com/hummerichsander/beamtime";
const nav = JSON.parse(await readFile(join(docs, "nav.json"), "utf8"));
const pages = nav.sections.flatMap((s) => s.pages);
const titles = Object.fromEntries(
  await Promise.all(pages.map(async (p) => [p, (await readFile(join(docs, p), "utf8")).match(/^# (.+)$/m)?.[1] ?? p])),
);
// the sidebar's icon per page, from the icons the app uses (lucide).
const PAGE_ICONS = {
  "index.md": "house", "quickstart.md": "rocket", "how-it-works.md": "lightbulb",
  "guides/agents.md": "bot", "guides/research-record.md": "target", "guides/views.md": "layout-panel-top",
  "guides/cluster.md": "server", "guides/remotes.md": "network", "guides/lightning.md": "zap",
  "guides/export.md": "share-2", "guides/settings.md": "settings", "reference/cli.md": "terminal",
};
const icons = await loadIcons([
  ...new Set([...Object.values(PAGE_ICONS), "file-text", "search", "sun", "moon", "monitor", "panel-left",
    "corner-down-left", "arrow-up-right"]),
]);
const broken = [];
const assets = new Set();
const index = [];

await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });
// the site uses the design system's tokens and fonts as they are.
await writeFile(join(out, "docs.css"), (await readFile("../design/tokens.css", "utf8")) + (await readFile("docs/docs.css", "utf8")));
await mkdir(join(out, "fonts"), { recursive: true });
for (const f of await readdir("../design/fonts")) await copyFile(`../design/fonts/${f}`, join(out, "fonts", f));
await copyFile("docs/docs.js", join(out, "docs.js"));
await writeFile(join(out, ".nojekyll"), "");
for (const [i, page] of pages.entries()) {
  const html = render(page, await readFile(join(docs, page), "utf8"));
  collect(page, html);
  const file = join(out, page.replace(/\.md$/, ".html"));
  await mkdir(dirname(file), { recursive: true });
  await writeFile(file, layout(page, html, pages[i - 1], pages[i + 1]));
}
for (const asset of assets) {
  await mkdir(dirname(join(out, asset)), { recursive: true });
  await copyFile(join(docs, asset), join(out, asset));
}
await writeFile(join(out, "search.json"), JSON.stringify(index));
if (broken.length) {
  console.error(`broken links:\n  ${broken.join("\n  ")}`);
  process.exit(1);
}
console.log(`wrote ${pages.length} pages, ${assets.size} images and ${index.length} search entries to site/`);

async function loadIcons(names) {
  const entries = await Promise.all(names.map(async (name) => {
    const { __iconData } = await import(`./node_modules/lucide-preact/dist/esm/icons/${name}.mjs`);
    const body = __iconData.node
      .map(([tag, attrs]) => `<${tag} ${Object.entries(attrs).filter(([k]) => k !== "key").map(([k, v]) => `${k}="${v}"`).join(" ")}/>`)
      .join("");
    return [name, body];
  }));
  return Object.fromEntries(entries);
}

function icon(name, size = 16) {
  return `<svg class="icon" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" ` +
    `stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icons[name]}</svg>`;
}

function render(page, text) {
  const marked = new Marked({
    gfm: true,
    renderer: {
      heading({ tokens, depth }) {
        const inner = this.parser.parseInline(tokens);
        if (depth === 1) return `<h1>${inner}</h1>\n`;
        const id = slug(inner.replace(/<[^>]+>/g, ""));
        return `<h${depth} id="${id}">${inner}<a class="anchor" href="#${id}" aria-label="Link to this section">#</a></h${depth}>\n`;
      },
      link({ href, title, tokens }) {
        const inner = this.parser.parseInline(tokens);
        const external = /^https?:/.test(href);
        return `<a href="${target(page, href)}"${title ? ` title="${title}"` : ""}${external ? ' class="external"' : ""}>${inner}</a>`;
      },
      image({ href, text }) {
        return figure(page, href, text);
      },
    },
  });
  return marked.parse(text);
}

// a figure next to its -light and -dark variants shows the one that matches the page's mode.
function figure(page, href, alt) {
  const file = normalize(join(dirname(page), href)).replace(/\\/g, "/");
  if (!existsSync(join(docs, file))) {
    broken.push(`${page}: ${href}`);
    return "";
  }
  const variant = (mode) => file.replace(/\.svg$/, `-${mode}.svg`);
  const rel = (f) => relative(dirname(page), f).replace(/\\/g, "/");
  const a = alt.replace(/"/g, "&quot;");
  if (file.endsWith(".svg") && existsSync(join(docs, variant("light"))) && existsSync(join(docs, variant("dark")))) {
    assets.add(variant("light"));
    assets.add(variant("dark"));
    const img = (mode) => `<a class="only-${mode}" href="${rel(variant(mode))}" title="Open at full size">` +
      `<img src="${rel(variant(mode))}" alt="${a}"></a>`;
    return `<span class="figure">${img("light")}${img("dark")}</span>`;
  }
  assets.add(file);
  return `<span class="figure"><a href="${rel(file)}" title="Open at full size"><img src="${rel(file)}" alt="${a}"></a></span>`;
}

// a link to another page becomes its .html; one to a page that isn't part of the site is broken.
function target(page, href) {
  if (/^[a-z]+:|^#/.test(href)) return href;
  const [file, hash] = href.split("#");
  const to = normalize(join(dirname(page), file)).replace(/\\/g, "/");
  if (!pages.includes(to)) broken.push(`${page}: ${href}`);
  return file.replace(/\.md$/, ".html") + (hash ? `#${hash}` : "");
}

// one search entry per section: the page's lead, then each h2 and h3 with its text.
function collect(page, html) {
  const url = page.replace(/\.md$/, ".html");
  const parts = html.split(/(?=<h[23] id=")/);
  for (const part of parts) {
    const head = part.match(/^<h[23] id="([^"]+)">(.*?)<a class="anchor"/);
    const body = part.replace(/^<h[23][^>]*>.*?<\/h[23]>/, "").replace(/<h1>.*?<\/h1>/, "");
    const text = plain(body).slice(0, 600);
    if (!head && !text) continue;
    index.push({ url: head ? `${url}#${head[1]}` : url, page: titles[page], section: head ? plain(head[2]) : "", text });
  }
}

function plain(html) {
  return html.replace(/<pre[\s\S]*?<\/pre>/g, " ").replace(/<\/?(p|li|ul|ol|h\d|tr|td|th|table|blockquote|br)\b[^>]*>/g, " ").replace(/<[^>]+>/g, "").replace(/&amp;/g, "&").replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/\s+/g, " ").trim();
}

function slug(text) {
  return text.toLowerCase().replace(/&[a-z]+;/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

function layout(page, html, prev, next) {
  const up = relative(dirname(page), ".").replace(/\\/g, "/");
  const root = up ? `${up}/` : "";
  const href = (p) => root + p.replace(/\.md$/, ".html");
  const sections = nav.sections
    .map((s) => `<h2>${s.title}</h2><ul>${s.pages
      .map((p) => `<li><a href="${href(p)}"${p === page ? ' aria-current="page"' : ""}>${icon(PAGE_ICONS[p] ?? "file-text")}<span>${titles[p]}</span></a></li>`)
      .join("")}</ul>`)
    .join("");
  const toc = [...html.matchAll(/<h2 id="([^"]+)">(.*?)<a class="anchor"/g)]
    .map(([, id, inner]) => `<li><a href="#${id}">${inner.replace(/<[^>]+>/g, "")}</a></li>`)
    .join("");
  const pager = [
    prev ? `<a class="prev" href="${href(prev)}"><span>Previous</span>${titles[prev]}</a>` : "",
    next ? `<a class="next" href="${href(next)}"><span>Next</span>${titles[next]}</a>` : "",
  ].join("");
  const title = page === "index.md" ? "Beamtime" : `${titles[page]} · Beamtime`;
  return `<!doctype html>
<html lang="en" data-root="${root}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
<script>try { const m = localStorage.getItem("beamtime-docs-mode"); if (m === "light" || m === "dark") document.documentElement.dataset.theme = m; } catch {}</script>
<link rel="stylesheet" href="${root}docs.css">
<script src="${root}docs.js" defer></script>
</head>
<body>
<div class="docs">
<header class="topbar">
  <button class="icon-button menu" type="button" aria-label="Show the pages" aria-expanded="false">${icon("panel-left")}</button>
  <a class="project" href="${href("index.md")}">Beamtime</a>
  <button class="search" type="button" aria-label="Search the documentation">${icon("search", 15)}<span class="search-label">Search the docs</span><kbd>⌘K</kbd></button>
  <div class="topbar-actions">
    <button class="icon-button mode" type="button" aria-label="Theme: system">${icon("monitor")}${icon("sun")}${icon("moon")}</button>
    <a class="github" href="${repo}">GitHub${icon("arrow-up-right", 14)}</a>
  </div>
</header>
<nav class="sidebar" aria-label="Documentation">${sections}</nav>
<main class="docs-main">
<article class="docs-page">
${html}
<nav class="docs-pager" aria-label="Pages">${pager}</nav>
</article>
${toc ? `<aside class="toc" aria-label="On this page"><h2>On this page</h2><ul>${toc}</ul></aside>` : ""}
</main>
</div>
<dialog class="sheet palette" aria-label="Search the documentation">
  <div class="palette-input">${icon("search", 18)}<input type="search" placeholder="Search the docs" aria-label="Search" autocomplete="off" spellcheck="false"></div>
  <ul class="palette-list" role="listbox"></ul>
  <div class="palette-foot"><span><kbd>↑</kbd><kbd>↓</kbd> to move</span><span>${icon("corner-down-left", 13)} to open</span><span><kbd>esc</kbd> to close</span></div>
</dialog>
</body>
</html>
`;
}
