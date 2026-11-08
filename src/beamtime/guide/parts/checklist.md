# Screenshot checklist

Answer yes or no for every block in the render, then fix what fails:

1. Is every label, tick and legend entry fully visible?
2. Can the runs or groups in each chart be told apart?
3. Does each title or caption match what the block shows?
4. Is any block empty or showing only a notice where data was expected?
5. Do axes use sensible scales (log for quantities spanning orders of magnitude)?
6. Does the first screen show the finding and the evidence for it?
7. Is anything decorative that carries no information?
8. Does every chart label its axes, and does each caption say what the chart shows rather than repeat the axes?
9. Does every top-level section have a one- or two-word title for the left column?
10. Do status, results and colours use the app's own marks (`bt.ui.Sym`, `bt.theme.tone`), not hex, emoji or typed-in results?

The render also reports what it measured: console errors, blank blocks, overflowing or clipped
content, overlapping blocks, and charts with more than eight curves.
