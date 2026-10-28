"""The operation set: one entry per operation, shared by the CLI, MCP and the API.

This module is imported on every CLI call, so it holds only names, parameter structs and
summaries; implementations are imported when an operation runs."""

from dataclasses import dataclass
from importlib import import_module
from typing import Annotated, Any, Literal

import msgspec

Where = Annotated[
    dict[str, Any],
    msgspec.Meta(
        description="field -> value or {op: value}; ops eq ne lt le gt ge in nin has "
        "exists glob; also any: [...], not: {...}. Fields: run.status, config.lr, "
        "metric.val/acc.max, metric.train/loss.mean[0:1000], value.test/acc"
    ),
]
Fields = Annotated[
    list[str] | None,
    msgspec.Meta(description="fields such as run.name, config.lr, metric.val/acc.max"),
]


class Params(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Base of the parameter structs."""


class NoParams(Params, kw_only=True):
    """An operation without parameters."""


class Page(Params, kw_only=True):
    """Paging for answers cut at the token budget."""

    cursor: str | None = None


class Selection(Page, kw_only=True):
    """Which runs an operation looks at."""

    from_: Annotated[str, msgspec.Meta(description="folder below the log dir, or a run id")] = (
        msgspec.field(default=".", name="from")
    )
    where: Where = msgspec.field(default_factory=dict)
    depth: Literal["all"] | int = "all"


class KeysParams(Selection, kw_only=True):
    """Parameters of ``keys``."""


class FoldersParams(Selection, kw_only=True):
    """Parameters of ``folders``."""


class RunsParams(Selection, kw_only=True):
    """Parameters of ``runs``."""

    select: Fields = None
    sort: Annotated[list[str], msgspec.Meta(description="fields; a leading - sorts descending")] = (
        msgspec.field(default_factory=list)
    )
    limit: int | None = None
    seeds: Annotated[
        str | None, msgspec.Meta(description="e.g. config.seed: average over seeds")
    ] = None


class CardParams(Params, kw_only=True):
    """Parameters of ``card``."""

    run: str


class SeriesParams(Selection, kw_only=True):
    """Parameters of ``series``."""

    y: Annotated[list[str], msgspec.Meta(description="metric keys, e.g. train/loss")]
    x: Annotated[str, msgspec.Meta(description="_step, _t, _elapsed or a metric key")] = "_step"
    steps: Annotated[
        list[int | None] | None, msgspec.Meta(description="[first, last] step window")
    ] = None
    points: int | None = None
    group: list[str] | None = None
    seeds: str | None = None
    smooth: float | None = None
    band: Literal["minmax", "std", "stderr", "none"] = "minmax"


class DataParams(Selection, kw_only=True):
    """Parameters of ``data``."""

    key: str
    step: Literal["last", "all"] | int | list[int] = "last"
    limit: int | None = None


class FileParams(Params, kw_only=True):
    """Parameters of ``file``."""

    view: str
    path: str


class OutputParams(Params, kw_only=True):
    """Parameters of ``output``."""

    run: str
    tail: int | None = 50
    grep: str | None = None
    rank: int = 0


class TimelineParams(Selection, kw_only=True):
    """Parameters of ``timeline``."""

    types: list[str] | None = None
    since: str | None = None
    limit: int | None = None
    full: bool = False


class QueryParams(Page, kw_only=True):
    """Parameters of ``query``."""

    query: Annotated[
        dict[str, Any],
        msgspec.Meta(description="one kind: keys, runs, series, data, timeline, folders, file"),
    ]


Folder = Annotated[str, msgspec.Meta(description="folder below the log dir, or a run id")]
Author = Annotated[
    str | None,
    msgspec.Meta(
        description="who writes it: a person, or your model id such as claude-opus-5-5; "
        "default: the local account"
    ),
]


class NotesParams(Page, kw_only=True):
    """Parameters of ``notes``."""

    from_: Folder = msgspec.field(default=".", name="from")
    types: list[str] | None = None
    open: Annotated[bool, msgspec.Meta(description="only open questions")] = False
    full: Annotated[bool, msgspec.Meta(description="include fields and bodies")] = False
    limit: int | None = None


class FolderParams(Params, kw_only=True):
    """Parameters of operations on one folder's research record."""

    folder: Folder = "."


class CheckParams(FolderParams, kw_only=True):
    """Parameters of ``check``."""

    version: Annotated[str | None, msgspec.Meta(description="default: the current one")] = None


class NoteAddParams(Params, kw_only=True):
    """Parameters of ``note add``."""

    folder: Folder
    type: Literal["observation", "decision", "idea", "question", "verdict"]
    description: Annotated[str, msgspec.Meta(description="one line; what listings show")]
    body: Annotated[
        str | None, msgspec.Meta(description="Markdown; [[run-id]], [[folder#prediction]] link")
    ] = None
    resolves: Annotated[list[str], msgspec.Meta(description="ids of notes it answers")] = (
        msgspec.field(default_factory=list)
    )
    supersedes: Annotated[str | None, msgspec.Meta(description="id of a note it corrects")] = None
    completes: Annotated[
        list[str], msgspec.Meta(description="decisions: folders declared complete")
    ] = msgspec.field(default_factory=list)
    evidence: Annotated[
        list[str | dict[str, Any]],
        msgspec.Meta(
            description="run ids, note ids, folder#prediction, folder@view-version, or "
            "{metric, stat, run, value}"
        ),
    ] = msgspec.field(default_factory=list)
    proposal: Annotated[
        str | None, msgspec.Meta(description="verdicts: the judged proposal version")
    ] = None
    verdict: Annotated[
        dict[str, str],
        msgspec.Meta(description="verdicts: prediction -> confirmed, refuted or inconclusive"),
    ] = msgspec.field(default_factory=dict)
    overall: Literal["confirmed", "refuted", "inconclusive"] | None = None
    author: Author = None


class ProposalSetParams(Params, kw_only=True):
    """Parameters of ``proposal set``."""

    folder: Folder
    file: Annotated[str | None, msgspec.Meta(description="a YAML file with the proposal")] = None
    proposal: Annotated[
        dict[str, Any] | str | None,
        msgspec.Meta(description="the proposal as an object or YAML text, instead of file"),
    ] = None
    reason: Annotated[
        str | None,
        msgspec.Meta(description="why a frozen current version is superseded"),
    ] = None
    author: Author = None


class MemoryUpdateParams(Params, kw_only=True):
    """Parameters of ``memory update``."""

    folder: Folder = "."
    file: Annotated[str | None, msgspec.Meta(description="a Markdown file")] = None
    body: Annotated[str | None, msgspec.Meta(description="the memory, instead of file")] = None
    covers_until: Annotated[
        str | None, msgspec.Meta(description="default: the time of the newest note in scope")
    ] = None
    author: Author = None


class InitParams(Params, kw_only=True):
    """Parameters of ``init``."""

    logdir: str | None = None


class MoveParams(Params, kw_only=True):
    """Parameters of ``mv``."""

    run: str
    folder: str


class RemoveParams(Params, kw_only=True):
    """Parameters of ``rm``."""

    target: str


class GcParams(Params, kw_only=True):
    """Parameters of ``gc``."""

    yes: bool = False


class McpInstallParams(Params, kw_only=True):
    """Parameters of ``mcp install``."""

    client: Literal["claude-code", "cursor", "codex"] = "claude-code"


@dataclass(frozen=True, kw_only=True)
class Op:
    """One operation of the set."""

    name: str
    params: type[Params]
    summary: str
    impl: str
    positional: tuple[str, ...] = ()
    user_only: bool = False
    stdin: str | None = None

    @property
    def tool(self) -> str:
        """The MCP tool name: the CLI path with ``_`` for spaces."""
        return self.name.replace(" ", "_")

    def function(self) -> Any:
        """Import the implementation.

        :return: The function ``(context, params) -> answer``."""
        module, name = self.impl.split(":")
        return getattr(import_module(module), name)


R = "beamtime.ops.reading"
W = "beamtime.ops.record"
A = "beamtime.ops.admin"
OPS = [
    Op(
        name="status",
        params=NoParams,
        impl=f"{R}:status",
        summary="Daemon, index and freshness; check before working with live runs.",
    ),
    Op(
        name="keys",
        params=KeysParams,
        impl=f"{R}:keys",
        positional=("from_",),
        summary="Metrics, config keys, data keys and tags: the first call in a folder.",
    ),
    Op(
        name="folders",
        params=FoldersParams,
        impl=f"{R}:folders",
        positional=("from_",),
        summary="The folder tree: research status, check, verdict and run counts.",
    ),
    Op(
        name="runs",
        params=RunsParams,
        impl=f"{R}:runs",
        positional=("from_",),
        summary="A run table: filter with where, choose columns, sort, limit.",
    ),
    Op(
        name="card",
        params=CardParams,
        impl=f"{R}:card",
        positional=("run",),
        summary="One run's card: status, config, metric statistics, recent events.",
    ),
    Op(
        name="series",
        params=SeriesParams,
        impl=f"{R}:series",
        positional=("from_",),
        summary="Curves of metrics, raw or downsampled, per run or grouped.",
    ),
    Op(
        name="data",
        params=DataParams,
        impl=f"{R}:data",
        positional=("from_", "key"),
        summary="Logged tables, images (as file references) and text of a key.",
    ),
    Op(
        name="file",
        params=FileParams,
        impl=f"{R}:file",
        positional=("view", "path"),
        summary="A data file stored with a view.",
    ),
    Op(
        name="output",
        params=OutputParams,
        impl=f"{R}:output",
        positional=("run",),
        summary="Captured stdout and stderr of a run: tail, grep, rank.",
    ),
    Op(
        name="timeline",
        params=TimelineParams,
        impl=f"{R}:timeline",
        positional=("from_",),
        summary="Notes and run events in time order.",
    ),
    Op(
        name="notes",
        params=NotesParams,
        impl=f"{W}:notes",
        positional=("from_",),
        summary="Notes with descriptions and states; open questions with --open.",
    ),
    Op(
        name="proposal show",
        params=FolderParams,
        impl=f"{W}:proposal_show",
        positional=("folder",),
        summary="The current proposal, its earlier versions and their checks.",
    ),
    Op(
        name="check",
        params=CheckParams,
        impl=f"{W}:check",
        positional=("folder",),
        summary="The predictions of a proposal version and their results, with plan progress.",
    ),
    Op(
        name="memory show",
        params=FolderParams,
        impl=f"{W}:memory_show",
        positional=("folder",),
        summary="The memory of a folder and every folder above it; read before designing.",
    ),
    Op(
        name="note add",
        params=NoteAddParams,
        impl=f"{W}:note_add",
        positional=("folder",),
        stdin="body",
        summary="Add a note; verdicts get the check snapshot added automatically.",
    ),
    Op(
        name="proposal set",
        params=ProposalSetParams,
        impl=f"{W}:proposal_set",
        positional=("folder", "file"),
        stdin="proposal",
        summary="Save a new proposal version; a frozen one is superseded with a reason.",
    ),
    Op(
        name="memory update",
        params=MemoryUpdateParams,
        impl=f"{W}:memory_update",
        positional=("folder", "file"),
        stdin="body",
        summary="Save a new memory version; warns beyond the size budget.",
    ),
    Op(
        name="query",
        params=QueryParams,
        impl=f"{R}:query",
        summary="Any query in its object form, e.g. {runs: {from: ., limit: 5}}.",
    ),
    Op(
        name="init",
        params=InitParams,
        impl=f"{A}:init",
        user_only=True,
        summary="Set up this project: log dir in .gitignore, beamtime.yaml.",
    ),
    Op(
        name="mcp install",
        params=McpInstallParams,
        impl=f"{A}:mcp_install",
        user_only=True,
        summary="Register `beamtime mcp` with an agent client.",
    ),
    Op(
        name="settings",
        params=NoParams,
        impl=f"{A}:settings",
        user_only=True,
        summary="The effective settings and the level each value comes from.",
    ),
    Op(
        name="doctor",
        params=NoParams,
        impl=f"{A}:doctor",
        user_only=True,
        summary="Check the installation, root, log dir and cache.",
    ),
    Op(
        name="reindex",
        params=NoParams,
        impl=f"{A}:reindex",
        user_only=True,
        summary="Rebuild the index from the files.",
    ),
    Op(
        name="mv",
        params=MoveParams,
        impl=f"{A}:move",
        positional=("run", "folder"),
        user_only=True,
        summary="Move a run to another folder; running runs are refused.",
    ),
    Op(
        name="rm",
        params=RemoveParams,
        impl=f"{A}:remove",
        positional=("target",),
        user_only=True,
        summary="Move a run or folder into the trash.",
    ),
    Op(
        name="gc",
        params=GcParams,
        impl=f"{A}:gc",
        user_only=True,
        summary="Empty the trash and remove ended runs without metrics (with --yes).",
    ),
]

BY_NAME = {op.name: op for op in OPS}
BY_TOOL = {op.tool: op for op in OPS if not op.user_only}
