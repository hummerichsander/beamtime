"""User-only commands: setup, settings, checks, and moving or deleting runs.

Agents never run these; they hand the user the command."""

import functools
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from beamtime.format import constants as c
from beamtime.format.io import read_json
from beamtime.format.run import derived_status
from beamtime.format.times import stamp
from beamtime.format.tree import is_reserved, is_run, iter_runs, to_trash
from beamtime.index.cache import daemon_status, resolve_cache
from beamtime.index.index import Index
from beamtime.ops import registry as r
from beamtime.ops.context import Context, OpError
from beamtime.ops.reading import find_run
from beamtime.settings import user_settings_path

if TYPE_CHECKING:
    from beamtime.setup.apply import ApplyError


def answer(kind: str, lines: list[str], **fields: Any) -> dict[str, Any]:
    """Build the answer of a user-only command.

    :param kind: The command.
    :param lines: What the command did or found, one line each.
    :param fields: More fields for ``--json``.
    :return: The answer."""
    return {"kind": kind, "lines": lines, **fields, "meta": {}}


def setup(ctx: Context, p: r.SetupParams) -> dict[str, Any]:
    """Set up the project and this machine: ask in a terminal, else plan from the flags.

    With a terminal and no ``--yes``, a first setup, a teammate's or a cluster's runs the wizard.
    Otherwise nothing is asked, and nothing is written without ``--yes``. With ``--check`` it
    only lists what is stale and asks for exit code 3 when something is.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What was changed, or the review and the command when nothing was written."""
    import dataclasses

    import msgspec

    from beamtime.setup.apply import ApplyError, apply
    from beamtime.setup.plan import Answers, command, plan, review
    from beamtime.setup.scan import scan

    if p.instructions and not p.agents:
        only_claude = (ctx.root / "CLAUDE.md").exists() and not (ctx.root / "AGENTS.md").exists()
        p = msgspec.structs.replace(p, agents=["claude-code" if only_claude else "other"])
    found = scan(ctx.root)
    fields = {"root": str(ctx.root), "logdir": str(found.project.logdir)}
    if p.check:
        lines = [s.line for s in found.stale]
        out = answer("setup", lines or ["nothing is stale"], written=[], **fields)
        out["stale"] = [dataclasses.asdict(s) for s in found.stale]
        out["meta"] = {"exit": 3} if lines else {}
        return out
    try:
        answers = Answers.from_params(p, found)
    except ValueError as e:
        raise OpError(str(e), code=2) from e
    if (
        not p.yes
        and found.flow in ("first", "teammate", "cluster")
        and sys.stdin.isatty()
        and sys.stdout.isatty()
    ):
        from beamtime.setup.flow import setup as wizard
        from beamtime.setup.term import Term

        try:
            written = wizard(Term.detect(), found, answers)
        except ApplyError as e:
            raise apply_failed(e) from e
        return answer("setup", [], written=written, **fields)
    try:
        changes = plan(found, answers)
    except ValueError as e:
        raise OpError(str(e), code=2) from e
    if not changes:
        return answer("setup", ["already set up"], written=[], **fields)
    if not p.yes:
        lines = [
            *review(changes),
            "",
            "Nothing was written. This command makes the same setup:",
            "",
            command(answers, found),
        ]
        return answer("setup", lines, written=[], **fields)
    lines: list[str] = []
    try:
        done = apply(changes, lines.append)
    except ApplyError as e:
        raise apply_failed(e) from e
    lines.append("next: log runs with beamtime.init() in your training script")
    return answer("setup", lines, written=[c.label for c in done], **fields)


def apply_failed(e: "ApplyError") -> OpError:
    """Word a failed apply: what stopped it and what was done before.

    :param e: The ``ApplyError``.
    :return: The error to raise."""
    return OpError(
        f"{e}\ndone: {', '.join(c.label for c in e.done) or 'nothing'}\n"
        "run `beamtime setup` again to pick up what is missing"
    )


def settings(ctx: Context, p: r.NoParams) -> dict[str, Any]:
    """Show the effective settings and where each value comes from.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The settings with their levels and any problems."""
    rows = [[k, v, level] for k, v, level in ctx.settings.flat()]
    return {
        "kind": "settings",
        "columns": ["key", "value", "level"],
        "rows": rows,
        "files": {
            "user": str(user_settings_path()),
            "project": str(ctx.root / "beamtime.yaml"),
        },
        "problems": ctx.settings.problems,
        "meta": {},
    }


