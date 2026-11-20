"""Data files stored with a view: CSV, JSON or Parquet read as tables."""

import csv
import io
import json
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.query import models as m
from beamtime.query.models import QueryError, closest
from beamtime.query.select import Context, meta

FORMATS = (".csv", ".json", ".parquet")
WARN_BYTES = 2 << 20
# the remote bundle limit, so every saved view can also be saved on a remote.
MAX_BYTES = 16 << 20


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
    columns, rows = pick_columns(*read_table(path), q.columns, q.path)
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
            lines = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
            if not lines:
                raise QueryError(f"{path.name} is empty; a CSV starts with a header row")
            columns, *body = lines
            if len(columns) == 1 and (sep := next((s for s in ";\t" if s in columns[0]), None)):
                name = "tab" if sep == "\t" else sep
                raise QueryError(
                    f"{path.name} looks {name}-separated; "
                    "write it comma-separated: df.to_csv(path, index=False)"
                )
            if "" in columns:
                raise QueryError(
                    f"{path.name} has an empty column name; "
                    "an empty column name is usually a pandas index: df.to_csv(path, index=False)"
                )
            if len(set(columns)) != len(columns):
                dup = next(c for c in columns if columns.count(c) > 1)
                raise QueryError(f"{path.name} has the column name {dup!r} twice")
            for i, row in enumerate(body, start=2):
                if row and len(row) != len(columns):
                    raise QueryError(
                        f"{path.name} line {i}: {len(row)} cells, the header has {len(columns)}"
                    )
            # a blank line is no row, as in pandas; editors often leave one at the end.
            rows = [[number_or_text(v) for v in row] for row in body if row]
        case ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "columns" in data and isinstance(data["columns"], dict):
                data = data["columns"]
            if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
                columns = list(data)
                rows = [list(r) for r in zip(*data.values(), strict=False)]
            elif isinstance(data, list) and all(isinstance(r, dict) for r in data):
                columns = list(dict.fromkeys(k for r in data for k in r))
                rows = [[r.get(k) for k in columns] for r in data]
            else:
                raise QueryError(
                    f"{path.name} is no table; a JSON table is a list of records or "
                    "{column: [values]}: df.to_json(path, orient='records')"
                )
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
            raise QueryError(
                f"file: unsupported format {other!r}; use {', '.join(FORMATS).replace('.', '')}"
            )
    return columns, rows


def pick_columns(
    columns: list[str], rows: list[list[Any]], wanted: list[str] | None, name: str
) -> tuple[list[str], list[list[Any]]]:
    """Narrow a table to the wanted columns, in that order.

    :param columns: The table's columns.
    :param rows: The table's rows.
    :param wanted: The columns to keep, or ``None`` for all.
    :param name: The file's name, for the error.
    :return: The chosen columns and their rows."""
    if wanted is None:
        return columns, rows
    for w in wanted:
        if w not in columns:
            raise QueryError(
                f"no column {w!r} in {name}; its columns: {', '.join(columns)}."
                + closest(w, columns)
            )
    index = [columns.index(w) for w in wanted]
    return list(wanted), [[row[i] for i in index] for row in rows]


def number_or_text(value: str) -> Any:
    """Read a CSV cell as a number when it is one.

    :param value: The cell.
    :return: An int, a float, ``None`` for an empty cell or the text."""
    if value == "":
        return None
    for kind in (int, float):
        try:
            return kind(value)
        except ValueError:
            continue
    return value
