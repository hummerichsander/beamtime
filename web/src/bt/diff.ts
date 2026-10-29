// A line diff of two texts (view versions' YAML): the longest common subsequence, small and exact.

export type DiffLine = { kind: "same" | "added" | "removed"; text: string };

export function diffLines(a: string, b: string): DiffLine[] {
  const x = a.split("\n");
  const y = b.split("\n");
  const n = x.length;
  const m = y.length;
  // lcs[i][j]: the common length of x[i:] and y[j:].
  const lcs = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      lcs[i][j] = x[i] === y[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1]);
    }
  }
  const out: DiffLine[] = [];
  let i = 0;
  let j = 0;
  while (i < n && j < m) {
    if (x[i] === y[j]) {
      out.push({ kind: "same", text: x[i] });
      i++;
      j++;
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      out.push({ kind: "removed", text: x[i++] });
    } else {
      out.push({ kind: "added", text: y[j++] });
    }
  }
  while (i < n) out.push({ kind: "removed", text: x[i++] });
  while (j < m) out.push({ kind: "added", text: y[j++] });
  return out;
}

// unchanged runs longer than 2 * context lines fold into one "n unchanged lines" marker.
export function fold(lines: DiffLine[], context = 3): (DiffLine | { kind: "skip"; count: number })[] {
  const out: (DiffLine | { kind: "skip"; count: number })[] = [];
  let i = 0;
  while (i < lines.length) {
    if (lines[i].kind !== "same") {
      out.push(lines[i++]);
      continue;
    }
    let j = i;
    while (j < lines.length && lines[j].kind === "same") j++;
    const head = i === 0 ? 0 : context;
    const tail = j === lines.length ? 0 : context;
    if (j - i > head + tail + 1) {
      out.push(...lines.slice(i, i + head), { kind: "skip", count: j - i - head - tail }, ...lines.slice(j - tail, j));
    } else {
      out.push(...lines.slice(i, j));
    }
    i = j;
  }
  return out;
}
