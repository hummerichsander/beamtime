// The renderer's layout checks, run in the settled page; what a screenshot can't be trusted to show.
() => {
  const out = [];
  const leaves = [...document.querySelectorAll(".node[data-block-id]")].filter((n) => !n.querySelector(".node"));
  const add = (level, n, message) => out.push({level, id: n.dataset.blockId, block: n.dataset.block, message});
  for (const n of leaves) {
    const r = n.getBoundingClientRect();
    const drawn = [...n.querySelectorAll("canvas, img, svg")].some((e) => e.getBoundingClientRect().width > 4);
    if (!n.innerText.trim() && !drawn) add("error", n, "the block is blank");
    const notice = n.querySelector(".notice");
    if (notice && !["note", "custom"].includes(n.dataset.block) && !drawn && !n.querySelector("table"))
      add("warning", n, `shows only a notice: ${notice.innerText.trim().slice(0, 160)}`);
    // charts reach 8px past their node for the hover tint; more is overflow.
    if (n.scrollWidth > n.clientWidth + 12) add("warning", n, "content overflows the block's width");
    for (const w of n.querySelectorAll(".table-wrap"))
      if (w.scrollWidth > w.clientWidth + 2) add("warning", n, "the table is wider than its column; fewer columns");
    let clipped = 0;
    for (const e of n.querySelectorAll("*")) {
      if (!e.childElementCount && e.textContent.trim() && getComputedStyle(e).textOverflow === "ellipsis"
          && e.scrollWidth > e.clientWidth + 1) clipped++;
    }
    if (clipped) add("warning", n, `${clipped} clipped label(s)`);
    const curves = Number(n.querySelector("[data-curves]")?.dataset.curves ?? 0);
    if (curves > 8) add("warning", n, `${curves} curves in one chart; use color, by or seeds`);
    if (r.height < 8) add("warning", n, "the block has no height");
  }
  for (let i = 0; i < leaves.length; i++) {
    for (let j = i + 1; j < leaves.length; j++) {
      const a = leaves[i].getBoundingClientRect();
      const b = leaves[j].getBoundingClientRect();
      const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (w > 2 && h > 2) add("warning", leaves[i], `overlaps ${leaves[j].dataset.blockId}`);
    }
  }
  return out;
}
