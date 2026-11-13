"""The scan: what a project and this machine look like, read from local files only."""

import glob
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from beamtime.format.constants import RUN
from beamtime.index.cache import NETWORK_FS
from beamtime.ops.admin import SKIP
from beamtime.sdk.paths import DEFAULT_LOGDIR, SETTINGS
from beamtime.settings import read_level

Flow = Literal["first", "teammate", "cluster", "update", "current"]

SCHEDULERS = {"sbatch": "slurm", "qsub": "pbs", "bsub": "lsf"}
DIRECTIVES = {"#SBATCH": "slurm", "#PBS": "pbs", "#BSUB": "lsf"}
JOB_SUFFIXES = (".sbatch", ".slurm", ".sh", ".pbs", ".lsf", ".job")
SCRATCH_VARS = ("SCRATCH", "SCRATCHDIR", "WORK", "WORKDIR", "PROJECT")
LIGHTNING = re.compile(r"^\s*(?:import|from)\s+(?:pytorch_lightning|lightning)\b", re.MULTILINE)
READ_BYTES = 1 << 20


@dataclass(frozen=True)
class Project:
    """The project's settings file and log dir."""

    settings: bool
    logdir: Path
    has_logdir: bool
    runs: int
    notes: int
    proposals: int
    memories: int
    remotes: tuple[str, ...]


@dataclass(frozen=True)
class Git:
    """The git checkout around the project."""

    root: Path | None
    branch: str | None
    clean: bool | None
    logdir_ignored: bool


@dataclass(frozen=True)
class PythonEnv:
    """The project's Python environment, read from disk and never imported."""

    tool: Literal["uv", "poetry", "conda", "pip"]
    path: Path | None
    python: str | None
    beamtime_version: str | None
    has_serve: bool


@dataclass(frozen=True)
class JobScript:
    """A batch script of a scheduler and the ssh hosts it names."""

    path: str
    scheduler: str
    hosts: tuple[str, ...]


@dataclass(frozen=True)
class SshHost:
    """A ``Host`` entry of the ssh config."""

    name: str
    hostname: str | None
    user: str | None


@dataclass(frozen=True)
class Disk:
    """A folder of this machine and the type of the filesystem under it."""

    label: str
    path: Path
    fstype: str | None
    network: bool


@dataclass(frozen=True)
class Scan:
    """Everything the wizard looks at before it asks."""

    root: Path
    home: Path
    project: Project
    git: Git
    env: PythonEnv | None
    framework: str | None
    job_scripts: tuple[JobScript, ...]
    ssh_hosts: tuple[SshHost, ...]
    disks: tuple[Disk, ...]
    scheduler: str | None
    display: bool
    flow: Flow


def scan(
    root: Path,
    *,
    home: Path | None = None,
    mounts: Path = Path("/proc/mounts"),
    env: Mapping[str, str] | None = None,
) -> Scan:
    """Look at a project and this machine, without network, ssh or a slow subprocess.

    :param root: The project root.
    :param home: The home directory; default the user's.
    :param mounts: The file listing mounted filesystems.
    :param env: The environment variables; default the process's.
    :return: The facts and the flow they pick."""
    home = home or Path.home()
    env = os.environ if env is None else env
    project = read_project(root)
    files = list(code_files(root))
    hosts = read_ssh_hosts(home)
    disks = read_disks(home, mounts, env)
    scheduler = find_scheduler(env)
    display = has_display(env)
    user_remotes = read_level(user_settings(home, env), "user", []).get("remotes") or {}
    return Scan(
        root=root,
        home=home,
        project=project,
        git=read_git(root, project.logdir),
        env=read_env(root, env),
        framework=find_framework(files),
        job_scripts=find_job_scripts(root, files, hosts),
        ssh_hosts=hosts,
        disks=disks,
        scheduler=scheduler,
        display=display,
        flow=pick_flow(project, user_remotes, scheduler, display, disks),
    )


