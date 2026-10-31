// Build the documentation site: docs/**/*.md (the pages docs/nav.json lists) into ../site, in
// Beamtime's look, light and dark. Links between pages are checked; a broken one fails the build.

import { readFile, writeFile, mkdir, rm, copyFile } from "node:fs/promises";
import { dirname, join, normalize, relative } from "node:path";
import { Marked } from "marked";

import { cssVariables } from "./src/bt/theme.ts";

const docs = "../docs";
const out = "../site";
const nav = JSON.parse(await readFile(join(docs, "nav.json"), "utf8"));
const pages = nav.sections.flatMap((s) => s.pages);
const titles = Object.fromEntries(
  await Promise.all(pages.map(async (p) => [p, (await readFile(join(docs, p), "utf8")).match(/^# (.+)$/m)?.[1] ?? p])),
);
const broken = [];

await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });
await writeFile(join(out, "docs.css"), (await themeCss()) + (await readFile("docs/docs.css", "utf8")));
await writeFile(join(out, ".nojekyll"), "");
for (const [i, page] of pages.entries()) {
  const html = render(page, await readFile(join(docs, page), "utf8"));
  const file = join(out, page.replace(/\.md$/, ".html"));
  await mkdir(dirname(file), { recursive: true });
  await writeFile(file, layout(page, html, pages[i - 1], pages[i + 1]));
}
if (broken.length) {
  console.error(`broken links:\n  ${broken.join("\n  ")}`);
  process.exit(1);
}
console.log(`wrote ${pages.length} pages to site/`);

// the light theme's tokens, and the dark theme's for dark systems.
async function themeCss() {
  const read = async (name) => JSON.parse(await readFile(`../src/beamtime/views/themes/${name}.json`, "utf8"));
  // a theme that extends another takes the other's values where it sets none.
  const theme = async (name) => {
    const t = await read(name);
    if (!t.extends) return t;
    const base = await theme(t.extends);
    return Object.fromEntries(Object.keys({ ...base, ...t }).map((k) => [k, typeof base[k] === "object" && !Array.isArray(base[k]) ? { ...base[k], ...t[k] } : t[k] ?? base[k]]));
  };
  const vars = (t) => Object.entries(cssVariables(t)).map(([k, v]) => `${k}: ${v};`).join(" ");
  return `:root { ${vars(await theme("beamtime-light"))} }\n@media (prefers-color-scheme: dark) { :root { ${vars(await theme("beamtime-dark"))} } }\n`;
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
        return `<a href="${target(page, href)}"${title ? ` title="${title}"` : ""}>${inner}</a>`;
      },
    },
  });
  return marked.parse(text);
}

// a link to another page becomes its .html; one to a page that isn't part of the site is broken.
function target(page, href) {
  if (/^[a-z]+:|^#/.test(href)) return href;
  const [file, hash] = href.split("#");
  const to = normalize(join(dirname(page), file)).replace(/\\/g, "/");
  if (!pages.includes(to)) broken.push(`${page}: ${href}`);
  return file.replace(/\.md$/, ".html") + (hash ? `#${hash}` : "");
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
      .map((p) => `<li><a href="${href(p)}"${p === page ? ' aria-current="page"' : ""}>${titles[p]}</a></li>`)
      .join("")}</ul>`)
    .join("");
  const pager = [
    prev ? `<a class="prev" href="${href(prev)}"><span>Previous</span>${titles[prev]}</a>` : "",
    next ? `<a class="next" href="${href(next)}"><span>Next</span>${titles[next]}</a>` : "",
  ].join("");
  const title = page === "index.md" ? "Beamtime" : `${titles[page]} · Beamtime`;
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
<link rel="stylesheet" href="${root}docs.css">
</head>
<body>
<div class="docs">
<nav class="docs-nav" aria-label="Documentation"><a class="docs-brand" href="${href("index.md")}">Beamtime</a>${sections}</nav>
<main class="docs-page">
${html}
<nav class="docs-pager" aria-label="Pages">${pager}</nav>
</main>
</div>
</body>
</html>
`;
}
