"""The operation set: one entry per operation, shared by the CLI, MCP and the API.

This module is imported on every CLI call, so it holds only names, parameter structs and
summaries; implementations are imported when an operation runs."""

from dataclasses import dataclass
from importlib import import_module
from typing import Annotated, Any, Literal

import msgspec

from beamtime.format.authored import NOTE_TYPES

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

    from_: Annotated[str, msgspec.Meta(description="group below the log dir, or a run id")] = (
        msgspec.field(default=".", name="from")
    )
    where: Where = msgspec.field(default_factory=dict)
    depth: Literal["all"] | int = "all"


class KeysParams(Selection, kw_only=True):
    """Parameters of ``keys``."""


class GroupsParams(Selection, kw_only=True):
    """Parameters of ``groups``."""


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
    points: Annotated[
        int | Literal["all"] | None,
        msgspec.Meta(description="points per curve; all: every logged point, as exports ask"),
    ] = None
    by: Annotated[
        list[str] | None, msgspec.Meta(description="aggregate runs by these fields, e.g. config.lr")
    ] = None
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
    draft: Annotated[str | None, msgspec.Meta(description="read from this draft instead")] = None


class OutputParams(Params, kw_only=True):
    """Parameters of ``output``."""

    run: str
    tail: int | None = 50
    grep: str | None = None
    rank: int = 0


class ResumeParams(Params, kw_only=True):
    """Parameters of ``resume``."""

    run: Annotated[str, msgspec.Meta(description="the run id")]


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
        msgspec.Meta(description="one kind: keys, runs, series, data, timeline, groups, file"),
    ]


Group = Annotated[str, msgspec.Meta(description="group below the log dir, or a run id")]
Author = Annotated[
    str | None,
    msgspec.Meta(
        description="who writes it: a person, or your model id such as claude-opus-5-5; "
        "default: the local account"
    ),
]


class NotesParams(Page, kw_only=True):
    """Parameters of ``notes``."""

    from_: Group = msgspec.field(default=".", name="from")
    types: list[str] | None = None
    open: Annotated[bool, msgspec.Meta(description="only open questions")] = False
    current: Annotated[
        bool, msgspec.Meta(description="leave out notes that a newer version supersedes")
    ] = False
    full: Annotated[bool, msgspec.Meta(description="include fields and bodies")] = False
    limit: int | None = None
    before: Annotated[
        str | None, msgspec.Meta(description="only notes older than this note id (paging)")
    ] = None


class GroupParams(Params, kw_only=True):
    """Parameters of operations on one group's research record."""

    group: Group = "."


class CheckParams(GroupParams, kw_only=True):
    """Parameters of ``check``."""

    version: Annotated[str | None, msgspec.Meta(description="default: the current one")] = None