def pick_flow(
    project: Project,
    user_remotes: Mapping[str, object],
    scheduler: str | None,
    display: bool,
    disks: tuple[Disk, ...],
) -> Flow:
    """Pick the flow from the facts: cluster, teammate, update, current or first setup.

    :param project: The project facts.
    :param user_remotes: The remotes in this machine's settings.
    :param scheduler: The scheduler on ``PATH``, if any.
    :param display: Whether the machine has a display.
    :param disks: The disks, among them ``home``.
    :return: The flow."""
    if scheduler or not display or any(d.network for d in disks if d.label == "home"):
        return "cluster"
    if project.settings:
        return "teammate" if set(project.remotes) - set(user_remotes) else "current"
    return "update" if project.has_logdir else "first"


def user_settings(home: Path, env: Mapping[str, str]) -> Path:
    """Locate the user settings file for a home directory.

    :param home: The home directory.
    :param env: The environment variables.
    :return: ``$XDG_CONFIG_HOME/beamtime/settings.yaml`` or ``~/.config/...``."""
    base = Path(env["XDG_CONFIG_HOME"]) if env.get("XDG_CONFIG_HOME") else home / ".config"
    return base / "beamtime" / "settings.yaml"


def read_project(root: Path) -> Project:
    """Read the settings file and count what the log dir holds.

    :param root: The project root.
    :return: The project facts."""
    settings = (root / SETTINGS).is_file()
    given = read_level(root / SETTINGS, "project", [])
    logdir = (root / Path(given.get("logdir") or DEFAULT_LOGDIR).expanduser()).resolve()
    runs = notes = proposals = memories = 0
    for d, dirs, names in os.walk(logdir):
        dirs[:] = [x for x in dirs if not x.startswith((".", "_"))]
        runs += RUN in names
        match Path(d).name:
            case "notes":
                notes += sum(n.endswith(".md") for n in names)
            case "proposal":
                proposals += sum(n.endswith(".yaml") for n in names)
            case "memory":
                memories += sum(n.endswith(".md") for n in names)
    remotes = given.get("remotes") or {}
    return Project(
        settings=settings,
        logdir=logdir,
        has_logdir=logdir.is_dir(),
        runs=runs,
        notes=notes,
        proposals=proposals,
        memories=memories,
        remotes=tuple(remotes) if isinstance(remotes, dict) else (),
    )


def read_git(root: Path, logdir: Path) -> Git:
    """Read the branch and cleanliness of the checkout around the project.

    :param root: The project root.
    :param logdir: The log dir.
    :return: The git facts; no root outside a checkout."""
    top = next((p for p in (root, *root.resolve().parents) if (p / ".git").exists()), None)
    if top is None:
        return Git(None, None, None, False)
    try:
        status = subprocess.run(
            ["git", "-C", str(top), "status", "--porcelain", "--branch"],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        ).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return Git(top, None, None, ignores(top, logdir))
    head = status[0].removeprefix("## ").removeprefix("No commits yet on ").split("...")[0]
    branch = None if head.startswith("HEAD (no branch)") else head
    return Git(top, branch, len(status) == 1, ignores(top, logdir))


def ignores(top: Path, logdir: Path) -> bool:
    """Tell whether the ``.gitignore`` at the top of a checkout names the log dir.

    :param top: The checkout's root.
    :param logdir: The log dir.
    :return: ``True`` for an entry such as ``beamtime/`` or ``/beamtime``."""
    try:
        name = logdir.relative_to(top.resolve()).as_posix()
        lines = (top / ".gitignore").read_text().splitlines()
    except (OSError, ValueError):
        return False
    return any(line.strip().strip("/").removesuffix("/**").strip("/") == name for line in lines)