def set_setting(ctx: Context, p: r.SetParams) -> dict[str, Any]:
    """Write one setting into the project's ``beamtime.yaml`` and use it from now on.

    :param ctx: The operation context; its settings are reloaded.
    :param p: The parameters.
    :return: What was written where."""
    import yaml

    from beamtime.settings import load, write_project
    from beamtime.views.theme import names

    value = yaml.safe_load(p.value) if isinstance(p.value, str) else p.value
    match p.key:
        case "theme":
            # a pair is chosen by its name without -light or -dark.
            themes = names(ctx.root)
            if value not in themes:
                raise OpError(f"no theme {value!r}; themes: {', '.join(themes)}", code=2)
        case "theme_mode":
            if value not in ("system", "light", "dark"):
                raise OpError("theme_mode is system, light or dark", code=2)
        case "figure_style":
            if isinstance(value, str):
                value = [value]
            if (
                not isinstance(value, list)
                or not value
                or not all(isinstance(v, str) for v in value)
            ):
                raise OpError(
                    "figure_style is a list of style names or .mplstyle files, "
                    "e.g. [science, nature, styles/paper.mplstyle]",
                    code=2,
                )
            files = [v for v in value if v.endswith(".mplstyle")]
            if missing := [f for f in files if not (ctx.root / f).is_file()]:
                raise OpError(
                    f"no style file {', '.join(missing)} in {ctx.root} (paths are relative to "
                    "the project)",
                    code=2,
                )
            known = figure_styles()
            if known and (unknown := [v for v in value if v not in known and v not in files]):
                raise OpError(
                    f"unknown style(s) {', '.join(unknown)}; styles: {', '.join(known)}, or a "
                    ".mplstyle file of the project",
                    code=2,
                )
        case other:
            raise ValueError(f"no setting {other!r}")
    path = write_project(ctx.root, p.key, value)
    ctx.settings = load(ctx.root)
    return answer("set", [f"{p.key}: {value} in {path}"], key=p.key, value=value)


@functools.cache
def figure_styles() -> list[str]:
    """List the matplotlib style sheets figures can use, scienceplots' included.

    :return: Style names, or an empty list without the figures extra."""
    try:
        import matplotlib.pyplot as plt
        import scienceplots  # noqa: F401
    except ImportError:
        return []
    return sorted(s for s in plt.style.available if not s.startswith("_"))


def project_styles(root: Path) -> list[str]:
    """List the project's own matplotlib style files.

    :param root: The project root.
    :return: Their paths relative to the root, e.g. ``styles/paper.mplstyle``."""
    out = []
    for d, dirs, names in os.walk(root):
        depth = len(Path(d).relative_to(root).parts)
        dirs[:] = (
            []
            if depth >= 3
            else [x for x in dirs if not x.startswith((".", "_")) and x not in SKIP]
        )
        out += [
            (Path(d) / n).relative_to(root).as_posix() for n in names if n.endswith(".mplstyle")
        ]
    return sorted(out)


# folders that never hold a project's style files, and can be large.
SKIP = ("node_modules", "venv", "beamtime", "__pycache__")


