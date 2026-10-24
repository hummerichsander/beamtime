"""Score agent answers for object-form and string-form `where` conditions.

Each answer is parsed the way a view would parse it (PyYAML, then the condition), normalized to a
canonical boolean tree, and compared with the reference. Usage: python score.py answers/*.md
"""

import re
import sys

import yaml

NUMERIC = {
    "config.lr", "config.optimizer.weight_decay", "config.batch_size", "config.warmup",
    "config.seed", "config.model.n_layers", "config.model.dropout", 'config["mixup.alpha"]',
    "run.steps", "run.duration_s",
}
NEGATE = {"eq": "ne", "ne": "eq", "lt": "ge", "ge": "lt", "le": "gt", "gt": "le",
          "has": "nhas", "nhas": "has", "exists": "nexists", "nexists": "exists",
          "glob": "nglob", "nglob": "glob"}


class ParseError(Exception):
    """An answer that cannot be parsed."""


def field(name: str) -> str:
    """Canonicalize a field name: strip whitespace and quote style.

    :param name: Field as written.
    :return: Canonical field name."""
    name = name.strip().replace("'", '"')
    return re.sub(r"\s+", "", name)


def cmp(f: str, op: str, v) -> tuple:
    """Build a comparison leaf.

    :param f: Field.
    :param op: Operator.
    :param v: Value.
    :return: Leaf tuple."""
    if isinstance(v, bool) or v is None:
        pass
    elif isinstance(v, (int, float)):
        v = float(v)
    return ("cmp", field(f), op, v)


def obj_condition(f: str, cond) -> list:
    """Translate one object-form field entry into leaves.

    :param f: Field.
    :param cond: Plain value or operator mapping.
    :return: List of nodes, all of which must hold."""
    if not isinstance(cond, dict):
        return [cmp(f, "eq", cond)]
    out = []
    for op, v in cond.items():
        match op:
            case "eq" | "ne" | "lt" | "le" | "gt" | "ge" | "has" | "glob":
                out.append(cmp(f, op, v))
            case "in":
                out.append(("or", [cmp(f, "eq", x) for x in v]))
            case "nin":
                out.append(("and", [cmp(f, "ne", x) for x in v]))
            case "exists":
                out.append(cmp(f, "exists" if v else "nexists", None))
            case _:
                raise ParseError(f"unknown operator {op}")
    return out


def obj_tree(m) -> tuple:
    """Translate an object-form mapping into a tree.

    :param m: The `where` mapping.
    :return: Tree."""
    if not isinstance(m, dict):
        raise ParseError(f"expected mapping, got {type(m).__name__}")
    parts = []
    for k, v in m.items():
        match k:
            case "any":
                parts.append(("or", [obj_tree(x) for x in v]))
            case "all":
                parts.append(("and", [obj_tree(x) for x in v]))
            case "not":
                parts.append(("not", obj_tree(v)))
            case _:
                parts.extend(obj_condition(k, v))
    return ("and", parts)


TOKEN = re.compile(r"""\s*(?:
    (?P<num>-?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?(?![\w./]))
  | (?P<str>'[^']*'|"[^"]*")
  | (?P<op>==|!=|<=|>=|<|>|~|\(|\)|\[|\]|,)
  | (?P<field>[A-Za-z_][\w./\-]*(?:\["[^"]*"\]|\['[^']*'\])?(?:\.[\w./\-]+)*(?:\[\d+:\d+\])?)
)""", re.VERBOSE)


def tokenize(s: str) -> list[tuple[str, str]]:
    """Split a condition string into tokens.

    :param s: Condition string.
    :return: List of (kind, text)."""
    out, pos = [], 0
    s = s.strip()
    while pos < len(s):
        if not (m := TOKEN.match(s, pos)) or m.end() == pos:
            raise ParseError(f"cannot tokenize at {s[pos:pos + 15]!r}")
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
        pos = m.end()
    return out