def read_env(root: Path, env: Mapping[str, str]) -> PythonEnv | None:
    """Find the project's Python environment and read its version and Beamtime from disk.

    :param root: The project root.
    :param env: The environment variables (``CONDA_PREFIX``).
    :return: The environment, or ``None`` when the project has none."""
    pyproject = root / "pyproject.toml"
    text = pyproject.read_text(errors="replace") if pyproject.is_file() else ""
    venv = next((root / d for d in (".venv", "venv") if (root / d).is_dir()), None)
    conda = env.get("CONDA_PREFIX")
    if (root / "uv.lock").is_file() or "[tool.uv" in text:
        tool, path = "uv", venv
    elif (root / "poetry.lock").is_file():
        tool, path = "poetry", venv
    elif (conda and env.get("CONDA_DEFAULT_ENV") != "base") or (root / "environment.yml").is_file():
        tool, path = "conda", Path(conda) if conda else None
    elif venv or any(root.glob("requirements*.txt")):
        tool, path = "pip", venv
    else:
        return None
    packages = next(iter(path.glob("lib/python3*/site-packages")), None) if path else None
    packages = packages or (path / "Lib" / "site-packages" if path else None)
    if packages is None or not packages.is_dir():
        return PythonEnv(tool, path, None, None, False)
    version = next((d.name for d in packages.glob("beamtime-*.dist-info")), None)
    return PythonEnv(
        tool=tool,
        path=path,
        python=packages.parent.name.removeprefix("python")
        if packages.parent.name != "Lib"
        else None,
        beamtime_version=version.removeprefix("beamtime-").removesuffix(".dist-info")
        if version
        else None,
        has_serve=all(any(packages.glob(f"{n}-*.dist-info")) for n in ("starlette", "uvicorn")),
    )


def code_files(root: Path) -> Iterator[Path]:
    """List the files two levels deep, without hidden, private and heavy folders.

    :param root: The project root.
    :return: The file paths."""
    for d, dirs, names in os.walk(root):
        depth = len(Path(d).relative_to(root).parts)
        dirs[:] = (
            []
            if depth >= 2
            else [x for x in dirs if not x.startswith((".", "_")) and x not in SKIP]
        )
        yield from (Path(d) / n for n in names)


def head_of(path: Path, size: int = READ_BYTES) -> str:
    """Read the start of a file, forgiving about encoding and errors.

    :param path: The file.
    :param size: How many bytes to read at most.
    :return: The text; empty if the file can't be read."""
    try:
        with path.open("rb") as f:
            return f.read(size).decode(errors="replace")
    except OSError:
        return ""


def find_framework(files: list[Path]) -> str | None:
    """Find the training framework the code imports.

    :param files: The files of the project.
    :return: ``lightning`` when a Python file imports it or ``pytorch_lightning``, else ``None``."""
    found = any(LIGHTNING.search(head_of(f)) for f in files if f.suffix == ".py")
    return "lightning" if found else None


def find_job_scripts(
    root: Path, files: list[Path], hosts: tuple[SshHost, ...]
) -> tuple[JobScript, ...]:
    """Find the scheduler scripts and the ssh hosts they name.

    :param root: The project root.
    :param files: The files of the project.
    :param hosts: The ssh hosts to look for, by alias and host name.
    :return: The job scripts, by path."""
    scripts = []
    for f in sorted(files):
        if f.suffix not in JOB_SUFFIXES:
            continue
        text = head_of(f, 8192)
        scheduler = "slurm" if f.suffix == ".sbatch" else None
        for line in text.splitlines():
            if (key := line.split(maxsplit=1)[0] if line.strip() else "") in DIRECTIVES:
                scheduler = scheduler or DIRECTIVES[key]
        if scheduler is None:
            continue
        named = tuple(h.name for h in hosts if names_host(text, h))
        scripts.append(JobScript(f.relative_to(root).as_posix(), scheduler, named))
    return tuple(scripts)


def names_host(text: str, host: SshHost) -> bool:
    """Tell whether a text mentions a host by alias or host name.

    :param text: The script.
    :param host: The ssh host.
    :return: ``True`` for a whole-word match."""
    return any(
        re.search(rf"(?<![\w.-]){re.escape(n)}(?![\w-])", text)
        for n in (host.name, host.hostname)
        if n
    )


def read_ssh_hosts(home: Path) -> tuple[SshHost, ...]:
    """Read the hosts of ``~/.ssh/config`` and its includes, without wildcard patterns.

    :param home: The home directory.
    :return: The hosts in file order."""
    hosts: list[SshHost] = []
    parse_ssh_config(home / ".ssh" / "config", home, hosts, set())
    return tuple(hosts)