def doctor(ctx: Context, p: r.NoParams) -> dict[str, Any]:
    """Check the installation, root, log dir and cache.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: One check per row: name, ok, detail."""
    from importlib.metadata import version

    checks: list[list[Any]] = []

    def check(name: str, ok: bool | None, detail: str) -> None:
        checks.append([name, ok, detail])

    check("python", sys.version_info >= (3, 11), platform.python_version())
    check("beamtime", True, version("beamtime"))
    check("root", True, f"{ctx.root} (from {ctx.root_reason})")
    source = "BEAMTIME_LOGDIR" if os.environ.get("BEAMTIME_LOGDIR") else "settings"
    check("log dir", ctx.logdir.is_dir(), f"{ctx.logdir} (from {source})"
          + ("" if ctx.logdir.is_dir() else "; created by the first run"))  # fmt: skip
    target = ctx.logdir if ctx.logdir.is_dir() else ctx.root
    check("write access", os.access(target, os.W_OK), str(target))
    resolved = resolve_cache(ctx.logdir, ctx.settings)
    cache = resolved.path
    where = f"{cache} ({resolved.kind}, from {resolved.source})"
    if resolved.refused:
        where += f"; the configured folder is on {resolved.refused}, where SQLite is unsafe"
    try:
        cache.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(":memory:")
        db.execute("SELECT json_extract('{\"a\": 1}', '$.a')")
        check("cache", True, f"{where}; SQLite {sqlite3.sqlite_version}")
    except (OSError, sqlite3.Error) as e:
        check("cache", False, f"{where}: {e}")
    try:
        import mcp  # noqa: F401

        check("serve extra", True, "MCP SDK installed")
    except ImportError:
        check("serve extra", None, "not installed: pip install 'beamtime[serve]' for MCP")
    daemon = daemon_status(cache)
    check("daemon", None, f"running, pid {daemon.get('pid')}" if daemon else "not running")
    for problem in ctx.settings.problems:
        check("settings", False, problem)
    check("browser", *browser())
    for name, conf in sorted(ctx.settings.remotes.items()):
        for row in remote_checks(name, conf):
            check(*row)
    failed = [name for name, ok, _ in checks if ok is False]
    return {
        "kind": "doctor",
        "columns": ["check", "ok", "detail"],
        "rows": checks,
        "meta": {"failed": failed},
    }


def browser() -> tuple[bool | None, str]:
    """Check for a browser the headless renderer can use (view renders and validation).

    :return: Whether one starts, and which or how to install one."""
    from beamtime.views.render import INSTALL, launch

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, "no Playwright: views validate statically; install the serve extra to render"
    with sync_playwright() as p:
        found = launch(p)
        if found is None:
            return None, f"none installed: views validate statically; `{INSTALL}` adds one"
        name = f"{found.browser_type.name} {found.version}"
        found.close()
    return True, name


def remote_checks(name: str, conf: dict[str, Any]) -> list[tuple[str, bool | None, str]]:
    """Check one remote: its settings, the ssh login, Beamtime there, its log dir and cache.

    :param name: The remote's name.
    :param conf: Its merged settings.
    :return: ``(check, ok, detail)`` rows."""

    from beamtime.remote.client import RemoteClient
    from beamtime.remote.sources import spec_of

    label = f"@{name}"
    try:
        spec = spec_of(name, conf)
    except OpError as e:
        return [(label, False, str(e))]
    rows: list[tuple[str, bool | None, str]] = []
    if spec.transport == "ssh":
        host = spec.host or name
        login = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, "true"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if login.returncode != 0:
            hint = (
                "; with two-factor login, open a ControlMaster first: "
                f"`ssh -fN {host}` (ControlMaster auto, ControlPersist in ~/.ssh/config)"
            )
            reason = login.stderr.strip() or "login failed"
            return [(f"{label} ssh", False, f"{host}: {reason}{hint}")]
        rows.append((f"{label} ssh", True, f"{host} (no prompt needed)"))
    client = RemoteClient(spec=spec)
    try:
        hello = client.request("hello", {}, timeout=60)
    except OpError as e:
        return [*rows, (f"{label} beamtime", False, f"{spec.command}: {e}")]
    finally:
        client.close()
    rows.append((f"{label} beamtime", True, f"{hello['version']} ({spec.command})"))
    exists = bool(hello.get("logdir_exists"))
    rows.append((f"{label} log dir", exists, hello["logdir"] + ("" if exists else " (missing)")))
    cache = hello.get("cache") or {}
    if cache.get("refused"):
        detail = f"{spec.cache} is on {cache['refused']}; a temporary cache is used instead"
        rows.append((f"{label} cache", None, detail))
    elif cache.get("temporary"):
        rows.append((f"{label} cache", True, "temporary, deleted when the connection closes"))
    else:
        rows.append((f"{label} cache", True, str(cache.get("path"))))
    return rows


