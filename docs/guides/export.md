# Sharing and figures

## Send a link

Every page has a URL; anyone who can reach your Beamtime and has its token sees the same page.

## Save a page as a file

```sh
beamtime export scaling/lr-sweep --html lr-sweep-page/
```

The folder opens from disk (`index.html`) without a server or Beamtime; zip it and send it. Charts
still zoom and show values on hover; the page is read-only. Curves keep 1000 points each
(`--points all` keeps every point). Exporting needs Chrome, Chromium or Edge (or
`playwright install chromium`).

## Figures for a paper

```sh
beamtime export scaling/lr-sweep --figures figs/                # one column wide
beamtime export scaling/lr-sweep --figures figs/ --size double  # two columns wide
```

Each chart becomes a PNG, a CSV of its data and a matplotlib PDF in your
[figure style](settings.md#figure-style) (the PDF needs `pip install 'beamtime[figures]'`). Each
chart's **Download** menu does the same in the browser.
