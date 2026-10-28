"""Proposals: their fields, validation, versions, membership and freezing."""

import time
from pathlib import Path
from typing import Any, Literal

import msgspec

from beamtime.format import constants as c
from beamtime.format.authored import file_hash, newest, versions
from beamtime.index.index import Index
from beamtime.query import models as m
from beamtime.query.fields import json_path, parse_field
from beamtime.query.kinds import Context, select_runs
from beamtime.query.models import QueryError, closest
from beamtime.query.where import fields_of

Op = Literal["<", "<=", ">", ">="]
TESTS_LATER = ("trend", "best")


class RecordError(ValueError):
    """A proposal, note or memory that can't be written as given; says how to fix it."""


class Struct(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Base of the record structs: unknown fields are errors."""


class Reduce(Struct, kw_only=True):
    """How a prediction reduces a run to one number."""

    metric: str
    stat: Literal["first", "last", "min", "max", "mean"] = "last"
    steps: list[int | None] | None = None

    @property
    def field(self) -> str:
        """The query field of the reduction, e.g. ``metric.val/acc.max[100:300]``."""
        if self.steps is None:
            return f"metric.{self.metric}.{self.stat}"
        a, b = ("" if s is None else s for s in self.steps)
        return f"metric.{self.metric}.{self.stat}[{a}:{b}]"


class Prediction(Struct, kw_only=True):
    """A named claim of a proposal."""

    name: str
    kind: Literal["auto", "manual"] = "auto"
    description: str | None = None
    where: dict[str, Any] = msgspec.field(default_factory=dict)
    reduce: Reduce | None = None
    seeds: str | None = None
    test: Literal["each", "compare", "trend", "best"] = "each"
    op: Op | None = None
    value: float | None = None
    ref: dict[str, str] | None = None
    margin: float = 0.0
    a: dict[str, Any] | None = None
    b: dict[str, Any] | None = None
    pair_by: list[str] | None = None


class Supersedes(Struct, kw_only=True):
    """Which version a new one replaces, and why."""

    version: str
    reason: str


class Proposal(Struct, kw_only=True):
    """One proposal version."""

    schema: int = 1
    statement: str | None = None
    rationale: str | None = None
    confidence: float | None = None
    plan: dict[str, Any] | Literal["children"] | None = None
    predictions: list[Prediction] = msgspec.field(default_factory=list)
    supersedes: Supersedes | None = None
    significance: float | Literal["none"] | None = None
    author: str | None = None
    user: str | None = None

    @property
    def level(self) -> float | None:
        """The confidence level of intervals; ``None`` for ``significance: none``."""
        match self.significance:
            case None:
                return 0.95
            case "none":
                return None
            case float() | int():
                return float(self.significance)
            case _:
                raise ValueError(f"unknown significance {self.significance!r}")

    @property
    def blank(self) -> bool:
        """Whether it says nothing, like the proposal of a run started without one."""
        return not self.statement and not self.predictions and self.plan is None


def parse(data: Any, *, source: str) -> Proposal:
    """Read proposal fields and check that they make sense.

    :param data: The parsed YAML.
    :param source: Where it came from, for messages.
    :return: The proposal."""
    if not isinstance(data, dict):
        raise RecordError(f"{source}: a proposal is a mapping with statement, plan, predictions")
    try:
        proposal = msgspec.convert(data, type=Proposal, strict=False)
    except msgspec.ValidationError as e:
        raise RecordError(f"{source}: {explain(str(e))}") from None
    if problems := check_fields(proposal):
        raise RecordError(f"{source}: " + "; ".join(problems))
    return proposal


def explain(message: str) -> str:
    """Turn a msgspec message into advice with the allowed fields.

    :param message: msgspec's message.
    :return: The advice."""
    names = {
        "proposal": [f.encode_name for f in msgspec.structs.fields(Proposal)],
        "prediction": [f.encode_name for f in msgspec.structs.fields(Prediction)],
    }
    if "unknown field" in message:
        word = message.split("`")[1]
        kind = "prediction" if "predictions[" in message else "proposal"
        return (
            f"unknown {kind} field {word!r}.{closest(word, names[kind])} "
            f"Fields: {', '.join(names[kind])}."
        )
    return message.replace("`$.", "`")


def check_fields(p: Proposal) -> list[str]:
    """Find the problems msgspec can't see: missing test fields, bad field names.

    :param p: The proposal.
    :return: One message per problem."""
    problems = []
    if p.confidence is not None and not 0 <= p.confidence <= 1:
        problems.append("confidence is a probability between 0 and 1")
    if isinstance(p.significance, (int, float)) and not 0.5 <= p.significance < 1:
        problems.append("significance is a level like 0.95 or 0.99, or none")
    match p.plan:
        case None | "children":
            pass
        case {"runs": int(n)} if len(p.plan) == 1 and n > 0:
            pass
        case {"grid": dict(grid)} if len(p.plan) == 1 and grid:
            for key, values in grid.items():
                problems += field_problems([key], "plan.grid")
                if not isinstance(values, list) or not values:
                    problems.append(f"plan.grid.{key}: list the values, e.g. [0, 1, 2]")
        case _:
            problems.append("plan is {runs: N}, {grid: {field: [values]}} or children")
    names = [pr.name for pr in p.predictions]
    if dupes := sorted({n for n in names if names.count(n) > 1}):
        problems.append(f"prediction names must be unique: {', '.join(dupes)}")
    for pr in p.predictions:
        problems += [f"prediction {pr.name!r}: {x}" for x in prediction_problems(pr)]
    return problems


def prediction_problems(pr: Prediction) -> list[str]:
    """Check that a prediction has what its test needs.

    :param pr: The prediction.
    :return: One message per problem."""
    if pr.kind == "manual":
        return [] if pr.description else ["a manual prediction needs a description"]
    problems = []
    if pr.test in TESTS_LATER:
        return [f"test {pr.test!r} comes in v1.1; use each or compare"]
    if pr.reduce is None:
        problems.append("reduce: {metric: <key>, stat: last|first|min|max|mean} is required")
    elif pr.reduce.steps is not None and len(pr.reduce.steps) != 2:
        problems.append("reduce.steps is [first, last]")
    if pr.op is None:
        problems.append("op is one of <, <=, >, >=")
    match pr.test:
        case "each":
            if (pr.value is None) == (pr.ref is None):
                problems.append("each needs value or ref: {run: <id>}, not both")
            if pr.ref is not None and set(pr.ref) != {"run"}:
                problems.append("ref is {run: <id>}")
            if pr.a is not None or pr.b is not None or pr.pair_by:
                problems.append("a, b and pair_by belong to test: compare")
        case "compare":
            if pr.a is None or pr.b is None:
                problems.append("compare needs a and b, conditions like {config.warmup: 500}")
            if pr.value is not None or pr.ref is not None:
                problems.append("compare uses margin, not value or ref")
        case _:
            raise ValueError(f"unknown test {pr.test!r}")
    if pr.margin < 0:
        problems.append("margin is not negative; the op gives the direction")
    texts = [*fields_of(pr.where), *fields_of(pr.a or {}), *fields_of(pr.b or {})]
    problems += field_problems([*texts, *(pr.pair_by or [])], "where")
    if pr.seeds is not None:
        try:
            seed = parse_field(pr.seeds)
            if seed.ns != "config" or len(seed.path) != 1:
                problems.append(f"seeds: {pr.seeds!r} must be a top-level config field")
        except QueryError as e:
            problems.append(f"seeds: {e}")
    return problems


def field_problems(texts: list[str], where: str) -> list[str]:
    """Check that fields parse.

    :param texts: The field texts.
    :param where: Where they are used, for messages.
    :return: One message per bad field."""
    out = []
    for text in texts:
        try:
            parse_field(text)
        except QueryError as e:
            out.append(f"{where}: {e}")
    return out


def load(folder_dir: Path, version: str) -> Proposal:
    """Read one proposal version.

    :param folder_dir: The group or run directory.
    :param version: The version id.
    :return: The proposal."""
    import yaml

    path = folder_dir / c.PROPOSAL / f"{version}.yaml"
    try:
        data = yaml.safe_load(path.read_text())
    except FileNotFoundError:
        raise RecordError(f"no proposal version {version} in {folder_dir.name}/proposal") from None
    except yaml.YAMLError as e:
        raise RecordError(f"{path.name}: not valid YAML: {e}") from None
    return parse(data, source=path.name)


def current(folder_dir: Path) -> str | None:
    """Find the current proposal version of a group.

    :param folder_dir: The group or run directory.
    :return: The newest version id, or ``None``."""
    return path.stem if (path := newest(folder_dir / c.PROPOSAL)) is not None else None


def all_versions(folder_dir: Path) -> list[str]:
    """List a group's proposal versions.

    :param folder_dir: The group or run directory.
    :return: The version ids, oldest first."""
    return [p.stem for p in versions(folder_dir / c.PROPOSAL)]


class Target:
    """A group or run whose proposal is looked at."""

    def __init__(self, *, index: Index, rel: str, run_id: str | None) -> None:
        """Name the target.

        :param index: The open index.
        :param rel: The group or run path relative to the log dir.
        :param run_id: The run id if the target is a run."""
        self.index = index
        self.rel = rel
        self.run_id = run_id

    @property
    def dir(self) -> Path:
        """The directory."""
        return self.index.folder_path(self.rel)

    @property
    def key(self) -> str:
        """The key runs record this target's proposal under in ``_run.json``."""
        return "." if self.run_id is not None else self.rel

    def membership(self, version: str) -> tuple[str, list[Any]]:
        """Build the SQL condition selecting the runs that recorded a version.

        :param version: The version id.
        :return: The condition and its parameters."""
        cond = f"json_extract(runs.info, '{json_path(('proposals', self.key))}') = ?"
        if self.run_id is not None:
            return f"runs.id = ? AND {cond}", [self.run_id, version]
        return cond, [version]

    def members(self, version: str) -> list[dict[str, Any]]:
        """List the runs that recorded a version.

        :param version: The version id.
        :return: Per run: id, path, status (``lost`` derived) and recorded hash."""
        from beamtime.query.kinds import derived_status

        cond, params = self.membership(version)
        now = time.time()
        recorded = json_path(("proposal_hashes", self.key))
        rows = self.index.store.db.execute(
            f"SELECT id, path, status, heartbeat, json_extract(info, '{recorded}') "
            f"FROM runs WHERE {cond}",
            params,
        )
        return [
            {"id": r[0], "path": r[1], "status": derived_status(r[2], r[3], now), "hash": r[4]}
            for r in rows
        ]

    def select(
        self,
        version: str,
        where: dict[str, Any],
        fields: list[str],
        *,
        seeds: str | None = None,
    ) -> list[dict[str, Any]]:
        """Select the members of a version that match a condition, with field values.

        :param version: The version id.
        :param where: The condition, in the query syntax.
        :param fields: Fields to fetch.
        :param seeds: The seed field, when seed groups are formed later.
        :return: One dict per run, as ``query.kinds.select_runs`` gives them."""
        ctx = Context(index=self.index, caller="cli", scope=".", run_id=None, now=time.time())
        sel = m.Selection(where=where, seeds=seeds)
        runs, _ = select_runs(ctx, sel, fields, config=True, restrict=self.membership(version))
        return runs

    def hash_problem(self, version: str, members: list[dict[str, Any]]) -> str | None:
        """Compare a frozen version's file with the hash its runs recorded.

        :param version: The version id.
        :param members: Its runs, from ``members``.
        :return: A message if the file was edited or removed, else ``None``."""
        recorded = {r["hash"] for r in members if r["hash"]}
        if not recorded:
            return None
        path = self.dir / c.PROPOSAL / f"{version}.yaml"
        if not path.exists():
            return f"proposal {version} is gone, but {len(members)} run(s) recorded it"
        if (now := file_hash(path)) not in recorded:
            return (
                f"proposal {version} was edited after runs recorded it (hash {now}, recorded "
                f"{', '.join(sorted(recorded))}); restore it, or save a new version that "
                "supersedes it"
            )
        return None
