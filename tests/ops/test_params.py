import msgspec
import pytest

from beamtime.mcp.server import tools
from beamtime.ops.registry import (
    BY_NAME,
    DataParams,
    GroupsParams,
    KeysParams,
    QueryParams,
    RunsParams,
    SeriesParams,
    TimelineParams,
)
from beamtime.query import models
from beamtime.views import code

EXTRAS = {"cursor", "to", "draft", "smooth"}
PARAMS = {
    "keys": (KeysParams, models.Keys),
    "groups": (GroupsParams, models.Groups),
    "runs": (RunsParams, models.Runs),
    "series": (SeriesParams, models.Series),
    "data": (DataParams, models.Data),
    "timeline": (TimelineParams, models.Timeline),
}


def encoded(struct: type[msgspec.Struct]) -> set[str]:
    """Name the fields of a struct as callers spell them.

    :param struct: A msgspec struct.
    :return: The encoded field names."""
    return {f.encode_name for f in msgspec.structs.fields(struct)}


@pytest.mark.parametrize("name", PARAMS)
def test_params_subclass_their_query_struct(name: str) -> None:
    """A query operation's params are its query struct plus a few extras."""
    params, query = PARAMS[name]
    assert BY_NAME[name].params is params
    assert issubclass(params, query)
    assert encoded(params) - encoded(query) <= EXTRAS
    assert encoded(query) <= encoded(params)


def test_smooth_is_the_flat_number() -> None:
    """The ``series`` operation takes ``smooth`` as one number and the query as ``{ema: ...}``."""
    assert msgspec.convert({"y": ["loss"], "smooth": 0.9}, SeriesParams).smooth == 0.9
    assert models.parse({"series": {"y": ["loss"], "smooth": {"ema": 0.9}}})[1].smooth.ema == 0.9


def test_code_kinds_follow_the_query_kinds() -> None:
    """Custom blocks may declare every query kind."""
    assert code.KINDS == tuple(models.KINDS)


def test_query_tool_lists_the_kinds() -> None:
    """The ``query`` tool's description of its body comes from the kind table."""
    assert QueryParams.__annotations__["query"] is models.QueryBody
    schema = next(t for t in tools() if t.name == "query").input_schema
    assert ", ".join(code.KINDS) in schema["properties"]["query"]["description"]


def test_body_is_the_params_without_paging_and_export() -> None:
    """``body`` encodes ``from`` under its query name and leaves out ``cursor`` and ``to``."""
    from beamtime.ops.reading import body

    p = msgspec.convert({"from": "g", "y": ["loss"], "cursor": "c", "to": "out.csv"}, SeriesParams)
    q = body(p)
    assert q["from"] == "g" and "from_" not in q
    assert q["y"] == ["loss"] and q["smooth"] is None
    assert not {"cursor", "to"} & q.keys()
    models.parse({"series": q})