class StringParser:
    """Recursive-descent parser for the string form."""

    def __init__(self, *, text: str) -> None:
        self.toks = tokenize(text)
        self.i = 0

    def parse(self) -> tuple:
        """Parse the full condition.

        :return: Tree."""
        tree = self.or_()
        if self.i != len(self.toks):
            raise ParseError(f"trailing tokens {self.toks[self.i:]}")
        return tree

    def peek(self) -> str | None:
        """Look at the next token text.

        :return: Token text or None."""
        return self.toks[self.i][1] if self.i < len(self.toks) else None

    def take(self) -> tuple[str, str]:
        """Consume the next token.

        :return: The token."""
        if self.i >= len(self.toks):
            raise ParseError("unexpected end")
        self.i += 1
        return self.toks[self.i - 1]

    def or_(self) -> tuple:
        """Parse an or-expression.

        :return: Tree."""
        parts = [self.and_()]
        while self.peek() == "or":
            self.take()
            parts.append(self.and_())
        return ("or", parts)

    def and_(self) -> tuple:
        """Parse an and-expression.

        :return: Tree."""
        parts = [self.not_()]
        while self.peek() == "and":
            self.take()
            parts.append(self.not_())
        return ("and", parts)

    def not_(self) -> tuple:
        """Parse a negation.

        :return: Tree."""
        if self.peek() == "not":
            self.take()
            return ("not", self.not_())
        return self.atom()

    def value(self):
        """Parse a value.

        :return: Python value."""
        kind, text = self.take()
        match kind:
            case "num":
                return float(text)
            case "str":
                return text[1:-1]
            case "field":
                return text
            case "op" if text == "[":
                items = []
                while self.peek() != "]":
                    items.append(self.value())
                    if self.peek() == ",":
                        self.take()
                self.take()
                return items
            case _:
                raise ParseError(f"unexpected value {text}")

    def atom(self) -> tuple:
        """Parse a parenthesized expression or a comparison.

        :return: Tree."""
        if self.peek() == "(":
            self.take()
            tree = self.or_()
            if self.take()[1] != ")":
                raise ParseError("missing )")
            return tree
        kind, f = self.take()
        if kind != "field":
            raise ParseError(f"expected field, got {f}")
        op = self.take()[1]
        ops = {"==": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge", "~": "glob",
               "has": "has"}
        if op in ops:
            return cmp(f, ops[op], self.value())
        if op == "exists":
            return cmp(f, "exists", None)
        if op == "in":
            return ("or", [cmp(f, "eq", x) for x in self.value()])
        if op == "not":
            nxt = self.take()[1]
            if nxt == "in":
                return ("and", [cmp(f, "ne", x) for x in self.value()])
            if nxt == "exists":
                return cmp(f, "nexists", None)
        raise ParseError(f"unknown operator {op}")


def nnf(t: tuple, neg: bool = False) -> tuple:
    """Push negations down to the leaves.

    :param t: Tree.
    :param neg: Whether the subtree is negated.
    :return: Tree without `not` nodes."""
    match t[0]:
        case "not":
            return nnf(t[1], not neg)
        case "and" | "or":
            kind = t[0] if not neg else {"and": "or", "or": "and"}[t[0]]
            return (kind, [nnf(c, neg) for c in t[1]])
        case "cmp":
            return ("cmp", t[1], NEGATE[t[2]] if neg else t[2], t[3])
    raise ValueError(t)


def canon(t: tuple):
    """Flatten, deduplicate and sort a tree in negation normal form.

    :param t: Tree.
    :return: Hashable canonical form."""
    if t[0] == "cmp":
        return t
    kids = []
    for c in (canon(c) for c in t[1]):
        if isinstance(c, tuple) and c[0] == t[0]:
            kids.extend(c[1])
        else:
            kids.append(c)
    kids = sorted(set(kids), key=repr)
    if len(kids) == 1:
        return kids[0]
    return (t[0], tuple(kids))


def coerce(t, numeric_only: bool):
    """Convert numeric strings on numeric fields to numbers (the fix for YAML's `1e-3` trap).

    :param t: Canonical tree.
    :param numeric_only: Unused marker to keep the signature explicit.
    :return: Tree with coerced values."""
    if t[0] == "cmp":
        _, f, op, v = t
        if f in NUMERIC and isinstance(v, str):
            try:
                return ("cmp", f, op, float(v))
            except ValueError:
                return t
        return t
    return (t[0], tuple(coerce(c, numeric_only) for c in t[1]))


