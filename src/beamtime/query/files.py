"""Data files stored with a view: CSV, JSON or Parquet read as tables."""

import csv
import io
import json
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.query import models as m
from beamtime.query.models import QueryError
from beamtime.query.select import Context, meta


def file_kind(ctx: Context, q: m.File) -> dict[str, Any]:
    """Answer a data file stored with a view.

    :param ctx: The query context.
    :param q: The query.
    :return: ``{columns, rows, meta}``."""
    view_dir = (ctx.index.folder_path(ctx.scope) / c.VIEW).resolve()
    path = (view_dir / q.path).resolve()
    if view_dir not in path.parents:
        raise QueryError(f"file {q.path!r} is outside {ctx.scope}/view")
    if not path.is_file():
        raise QueryError(f"no file {q.path!r} in {ctx.scope}/view", code="not_found")
    columns, rows = read_table(path)
    return {
        "kind": "file",
        "group": ctx.scope,
        "path": q.path,
        "columns": columns,
        "rows": rows,
        "meta": meta(ctx, matched=len(rows)),
    }


def read_table(path: Path) -> tuple[list[str], list[list[Any]]]:
    """Read a data file as a table.

    :param path: A CSV, JSON or Parquet file.
    :return: The columns and the rows."""
    match path.suffix.lower():
        case ".csv":
            lines = list(csv.reader(io.StringIO(path.read_text())))
            if not lines:
                raise QueryError(f"{path.name} is empty; a CSV starts with a header row")
            columns, *body = lines
            rows = [[number_or_text(v) for v in row] for row in body]
        case ".json":
            data = json.loads(path.read_text())
            if isinstance(data, dict) and "columns" in data and isinstance(data["columns"], dict):
                data = data["columns"]
            if isinstance(data, dict):
                columns = list(data)
                rows = [list(r) for r in zip(*data.values(), strict=False)]
            else:
                columns = list(dict.fromkeys(k for r in data for k in r))
                rows = [[r.get(k) for k in columns] for r in data]
        case ".parquet":
            try:
                import pyarrow.parquet as pq
            except ImportError:
                raise QueryError(
                    "reading Parquet view files needs PyArrow: pip install pyarrow"
                ) from None
            table = pq.read_table(path).to_pydict()
            columns = list(table)
            rows = [list(r) for r in zip(*table.values(), strict=False)]
        case other:
            raise QueryError(f"file: unsupported format {other!r}; use csv, json or parquet")
    return columns, rows


def number_or_text(value: str) -> Any:
    """Read a CSV cell as a number when it is one.

    :param value: The cell.
    :return: An int, a float or the text."""
    for kind in (int, float):
        try:
            return kind(value)
        except ValueError:
            continue
    return value