class NoteAddParams(Params, kw_only=True):
    """Parameters of ``note add``."""

    group: Group
    type: Literal[NOTE_TYPES]
    description: Annotated[str, msgspec.Meta(description="one line; what listings show")]
    body: Annotated[
        str | None, msgspec.Meta(description="Markdown; [[run-id]], [[group#prediction]] link")
    ] = None
    resolves: Annotated[list[str], msgspec.Meta(description="ids of notes it answers")] = (
        msgspec.field(default_factory=list)
    )
    supersedes: Annotated[str | None, msgspec.Meta(description="id of a note it corrects")] = None
    completes: Annotated[
        list[str], msgspec.Meta(description="decisions: groups declared complete")
    ] = msgspec.field(default_factory=list)
    evidence: Annotated[
        list[str | dict[str, Any]],
        msgspec.Meta(
            description="run ids, note ids, group#prediction, group@view-version, or "
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


class NameParams(Params, kw_only=True):
    """Parameters of ``name``."""

    run: Annotated[str, msgspec.Meta(description="the run id")]
    name: Annotated[str, msgspec.Meta(description="the run's new display name")]
    author: Author = None


class NoteRmParams(Params, kw_only=True):
    """Parameters of ``note rm``."""

    note: Annotated[str, msgspec.Meta(description="the note's id")]


class ProposalSetParams(Params, kw_only=True):
    """Parameters of ``proposal set``."""

    group: Group
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

    group: Group = "."
    file: Annotated[str | None, msgspec.Meta(description="a Markdown file")] = None
    body: Annotated[str | None, msgspec.Meta(description="the memory, instead of file")] = None
    covers_until: Annotated[
        str | None, msgspec.Meta(description="default: the time of the newest note in scope")
    ] = None
    author: Author = None


Draft = Annotated[str, msgspec.Meta(description="the draft's name, from view new")]


class ViewNewParams(Params, kw_only=True):
    """Parameters of ``view new``."""

    group: Group
    from_: Annotated[
        Literal["sweep", "ablation", "run", "direction", "custom"] | None,
        msgspec.Meta(description="an example to start from; default: the page's current view"),
    ] = msgspec.field(default=None, name="from")
    name: Annotated[str | None, msgspec.Meta(description="default: the group's name")] = None


class ViewValidateParams(Params, kw_only=True):
    """Parameters of ``view validate``."""

    draft: Draft
    render: Annotated[bool, msgspec.Meta(description="also render once, if a browser exists")] = (
        True
    )


class ViewRenderParams(Params, kw_only=True):
    """Parameters of ``view render``."""

    draft: Draft
    block: Annotated[str | None, msgspec.Meta(description="one block's id; default the page")] = (
        None
    )
    theme: Literal["light", "dark"] = "light"
    width: int = 1280


class ViewSaveParams(Params, kw_only=True):
    """Parameters of ``view save``."""

    draft: Draft
    message: Annotated[str | None, msgspec.Meta(description="what this version changes")] = None
    author: Author = None


class ViewShowParams(Params, kw_only=True):
    """Parameters of ``view show``."""

    group: Group = "."
    version: Annotated[str | None, msgspec.Meta(description="default: the newest")] = None


class ViewHistoryParams(Params, kw_only=True):
    """Parameters of ``view history``."""

    group: Group = "."


class ExportParams(Params, kw_only=True):
    """Parameters of ``export``."""

    group: Group = "."
    html: Annotated[
        str | None, msgspec.Meta(description="a folder for the page, which then opens from disk")
    ] = None
    figures: Annotated[
        str | None, msgspec.Meta(description="a folder for one figure per block")
    ] = None
    points: Annotated[
        int | Literal["all"], msgspec.Meta(description="points per curve; all: every logged point")
    ] = 1000
    size: Annotated[
        Literal["single", "double"],
        msgspec.Meta(description="figure width: one column (3.3 in) or two (6.9 in)"),
    ] = "single"


class ViewOutdatedParams(Params, kw_only=True):
    """Parameters of ``view outdated``."""

    group: Group = "."


class ViewUpgradeParams(Params, kw_only=True):
    """Parameters of ``view upgrade``."""

    group: Group
    block: Annotated[str | None, msgspec.Meta(description="one block; default all")] = None
    author: Author = None


BlockName = Annotated[str, msgspec.Meta(description="a library block's name, e.g. phase-map")]
BlockDraft = Annotated[
    str, msgspec.Meta(description="the block draft's name, from promote or fork")
]


class BlockListParams(Params, kw_only=True):
    """Parameters of ``block list``."""

    group: Annotated[str, msgspec.Meta(description="the blocks this group can use")] = "."


class BlockShowParams(Params, kw_only=True):
    """Parameters of ``block show``."""

    name: BlockName
    group: Group = "."
    version: Annotated[str | None, msgspec.Meta(description="default: the newest")] = None


class BlockPromoteParams(Params, kw_only=True):
    """Parameters of ``block promote``."""

    group: Annotated[str, msgspec.Meta(description="the group whose view has the custom block")]
    block_id: Annotated[str, msgspec.Meta(description="the custom block's id in that view")]
    name: BlockName


class BlockForkParams(Params, kw_only=True):
    """Parameters of ``block fork``."""

    name: BlockName
    new_name: Annotated[str, msgspec.Meta(description="the new block's name")]
    group: Group = "."


class BlockValidateParams(Params, kw_only=True):
    """Parameters of ``block validate``."""

    draft: BlockDraft
    render: Annotated[
        bool, msgspec.Meta(description="render its examples, if a browser exists")
    ] = True


class BlockSaveParams(Params, kw_only=True):
    """Parameters of ``block save``."""

    draft: BlockDraft
    group: Annotated[str, msgspec.Meta(description="where it lives; default the log dir root")] = (
        "."
    )
    message: Annotated[str | None, msgspec.Meta(description="what this version changes")] = None
    author: Author = None


class BlockExportParams(Params, kw_only=True):
    """Parameters of ``block export``."""

    name: BlockName
    to: Annotated[str, msgspec.Meta(description="a folder; the block goes to <to>/blocks/<name>/")]
    group: Annotated[str, msgspec.Meta(description="the group whose library has it")] = "."


class BlockImportParams(Params, kw_only=True):
    """Parameters of ``block import``."""

    group: Annotated[str, msgspec.Meta(description="where the blocks go; . for every group")]
    from_: Annotated[
        str,
        msgspec.Meta(
            description="a project, a folder with blocks/, or a git URL with an optional @ref"
        ),
    ] = msgspec.field(name="from")
    name: Annotated[str | None, msgspec.Meta(description="one block; default all")] = None


class PullParams(Params, kw_only=True):
    """Parameters of ``pull``."""

    target: Annotated[str, msgspec.Meta(description="remote:group, e.g. cluster:scaling/lr-sweep")]
    drop: Annotated[bool, msgspec.Meta(description="remove the group from the snapshot")] = False


class GuideParams(Params, kw_only=True):
    """Parameters of ``guide``."""

    part: Annotated[
        Literal[
            "examples",
            "blocks",
            "queries",
            "checklist",
            "anti-patterns",
            "charts",
            "kit",
            "kit-api",
            "library",
            "proposals",
            "predictions",
            "notes",
            "verdicts",
            "memory",
            "remote",
            "analysis",
        ]
        | None,
        msgspec.Meta(description="default: the overview"),
    ] = None
    name: Annotated[
        str | None, msgspec.Meta(description="one example or block, e.g. sweep or scatter")
    ] = None
    group: Annotated[str | None, msgspec.Meta(description="fill examples with its keys")] = None


class SetParams(Params, kw_only=True):
    """Parameters of ``set``."""

    key: Literal["theme", "theme_mode", "figure_style"]
    value: Annotated[
        Any, msgspec.Meta(description="e.g. beamtime, dark, or [science, nature] (YAML)")
    ]


Instructions = Annotated[
    bool,
    msgspec.Meta(description="add Beamtime's agent rules to AGENTS.md (CLAUDE.md for Claude Code)"),
]


class InitParams(Params, kw_only=True):
    """Parameters of ``init``."""

    logdir: str | None = None
    instructions: Instructions = False


class CpParams(Params, kw_only=True):
    """Parameters of ``cp``."""

    source: Annotated[str, msgspec.Meta(description="a run id, or a group to copy")]
    dest: Annotated[str, msgspec.Meta(description="the destination group")]
    name: Annotated[
        str | None,
        msgspec.Meta(description="a run: its new display name; a group: the destination's name"),
    ] = None
    with_checkpoints: Annotated[
        bool,
        msgspec.Meta(description="copy checkpoint files in, leaving no reference to the source"),
    ] = False
    with_record: Annotated[
        bool,
        msgspec.Meta(
            description="a group only: also copy proposal, notes, view, memory and blocks"
        ),
    ] = False


class MoveParams(Params, kw_only=True):
    """Parameters of ``mv``."""

    source: Annotated[str, msgspec.Meta(description="a run id, or a group to move or rename")]
    to: Annotated[
        str, msgspec.Meta(description="a run: the group it goes into; a group: its new path")
    ]


class RemoveParams(Params, kw_only=True):
    """Parameters of ``rm``."""

    target: str


class GcParams(Params, kw_only=True):
    """Parameters of ``gc``."""

    yes: bool = False


class SourceAddParams(Params, kw_only=True):
    """Parameters of ``source add``."""

    name: str
    remote: Annotated[str, msgspec.Meta(description="host:/absolute/path/to/beamtime")]
    command: Annotated[
        str | None,
        msgspec.Meta(description="how to start beamtime there; probed over ssh by default"),
    ] = None
    cache: Annotated[
        str | None, msgspec.Meta(description="a persistent index cache on a local disk there")
    ] = None
    project: Annotated[
        bool, msgspec.Meta(description="write to this project's beamtime.yaml, not the user's")
    ] = False


class SourceRmParams(Params, kw_only=True):
    """Parameters of ``source rm``."""

    name: str


class ServeParams(Params, kw_only=True):
    """Parameters of ``serve``."""

    sources: Annotated[
        list[str],
        msgspec.Meta(description="remotes: names from the settings, name:group, or host:/path"),
    ] = msgspec.field(default_factory=list)

    port: Annotated[int, msgspec.Meta(description="the first port to try")] = 8080
    no_ui: Annotated[bool, msgspec.Meta(description="only index, no web UI")] = False
    open: Annotated[bool, msgspec.Meta(description="open the UI in a browser")] = False
    watch: Annotated[
        bool,
        msgspec.Meta(description="restart when Beamtime's own code changes (working on Beamtime)"),
    ] = False
    stdio: Annotated[
        bool, msgspec.Meta(description="answer the API on stdin/stdout (what a laptop starts)")
    ] = False
    logdir: Annotated[str | None, msgspec.Meta(description="with --stdio: the log dir")] = None
    cache: Annotated[
        str | None, msgspec.Meta(description="a persistent index cache on a local disk")
    ] = None


class DemoParams(Params, kw_only=True):
    """Parameters of ``demo``."""

    dir: str = "beamtime-demo"
    port: int = 8080
    open: bool = False
    seed: int = 1


class McpInstallParams(Params, kw_only=True):
    """Parameters of ``mcp install``."""

    client: Literal["claude-code", "cursor", "codex"] = "claude-code"
    instructions: Instructions = False


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
    # how remotes treat it: a listing merges across sources; a write is refused by snapshots;
    # draft work needs this project's drafts; local runs here even with an @remote target (pull).
    listing: bool = False
    writes: bool = False
    drafts: bool = False
    local: bool = False

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
V = "beamtime.ops.views"
B = "beamtime.ops.blocks"
C = "beamtime.ops.copy"
OPS = [
    Op(
        name="status",
        params=NoParams,
        impl=f"{R}:status",
        summary="Daemon, index and freshness; check before working with live runs.",
    ),
    Op(
        name="keys",
        listing=True,
        params=KeysParams,
        impl=f"{R}:keys",
        positional=("from_",),
        summary="Metrics, config keys, data keys and tags: the first call in a group.",
    ),
    Op(
        name="groups",
        listing=True,
        params=GroupsParams,
        impl=f"{R}:groups",
        positional=("from_",),
        summary="The group tree: research status, check, verdict and run counts.",
    ),
    Op(
        name="runs",
        listing=True,
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
        listing=True,
        params=SeriesParams,
        impl=f"{R}:series",
        positional=("from_",),
        summary="Curves of metrics, raw or downsampled, per run or aggregated.",
    ),
    Op(
        name="data",
        listing=True,
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
        name="resume",
        params=ResumeParams,
        impl=f"{R}:resume",
        positional=("run",),
        summary="What's needed to resume a killed run by hand: command, cwd, step, checkpoint.",
    ),
    Op(
        name="timeline",
        listing=True,
        params=TimelineParams,
        impl=f"{R}:timeline",
        positional=("from_",),
        summary="Notes and run events in time order.",
    ),
    Op(
        name="notes",
        listing=True,
        params=NotesParams,
        impl=f"{W}:notes",
        positional=("from_",),
        summary="Notes with descriptions and states; open questions with --open.",
    ),
    Op(
        name="proposal show",
        params=GroupParams,
        impl=f"{W}:proposal_show",
        positional=("group",),
        summary="The current proposal, its earlier versions and their checks.",
    ),
    Op(
        name="check",
        params=CheckParams,
        impl=f"{W}:check",
        positional=("group",),
        summary="The predictions of a proposal version and their results, with plan progress.",
    ),
    Op(
        name="memory show",
        params=GroupParams,
        impl=f"{W}:memory_show",
        positional=("group",),
        summary="The memory of a group and every group above it; read before designing.",
    ),
    Op(
        name="note add",
        writes=True,
        params=NoteAddParams,
        impl=f"{W}:note_add",
        positional=("group",),
        stdin="body",
        summary="Add a note; verdicts get the check snapshot added automatically.",
    ),
    Op(
        name="proposal set",
        writes=True,
        params=ProposalSetParams,
        impl=f"{W}:proposal_set",
        positional=("group", "file"),
        stdin="proposal",
        summary="Save a new proposal version; a frozen one is superseded with a reason.",
    ),
    Op(
        name="memory update",
        writes=True,
        params=MemoryUpdateParams,
        impl=f"{W}:memory_update",
        positional=("group", "file"),
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
        name="guide",
        params=GuideParams,
        impl="beamtime.guide:guide",
        positional=("part", "name"),
        summary="The agent guide by topic: views, charts, the record. Read before view new.",
    ),
    Op(
        name="view new",
        drafts=True,
        params=ViewNewParams,
        impl=f"{V}:new",
        positional=("group",),
        summary="Start a view draft in .beamtime/drafts/: from an example or the current view.",
    ),
    Op(
        name="view validate",
        drafts=True,
        params=ViewValidateParams,
        impl=f"{V}:validate",
        positional=("draft",),
        summary="Check a draft: schema, queries, fields, data, and one render for layout.",
    ),
    Op(
        name="view render",
        drafts=True,
        params=ViewRenderParams,
        impl=f"{V}:render",
        positional=("draft",),
        summary="Screenshot a draft (or one block) to look at it; at most two rounds.",
    ),
    Op(
        name="view save",
        drafts=True,
        params=ViewSaveParams,
        impl=f"{V}:save_draft",
        positional=("draft",),
        summary="Save a draft without errors as the page's new view version.",
    ),
    Op(
        name="view show",
        params=ViewShowParams,
        impl=f"{V}:show",
        positional=("group",),
        summary="The YAML of a page's current (or a given) view version.",
    ),
    Op(
        name="view history",
        params=ViewHistoryParams,
        impl=f"{V}:history",
        positional=("group",),
        summary="A page's view versions with author and message, newest first.",
    ),
    Op(
        name="export",
        local=True,
        params=ExportParams,
        impl=f"{V}:export",
        positional=("group",),
        summary="Write a page as HTML that opens from disk (--html), or its blocks as figures.",
    ),
    Op(
        name="view outdated",
        params=ViewOutdatedParams,
        impl=f"{V}:outdated",
        positional=("group",),
        summary="Views pinned to older versions of their library blocks.",
    ),
    Op(
        name="view upgrade",
        writes=True,
        params=ViewUpgradeParams,
        impl=f"{V}:upgrade",
        positional=("group",),
        summary="Re-pin a view to the newest versions of its library blocks; validates first.",
    ),
    Op(
        name="block list",
        params=BlockListParams,
        impl=f"{B}:listing",
        positional=("group",),
        summary="Library blocks a group can use, with descriptions and params.",
    ),
    Op(
        name="block show",
        params=BlockShowParams,
        impl=f"{B}:show",
        positional=("name",),
        summary="A library block's definition and code.",
    ),
    Op(
        name="block promote",
        drafts=True,
        params=BlockPromoteParams,
        impl=f"{B}:promote",
        positional=("group", "block_id", "name"),
        summary="Start a block draft from a custom block of a group's view.",
    ),
    Op(
        name="block fork",
        drafts=True,
        params=BlockForkParams,
        impl=f"{B}:fork",
        positional=("name", "new_name"),
        summary="Start a block draft as a copy of a library block.",
    ),
    Op(
        name="block validate",
        drafts=True,
        params=BlockValidateParams,
        impl=f"{B}:validate",
        positional=("draft",),
        summary="Check a block draft: params, examples, generality, code, and a render.",
    ),
    Op(
        name="block save",
        drafts=True,
        params=BlockSaveParams,
        impl=f"{B}:save_draft",
        positional=("draft",),
        summary="Save a block draft without errors as a new library block version.",
    ),
    Op(
        name="serve",
        params=ServeParams,
        impl="beamtime.serve.server:serve",
        positional=("sources",),
        user_only=True,
        summary="The web UI and the indexing daemon for this root; --no-ui only indexes.",
    ),
    Op(
        name="demo",
        params=DemoParams,
        impl="beamtime.serve.server:demo",
        positional=("dir",),
        user_only=True,
        summary="Generate a sample log dir and serve it.",
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
        name="set",
        params=SetParams,
        impl=f"{A}:set_setting",
        positional=("key", "value"),
        user_only=True,
        summary="Set theme, theme_mode or figure_style in this project's beamtime.yaml.",
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
        name="cp",
        writes=True,
        params=CpParams,
        impl=f"{C}:cp",
        positional=("source", "dest"),
        summary="Copy a run or group into another group, under new run ids; never the source.",
    ),
    Op(
        name="mv",
        params=MoveParams,
        impl=f"{A}:move",
        positional=("source", "to"),
        user_only=True,
        summary="Move a run into a group, or move or rename a group; running runs are refused.",
    ),
    Op(
        name="rm",
        params=RemoveParams,
        impl=f"{A}:remove",
        positional=("target",),
        user_only=True,
        summary="Move a run or group into the trash.",
    ),
    Op(
        name="name",
        writes=True,
        params=NameParams,
        impl=f"{W}:name",
        positional=("run", "name"),
        summary="Give a run a display name (a new version; the id never changes).",
    ),
    Op(
        name="block export",
        params=BlockExportParams,
        impl=f"{B}:export",
        positional=("name",),
        user_only=True,
        summary="Copy a library block with every version into <to>/blocks/<name>/.",
    ),
    Op(
        name="block import",
        params=BlockImportParams,
        impl=f"{B}:import_blocks",
        positional=("group",),
        user_only=True,
        summary="Copy library blocks from a project, a folder or a git repository into a group.",
    ),
    Op(
        name="pull",
        local=True,
        params=PullParams,
        impl="beamtime.remote.pull:pull_op",
        positional=("target",),
        user_only=True,
        summary="Copy a remote group into a read-only snapshot that answers while it's away.",
    ),
    Op(
        name="note rm",
        writes=True,
        params=NoteRmParams,
        impl=f"{W}:note_rm",
        positional=("note",),
        user_only=True,
        summary="Move a note, with the earlier versions it replaced, into the trash.",
    ),
    Op(
        name="gc",
        params=GcParams,
        impl=f"{A}:gc",
        user_only=True,
        summary="Empty the trash and remove ended runs without metrics (with --yes).",
    ),
    Op(
        name="source add",
        params=SourceAddParams,
        impl=f"{A}:source_add",
        positional=("name", "remote"),
        user_only=True,
        summary="Add a remote: name, host:/path; probes ssh for the command unless given.",
    ),
    Op(
        name="source list",
        params=NoParams,
        impl=f"{A}:source_list",
        user_only=True,
        summary="List the configured remotes.",
    ),
    Op(
        name="source rm",
        params=SourceRmParams,
        impl=f"{A}:source_rm",
        positional=("name",),
        user_only=True,
        summary="Remove a remote from wherever it is configured.",
    ),
]

BY_NAME = {op.name: op for op in OPS}
BY_TOOL = {op.tool: op for op in OPS if not op.user_only}