def parse_ssh_config(path: Path, home: Path, hosts: list[SshHost], seen: set[Path]) -> None:
    """Add the hosts of one ssh config file, following its ``Include`` lines.

    :param path: The file.
    :param home: The home directory, for ``~`` and relative includes.
    :param hosts: Collects the hosts.
    :param seen: The files already read, against include loops."""
    if path in seen:
        return
    seen.add(path)
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return
    names: list[str] = []
    fields: dict[str, str] = {}

    def flush() -> None:
        hosts.extend(SshHost(n, fields.get("hostname"), fields.get("user")) for n in names)
        names.clear()
        fields.clear()

    for line in lines:
        if not (m := re.match(r"\s*(\w+)\s*=?\s*(.*?)\s*$", line)) or line.lstrip().startswith("#"):
            continue
        key, value = m.group(1).lower(), m.group(2).strip('"')
        match key:
            case "host":
                flush()
                names += [
                    n for n in value.split() if not n.startswith("!") and not re.search(r"[*?]", n)
                ]
            case "include":
                flush()
                for pattern in value.split():
                    full = (
                        pattern.replace("~", str(home), 1) if pattern.startswith("~") else pattern
                    )
                    base = full if os.path.isabs(full) else str(home / ".ssh" / full)
                    for file in sorted(glob.glob(base)):
                        parse_ssh_config(Path(file), home, hosts, seen)
            case "hostname" | "user" if names:
                fields[key] = value
    flush()


def fs_type(path: Path, mounts: Path) -> str | None:
    """Find the type of the filesystem a path is on.

    :param path: The path (it may not exist).
    :param mounts: A ``/proc/mounts``-style file.
    :return: The type of the deepest mount containing the path, or ``None`` without the file."""
    try:
        lines = mounts.read_text().splitlines()
    except OSError:
        return None
    target = str(path.resolve())
    best, kind = "", None
    for parts in (line.split() for line in lines):
        if len(parts) < 3:
            continue
        mount = parts[1]
        if (target == mount or target.startswith(mount.rstrip("/") + "/")) and len(mount) > len(
            best
        ):
            best, kind = mount, parts[2]
    return kind


def read_disks(home: Path, mounts: Path, env: Mapping[str, str]) -> tuple[Disk, ...]:
    """Read the filesystem types under the folders a setup may write to.

    :param home: The home directory.
    :param mounts: A ``/proc/mounts``-style file.
    :param env: The environment variables (``XDG_CACHE_HOME`` and scratch-like variables).
    :return: Disks labeled ``home``, ``cache``, the variable's name, and ``tmp``."""
    cache = Path(env["XDG_CACHE_HOME"]) if env.get("XDG_CACHE_HOME") else home / ".cache"
    where = {"home": home, "cache": cache}
    where |= {v: Path(env[v]) for v in SCRATCH_VARS if env.get(v)}
    where["tmp"] = Path("/tmp")
    disks = []
    for label, path in where.items():
        kind = fs_type(path, mounts)
        disks.append(Disk(label, path, kind, kind in NETWORK_FS))
    return tuple(disks)


def find_scheduler(env: Mapping[str, str]) -> str | None:
    """Find a batch scheduler on ``PATH``.

    :param env: The environment variables.
    :return: ``slurm``, ``pbs`` or ``lsf``, or ``None``."""
    if not (path := env.get("PATH")):
        return None
    return next((name for cmd, name in SCHEDULERS.items() if shutil.which(cmd, path=path)), None)


def has_display(env: Mapping[str, str]) -> bool:
    """Tell whether the machine can show a window.

    :param env: The environment variables.
    :return: ``True`` on macOS and Windows, else when ``DISPLAY`` or ``WAYLAND_DISPLAY`` is set."""
    if sys.platform in ("darwin", "win32"):
        return True
    return bool(env.get("DISPLAY") or env.get("WAYLAND_DISPLAY"))
