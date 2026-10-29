// What each state looks like: an icon, a color token and a word, so color is never alone.

export type Tone = "good" | "bad" | "warn" | "muted" | "accent" | "running" | "finished" | "failed" | "killed" | "lost";
export type SymbolSpec = { icon: string; tone: Tone; label: string; pulse?: boolean };
export type Kind = "run" | "result" | "verdict" | "note" | "research" | "thing";

const TABLE: Record<Kind, Record<string, SymbolSpec>> = {
  run: {
    running: { icon: "circle-dot", tone: "running", label: "running", pulse: true },
    finished: { icon: "check", tone: "finished", label: "finished" },
    failed: { icon: "circle-x", tone: "failed", label: "failed" },
    killed: { icon: "square", tone: "killed", label: "killed" },
    lost: { icon: "cloud-off", tone: "lost", label: "lost" },
  },
  result: {
    pass: { icon: "check", tone: "good", label: "pass" },
    fail: { icon: "x", tone: "bad", label: "fail" },
    inconclusive: { icon: "minus", tone: "warn", label: "inconclusive" },
    insufficient: { icon: "circle-dashed", tone: "muted", label: "insufficient" },
    pending: { icon: "hourglass", tone: "muted", label: "pending" },
    invalid: { icon: "triangle-alert", tone: "bad", label: "invalid" },
  },
  verdict: {
    confirmed: { icon: "circle-check", tone: "good", label: "confirmed" },
    refuted: { icon: "circle-x", tone: "bad", label: "refuted" },
    inconclusive: { icon: "circle-minus", tone: "warn", label: "inconclusive" },
  },
  note: {
    observation: { icon: "eye", tone: "accent", label: "observation" },
    decision: { icon: "signpost", tone: "accent", label: "decision" },
    idea: { icon: "lightbulb", tone: "accent", label: "idea" },
    question: { icon: "circle-help", tone: "accent", label: "question" },
    verdict: { icon: "scale", tone: "accent", label: "verdict" },
  },
  research: {
    open: { icon: "circle", tone: "muted", label: "open" },
    proposed: { icon: "target", tone: "accent", label: "proposed" },
    running: { icon: "circle-dot", tone: "running", label: "running", pulse: true },
    evaluable: { icon: "scale", tone: "warn", label: "evaluable" },
    concluded: { icon: "circle-check", tone: "good", label: "concluded" },
  },
  thing: {
    group: { icon: "folder-tree", tone: "muted", label: "group" },
    run: { icon: "activity", tone: "muted", label: "run" },
    proposal: { icon: "target", tone: "muted", label: "proposal" },
    memory: { icon: "bookmark", tone: "muted", label: "memory" },
    note: { icon: "file-text", tone: "muted", label: "note" },
    command: { icon: "chevron-right", tone: "muted", label: "command" },
  },
};

export function symbolFor(kind: Kind, value: string | null | undefined): SymbolSpec {
  // check results can carry " (provisional)"; the first word decides the symbol.
  const key = (value ?? "").split(" ")[0];
  return TABLE[kind][key] ?? { icon: "circle-dashed", tone: "muted", label: value ?? "unknown" };
}

// the icon of a run event in timelines.
export function eventIcon(type: string | null | undefined): string {
  switch (type) {
    case "finished":
      return "check";
    case "failed":
    case "crashed":
      return "circle-x";
    case "killed":
      return "square";
    case "attempt_started":
    case "created":
      return "play";
    default:
      return "circle";
  }
}
