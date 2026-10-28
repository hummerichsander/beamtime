// Markdown for notes and memory, loaded on first use: GitHub-flavoured Markdown with raw HTML shown
// as text, [[links]] to runs and groups, and KaTeX for $…$ and $$…$$ (loaded only when needed).

import { Marked, type TokenizerAndRendererExtension, type Tokens } from "marked";

const RUN_ID = /^\d{8}-\d{6}-[0-9a-z]{8}$/;
const SAFE_URL = /^(https?:|mailto:|\/(?!\/)|#)/i;

type Katex = { renderToString: (tex: string, opts: Record<string, unknown>) => string };

export function linkFor(target: string): string {
  const [path, rest] = target.split(/(?=[#@])/);
  const last = path.split("/").pop() ?? "";
  if (RUN_ID.test(last)) return `/r/${last}`;
  const base = `/f/local${path === "." ? "" : `/${path.split("/").map(encodeURIComponent).join("/")}`}`;
  if (rest?.startsWith("@")) return `${base}?v=${encodeURIComponent(rest.slice(1))}`;
  return base;
}

export function escape(text: string): string {
  return text.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

const wikilink: TokenizerAndRendererExtension = {
  name: "wikilink",
  level: "inline",
  start: (src) => src.indexOf("[["),
  tokenizer(src) {
    const m = /^\[\[([^\]\n]+)\]\]/.exec(src);
    return m ? { type: "wikilink", raw: m[0], target: m[1].trim() } : undefined;
  },
  renderer: (token) => `<a class="wikilink" href="${escape(linkFor(token.target))}">${escape(token.target)}</a>`,
};

function math(katex: Katex): TokenizerAndRendererExtension[] {
  const render = (tex: string, display: boolean) =>
    katex.renderToString(tex, { displayMode: display, throwOnError: false, output: "htmlAndMathml" });
  return [
    {
      name: "mathBlock",
      level: "block",
      start: (src) => src.indexOf("$$"),
      tokenizer(src) {
        const m = /^\$\$([\s\S]+?)\$\$(?:\n|$)/.exec(src);
        return m ? { type: "mathBlock", raw: m[0], tex: m[1].trim() } : undefined;
      },
      renderer: (token) => `<div class="math">${render(token.tex, true)}</div>`,
    },
    {
      name: "mathInline",
      level: "inline",
      start: (src) => src.indexOf("$"),
      tokenizer(src) {
        // $ must hug its content and not precede a digit, so prices like $5 stay text.
        const m = /^\$(?=\S)((?:\\\$|[^$\n])*?\S)\$(?!\d)/.exec(src);
        return m ? { type: "mathInline", raw: m[0], tex: m[1] } : undefined;
      },
      renderer: (token) => render(token.tex, false),
    },
  ];
}

export function hasMath(text: string): boolean {
  return /\$\$[\s\S]+?\$\$|\$(?=\S)[^$\n]*?\S\$(?!\d)/.test(text);
}

export function markdown(text: string, katex: Katex | null = null): string {
  const md = new Marked({ gfm: true, breaks: false });
  md.use({
    extensions: [wikilink, ...(katex ? math(katex) : [])],
    renderer: {
      html: ({ text: raw }: Tokens.HTML | Tokens.Tag) => escape(raw),
      link({ href, title, tokens }: Tokens.Link) {
        const inner = this.parser.parseInline(tokens);
        if (!SAFE_URL.test(href)) return inner;
        const external = /^https?:/i.test(href);
        return `<a href="${escape(href)}"${title ? ` title="${escape(title)}"` : ""}${
          external ? ' target="_blank" rel="noopener noreferrer"' : ""
        }>${inner}</a>`;
      },
      image: ({ text: alt }: Tokens.Image) => escape(alt),
    },
  });
  return md.parse(text, { async: false }) as string;
}

let katexStyle = false;

export async function render(text: string): Promise<string> {
  if (!hasMath(text)) return markdown(text);
  const katex = (await import("katex")).default as Katex;
  if (!katexStyle) {
    katexStyle = true;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/static/katex.css";
    document.head.append(link);
  }
  return markdown(text, katex);
}