def source_add(ctx: Context, p: r.SourceAddParams) -> dict[str, Any]:
    """Add a remote to the settings: the user's by default, probing ssh for how to start
    Beamtime there unless ``--command`` is given.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What was written."""
    from beamtime.settings import load, user_settings_path, write_remote
    from beamtime.setup.remotes import probe_command, remote_name_problem

    if (problem := remote_name_problem(p.name)) is not None:
        raise OpError(f"{p.name!r}: {problem}", code=2)
    host, _, path = p.remote.partition(":")
    if not host or not path.startswith(("/", "~", "$")):
        raise OpError(f"{p.remote!r}: give host:/absolute/path/to/beamtime", code=2)
    command = p.command or probe_command(host, path)
    conf = {"host": host, "path": path, "command": command or "beamtime", "cache": p.cache}
    target = (ctx.root / "beamtime.yaml") if p.project else user_settings_path()
    write_remote(target, p.name, conf)
    ctx.settings = load(ctx.root)
    lines = [f"added @{p.name}: {host}:{path} ({conf['command']}) to {target}"]
    if command is None:
        lines.append(f"no beamtime found on {host}; give --command if `beamtime` isn't on its PATH")
    lines.append("`beamtime serve` picks it up; or `beamtime doctor` checks it first")
    return answer("source add", lines, name=p.name)


def source_list(ctx: Context, p: r.NoParams) -> dict[str, Any]:
    """List the configured remotes.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: One row per remote: name, host, path, command and cache."""
    remotes = ctx.settings.get("remotes") or {}
    rows = [
        [
            name,
            conf.get("host"),
            conf.get("path"),
            conf.get("command") or "beamtime",
            conf.get("cache"),
        ]
        for name, conf in sorted(remotes.items())
    ]
    return {
        "kind": "source list",
        "columns": ["name", "host", "path", "command", "cache"],
        "rows": rows,
        "meta": {},
    }


def source_rm(ctx: Context, p: r.SourceRmParams) -> dict[str, Any]:
    """Remove a remote from wherever it is configured.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What was removed."""
    from beamtime.settings import load, remove_remote, user_settings_path

    removed = [
        path
        for path in (user_settings_path(), ctx.root / "beamtime.yaml")
        if remove_remote(path, p.name)
    ]
    if not removed:
        raise OpError(f"no remote {p.name!r} configured", code=4)
    ctx.settings = load(ctx.root)
    return answer("source rm", [f"removed @{p.name} from {', '.join(str(x) for x in removed)}"])


def reindex(ctx: Context, p: r.NoParams) -> dict[str, Any]:
    """Rebuild the index from the files.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: How long it took and how many runs it found."""
    if not ctx.logdir.is_dir():
        raise OpError(f"no log dir at {ctx.logdir}", code=4)
    with Index(logdir=ctx.logdir, settings=ctx.settings) as index:
        t = time.perf_counter()
        freshness = index.reindex()
        n = index.store.db.execute("SELECT count(*) FROM runs").fetchone()[0]
    lines = [f"indexed {n} runs in {time.perf_counter() - t:.1f} s"]
    lines += [f"skipped {d}" for d in freshness.damaged]
    return answer("reindex", lines, runs=n)


def refuse_running(run_dir: Path, verb: str) -> None:
    """Refuse to move or delete a run that is still running.

    :param run_dir: The run directory.
    :param verb: What was asked, for the message."""
    info = read_json(run_dir / c.RUN)
    beat = (run_dir / c.RUN).stat().st_mtime
    if derived_status(info.get("status"), beat, time.time()) == "running":
        raise OpError(
            f"{run_dir.name} is still running (heartbeat "
            f"{time.time() - beat:.0f} s ago); {verb} it once it has ended",
            code=1,
        )


def move(ctx: Context, p: r.MoveParams) -> dict[str, Any]:
    """Move a run into another group, or move (rename) a group.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: Where it went."""
    source = (ctx.logdir / p.source.strip("/")).resolve()
    if source.is_dir() and ctx.logdir in source.parents and not (source / c.RUN).exists():
        return move_group(ctx, source, p.to)
    run_dir = find_run(ctx, p.source)
    refuse_running(run_dir, "move")
    target = inside(ctx, p.to)
    if (target / c.RUN).exists():
        raise OpError(f"{p.to!r} is a run; choose a group", code=2)
    target.mkdir(parents=True, exist_ok=True)
    dest = target / run_dir.name
    shutil.move(str(run_dir), str(dest))
    return answer(
        "mv",
        [
            f"moved {run_dir.relative_to(ctx.logdir)} to {dest.relative_to(ctx.logdir)}",
            "its proposal membership stays as recorded at its start",
        ],
        path=dest.relative_to(ctx.logdir).as_posix(),
    )


