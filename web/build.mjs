// Bundle the frontend into the Python package: src/beamtime/serve/static.

import { build } from "esbuild";
import { copyFile, mkdir, readdir, readFile, rm, writeFile } from "node:fs/promises";

const out = "../src/beamtime/serve/static";
await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });
// every build's inputs, to name the packages the bundle carries.
const inputs = new Set();
const keep = (result) => Object.keys(result.metafile.inputs).forEach((f) => inputs.add(f));
keep(await build({
  entryPoints: { app: "src/main.ts", kit: "src/kit/frame.ts" },
  bundle: true,
  metafile: true,
  splitting: true,
  format: "esm",
  minify: true,
  target: "es2022",
  outdir: out,
  entryNames: "[name]",
  chunkNames: "chunks/[name]-[hash]",
  assetNames: "fonts/[name]",
  loader: { ".woff2": "file" },
  legalComments: "none",
  logLevel: "warning",
  define: { __EXPORT__: "false" },
}));
// pages exported as static HTML open from disk, where browsers load no ES modules: the page and the
// custom-block kit as classic scripts, libraries included (beamtime export --html).
keep(await build({
  entryPoints: { main: "src/main.ts", kit: "src/kit/frame.ts" },
  bundle: true,
  metafile: true,
  format: "iife",
  minify: true,
  target: "es2022",
  outdir: `${out}/export`,
  // the same font files as the page's, one folder up.
  assetNames: "../fonts/[name]",
  loader: { ".woff2": "file" },
  legalComments: "none",
  logLevel: "warning",
  define: { __EXPORT__: "true" },
}));
// KaTeX's stylesheet, loaded by the Markdown renderer when a text has math; woff2 fonts only.
const woff2Only = {
  name: "woff2-only",
  setup(b) {
    b.onLoad({ filter: /katex\.min\.css$/ }, async (args) => ({
      contents: (await readFile(args.path, "utf8")).replace(/,url\([^)]*\.(woff|ttf)\) format\("(woff|truetype)"\)/g, ""),
      loader: "css",
    }));
  },
};
keep(await build({
  entryPoints: { katex: "node_modules/katex/dist/katex.min.css" },
  bundle: true,
  metafile: true,
  minify: true,
  outdir: out,
  assetNames: "fonts/[name]-[hash]",
  loader: { ".woff2": "file" },
  plugins: [woff2Only],
  logLevel: "warning",
}));
await copyFile("src/index.html", `${out}/index.html`);
await mkdir(`${out}/kit`, { recursive: true });
await copyFile("src/kit/frame.html", `${out}/kit/frame.html`);
await writeFile(`${out}/THIRD_PARTY_LICENSES.txt`, await licenses());
// the fonts' license texts ship next to the fonts, which esbuild copied from design/fonts.
for (const f of await readdir("../design/fonts")) {
  if (f.endsWith(".txt")) await copyFile(`../design/fonts/${f}`, `${out}/fonts/${f}`);
}
// serve resolves themes from the tokens, and a wheel holds only the package.
await copyFile("../design/tokens.json", `${out}/tokens.json`);

// the licenses of the packages bundled into the frontend, which ship with it (their notices are
// stripped from the minified files).
async function licenses() {
  const names = [...new Set([...inputs].map((f) => f.match(/node_modules\/((?:@[^/]+\/)?[^/]+)/)?.[1]).filter(Boolean))].sort();
  const parts = [
    "Beamtime's web interface bundles the following packages. Their licenses follow.\n",
  ];
  for (const name of names) {
    const dir = `node_modules/${name}`;
    const pkg = JSON.parse(await readFile(`${dir}/package.json`, "utf8"));
    const file = (await readdir(dir)).find((f) => /^(licen[cs]e|copying)(\.|$)/i.test(f));
    if (!file) throw new Error(`${name} has no license file to ship`);
    parts.push(`${"=".repeat(78)}\n${name} ${pkg.version} (${pkg.license})\n${"=".repeat(78)}\n\n${(await readFile(`${dir}/${file}`, "utf8")).trim()}\n`);
  }
  return parts.join("\n");
}