def g(s: str) -> object:
    """Build a reference tree from a string-form condition.

    :param s: Condition string.
    :return: Canonical tree."""
    return canon(nnf(StringParser(text=s).parse()))


GOLD = {
    "t01": "run.status == finished",
    "t02": "config.lr < 1e-3",
    "t03": "config.lr >= 1e-4 and config.lr <= 1e-3",
    "t04": "config.warmup in [500, 1000]",
    "t05": "run.tags has baseline",
    "t06": "not run.tags has baseline",
    "t07": "run.status == finished and metric.val/acc.max >= 0.92",
    "t08": "run.status in [failed, killed]",
    "t09": "config.optimizer.name == adam and config.lr in [3e-4, 1e-3]",
    "t10": "run.name ~ 'boosted*'",
    "t11": "metric.train/loss.nonfinite > 0",
    "t12": "metric.val/loss.mean[1000:2000] < 0.5",
    "t13": "config.optimizer.weight_decay exists",
    "t14": "proposal.check == fail and proposal.verdict == confirmed",
    "t15": "config.model.n_layers in [12, 24, 48] and config.model.dropout != 0",
    "t16": "config.batch_size >= 256 and config.lr <= 2e-3 and run.status != failed",
    "t17": "config.seed == 0 and (metric.train/loss.ema_last < 1.5 or metric.val/acc.max > 0.9)",
    "t18": """config["mixup.alpha"] > 0.2""",
    "t19": "config.scheduler == 'cosine with restarts'",
    "t20": "not (run.status == lost or (run.status == running and run.steps < 1000))",
}
# t11 also accepts >= 1.
ALTERNATIVES = {"t11": ["metric.train/loss.nonfinite >= 1"]}


def parse_answer(form: str, block: str):
    """Parse one fenced YAML block as a view would.

    :param form: "object" or "string".
    :param block: YAML text containing `where:`.
    :return: Canonical tree."""
    try:
        doc = yaml.safe_load(block)
    except yaml.YAMLError as e:
        raise ParseError(f"YAML: {str(e).splitlines()[0]}") from e
    if not isinstance(doc, dict) or "where" not in doc:
        raise ParseError("no `where` key")
    w = doc["where"]
    match form:
        case "object":
            return canon(nnf(obj_tree(w)))
        case "string":
            if not isinstance(w, str):
                raise ParseError(f"where is a {type(w).__name__}, not a string")
            return canon(nnf(StringParser(text=w).parse()))
        case _:
            raise ValueError(form)


def answers(path: str) -> dict[str, str]:
    """Read answer blocks from a Markdown file.

    :param path: Answer file.
    :return: Mapping from task id to YAML block."""
    text = open(path).read()
    out = {}
    for m in re.finditer(r"###\s*(t\d\d)\s*\n+```(?:yaml)?\n(.*?)```", text, re.S):
        out[m.group(1)] = m.group(2)
    return out


def main() -> None:
    """Score every answer file given on the command line."""
    gold = {k: g(v) for k, v in GOLD.items()}
    alts = {k: [g(v) for v in vs] for k, vs in ALTERNATIVES.items()}
    for path in sys.argv[1:]:
        form = "object" if "object" in path else "string"
        ans = answers(path)
        strict = coerced = 0
        fails = []
        for tid, ref in gold.items():
            ok = [ref, *alts.get(tid, [])]
            if tid not in ans:
                fails.append(f"{tid}: missing")
                continue
            try:
                got = parse_answer(form, ans[tid])
            except Exception as e:
                fails.append(f"{tid}: parse error: {e}")
                continue
            if got in ok:
                strict += 1
                coerced += 1
            elif coerce(got, True) in [coerce(o, True) for o in ok]:
                coerced += 1
                fails.append(f"{tid}: correct only after numeric coercion")
            else:
                fails.append(f"{tid}: wrong meaning: {got}")
        print(f"{path}: strict {strict}/20, with coercion {coerced}/20")
        for f in fails:
            print(f"    {f}")


if __name__ == "__main__":
    main()