def move_group(ctx: Context, source: Path, to: str) -> dict[str, Any]:
    """Move or rename a group, and record the move so paths written before it still resolve.

    :param ctx: The operation context.
    :param source: The group's directory.
    :param to: Its new path below the log dir.
    :return: Where it went."""
    from beamtime.format import moves

    target = inside(ctx, to)
    old = source.relative_to(ctx.logdir).as_posix()
    new = target.relative_to(ctx.logdir).as_posix()
    if target.exists():
        raise OpError(f"{new!r} exists; choose a new path", code=2)
    if target == source or source in target.parents:
        raise OpError(f"{new!r} is inside {old!r}", code=2)
    if any((parent / c.RUN).exists() for parent in target.parents):
        raise OpError(f"{new!r} is inside a run; choose a group path", code=2)
    for run_dir in iter_runs(source):
        refuse_running(run_dir, "move")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    moves.record(ctx.logdir, old, new)
    return answer(
        "mv",
        [
            f"moved {old} to {new}",
            f"runs, notes and links that name the old path still find it (recorded in {c.MOVES})",
        ],
        path=new,
    )


def inside(ctx: Context, path: str) -> Path:
    """Resolve a group path, refusing ones outside the log dir or with reserved names.

    :param ctx: The operation context.
    :param path: The path below the log dir.
    :return: The directory (it may not exist)."""
    target = (ctx.logdir / path.strip("/")).resolve()
    if ctx.logdir not in [target, *target.parents]:
        raise OpError(f"{path!r} is outside the log dir {ctx.logdir}", code=2)
    rel = target.relative_to(ctx.logdir)
    if any(is_reserved(part) for part in rel.parts):
        raise OpError(f"{path!r} has a reserved name; choose another", code=2)
    return target


def doomed_run_ids(paths: list[Path]) -> list[str]:
    """Collect the ids of every run below the given paths.

    :param paths: Run or group directories.
    :return: Their ids; unreadable runs are skipped."""
    ids = []
    for path in paths:
        for run_dir in iter_runs(path):
            try:
                ids.append(read_json(run_dir / c.RUN)["id"])
            except (OSError, ValueError, KeyError):
                continue
    return ids


def copies_of(ctx: Context, run_ids: list[str]) -> list[str]:
    """List runs that reference one of these runs' checkpoints by id.

    A copy stays readable once its source is gone; only the checkpoint becomes unresolved.

    :param ctx: The operation context.
    :param run_ids: The run ids about to be moved to the trash or deleted.
    :return: One line per referencing copy."""
    if not run_ids:
        return []
    with Index(logdir=ctx.logdir, settings=ctx.settings) as index:
        index.catch_up(".", budget_s=0.2)
        placeholders = ",".join("?" * len(run_ids))
        rows = index.store.db.execute(
            "SELECT id, path FROM runs WHERE json_extract(info, '$.copied_from.id') IN "
            f"({placeholders})",
            run_ids,
        ).fetchall()
    return [f"{run_id} ({path}) references its checkpoints" for run_id, path in rows]


def stray_copies(logdir: Path) -> list[Path]:
    """Find ``cp`` working directories a crash left behind, never renamed into place.

    :param logdir: The log dir.
    :return: Their paths."""
    from beamtime.ops.copy import TEMP_PREFIX

    out = []
    for d, dirs, _ in os.walk(logdir):
        keep = []
        for name in dirs:
            if name.startswith(TEMP_PREFIX):
                out.append(Path(d) / name)
            elif not is_reserved(name) and not is_run(Path(d) / name):
                keep.append(name)
        dirs[:] = keep
    return out


