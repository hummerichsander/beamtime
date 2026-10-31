# Sharing and figures

## Send a link

Every page has a URL. Anyone who can reach your Beamtime (and has its token) sees the same page.

## Save a page as a file

```sh
beamtime export scaling/lr-sweep --html lr-sweep-page/
```

writes a folder you can zip and send, or open from disk with a double click on `index.html`. It
needs no server and no Beamtime: the curves, tables and notes are stored in the folder. Charts
still zoom and show values on hover; the page is read-only.

Curves are stored with 1000 points each. For every logged point, add `--points all`.

Exporting needs Chrome, Chromium or Edge on the machine (or `playwright install chromium`).

## Figures for a paper

```sh
beamtime export scaling/lr-sweep --figures figs/                # one column wide
beamtime export scaling/lr-sweep --figures figs/ --size double  # two columns wide
```

Every chart of the page becomes three files: a PNG, a CSV with its data, and a PDF drawn with
matplotlib in your figure style (see [Settings](settings.md); the PDF needs `pip install
'beamtime[figures]'`).

In the browser, each chart's **Download** menu does the same for one chart.