def remove(ctx: Context, p: r.RemoveParams) -> dict[str, Any]:
    """Move a run or group into the trash.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: Where it went."""
    target = (ctx.logdir / p.target).resolve()
    if not target.is_dir() or ctx.logdir not in target.parents:
        target = find_run(ctx, p.target)
    for run_dir in iter_runs(target):
        refuse_running(run_dir, "remove")
    rel = target.relative_to(ctx.logdir)
    if rel.parts and rel.parts[0] == c.TRASH:
        raise OpError("that is already in the trash; `beamtime gc --yes` empties it", code=2)
    referencing = copies_of(ctx, doomed_run_ids([target]))
    dest = to_trash(ctx.logdir, rel, stamp())
    lines = [f"moved {rel} to {dest}", "`beamtime gc --yes` deletes the trash for good"]
    lines += referencing
    return answer("rm", lines, trash=dest.as_posix())


def gc(ctx: Context, p: r.GcParams) -> dict[str, Any]:
    """Empty the trash and remove ended runs that never logged a metric.

    :param ctx: The operation context.
    :param p: The parameters; nothing is deleted without ``yes``.
    :return: What was (or would be) deleted."""
    doomed: list[Path] = []
    trash = ctx.logdir / c.TRASH
    if trash.is_dir():
        doomed += sorted(trash.iterdir())
    for run_dir in iter_runs(ctx.logdir):
        metrics = run_dir / c.METRICS
        if metrics.exists() and metrics.stat().st_size:
            continue
        try:
            refuse_running(run_dir, "collect")
        except OpError:
            continue
        doomed.append(run_dir)
    doomed += stray_copies(ctx.logdir)
    lines = [str(d.relative_to(ctx.logdir)) for d in doomed]
    if not doomed:
        return answer("gc", ["nothing to delete"], deleted=[])
    referencing = copies_of(ctx, doomed_run_ids(doomed))
    if not p.yes:
        return answer(
            "gc",
            [
                *lines,
                f"would delete {len(doomed)} item(s); run `beamtime gc --yes` to delete",
                *referencing,
            ],
            deleted=[],
        )
    for d in doomed:
        shutil.rmtree(d)
    return answer("gc", [*lines, f"deleted {len(doomed)} item(s)", *referencing], deleted=lines)


def mcp_install(ctx: Context, p: r.McpInstallParams) -> dict[str, Any]:
    """Register ``beamtime mcp`` with an agent client, with ``--skills`` write the Beamtime skills,
    and with ``--instructions`` add Beamtime's agent rules to its instruction file.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What was changed, or the config to paste."""
    from beamtime.setup.agents import ConfigError, client_named, register
    from beamtime.setup.scan import read_env

    client = client_named(p.client)
    try:
        change = register(client, ctx.root, read_env(ctx.root, os.environ))
    except ConfigError as e:
        raise OpError(str(e), code=3) from e
    if client.name == "other":
        lines = [f"{change.label}:", change.after]
    else:
        try:
            change.run()
        except ConfigError as e:
            raise OpError(str(e), code=3) from e
        lines = [f"wrote {change.after}"]
    answered = answer("mcp install", lines)
    if p.skills:
        from beamtime.guide.skills import write_skills

        names = [str(f.relative_to(ctx.root)) for f in write_skills(ctx.root)]
        answered["lines"].append(f"wrote {', '.join(names)}")
    if p.instructions:
        answered["lines"].append(write_rules(ctx, p.client))
    else:
        answered["lines"].append(
            f"`beamtime mcp install --instructions` adds the agent rules to {client.rules}"
        )
    return answered


def write_rules(ctx: Context, client: str) -> str:
    """Write Beamtime's agent rules into a client's instruction file, as one marked block.

    A rerun replaces the block, so updated rules arrive and the user's own text stays.

    :param ctx: The operation context, whose settings hold the agent behaviour.
    :param client: The agent client's name.
    :return: What happened."""
    from beamtime.setup.agents import client_named, rules_change

    c = client_named(client)
    change = rules_change(
        c, ctx.root, ctx.settings.agent, sorted(o.name for o in r.OPS if o.user_only)
    )
    file = ctx.root / c.rules
    match change.run():
        case "added":
            return f"added Beamtime's agent rules to {file}"
        case "updated":
            return f"updated Beamtime's agent rules in {file}"
        case _:
            return f"{file.name} has Beamtime's agent rules already"
