"""The machine a run trains on: its hardware once at start, and system metrics while it runs.

Standard library only, plus ``nvidia-smi`` where it exists. What a platform can't tell (memory on
macOS, CPU load on Windows) is left out rather than guessed."""

import os
import platform
import shutil
import subprocess
from typing import Any

GPU_TIMEOUT_S = 5.0
GPU_QUERY = "utilization.gpu,memory.used,memory.total"


def hardware() -> dict[str, Any]:
    """Describe the CPU, memory and GPUs.

    :return: ``cpu``, ``cores``, ``memory_gb``, ``gpus``, ``cuda_visible_devices``, where known."""
    out: dict[str, Any] = {"cpu": cpu_model(), "cores": os.cpu_count()}
    if (total := memory_total()) is not None:
        out["memory_gb"] = round(total / 2**30, 1)
    if gpus := gpu_list():
        out["gpus"] = gpus
    if (visible := os.environ.get("CUDA_VISIBLE_DEVICES")) is not None:
        out["cuda_visible_devices"] = visible
    return out


def cpu_model() -> str | None:
    """Name the CPU.

    :return: The model, e.g. ``AMD EPYC 7742 64-Core Processor``."""
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    if platform.system() == "Darwin":
        try:
            name = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True,
                text=True,
                timeout=2,
            ).stdout.strip()
            if name:
                return name
        except (OSError, subprocess.SubprocessError):
            pass
    return platform.processor() or None


def memory_total() -> int | None:
    """Measure the machine's memory.

    :return: Bytes, or ``None`` where the platform doesn't say."""
    if (info := meminfo()) is not None:
        return info.get("MemTotal")
    if platform.system() == "Darwin":
        try:
            out = subprocess.run(
                ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=2
            ).stdout.strip()
            return int(out) if out.isdigit() else None
        except (OSError, subprocess.SubprocessError):
            return None
    return None


def meminfo() -> dict[str, int] | None:
    """Read Linux's ``/proc/meminfo``.

    :return: Its fields in bytes, or ``None`` elsewhere."""
    try:
        with open("/proc/meminfo") as f:
            lines = f.readlines()
    except OSError:
        return None
    out = {}
    for line in lines:
        name, _, rest = line.partition(":")
        parts = rest.split()
        if parts and parts[0].isdigit():
            out[name] = int(parts[0]) * (1024 if len(parts) > 1 and parts[1] == "kB" else 1)
    return out


def gpu_list() -> list[dict[str, Any]]:
    """List the GPUs ``nvidia-smi`` sees.

    :return: Name, memory in GB and driver per GPU; empty without NVIDIA GPUs."""
    rows = nvidia_smi("name,memory.total,driver_version")
    return [
        {"name": r[0], "memory_gb": round(float(r[1]) / 1024, 1), "driver": r[2]}
        for r in rows
        if len(r) == 3 and is_number(r[1])
    ]


def nvidia_smi(fields: str) -> list[list[str]]:
    """Ask ``nvidia-smi`` for some fields of every GPU.

    :param fields: Comma-separated query fields.
    :return: One row of values per GPU; empty without ``nvidia-smi`` or on errors."""
    if shutil.which("nvidia-smi") is None:
        return []
    try:
        done = subprocess.run(
            ["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=GPU_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if done.returncode != 0:
        return []
    return [
        [v.strip() for v in line.split(",")] for line in done.stdout.splitlines() if line.strip()
    ]


def is_number(text: str) -> bool:
    """Tell whether a value from ``nvidia-smi`` is a number (not ``[N/A]``).

    :param text: The value.
    :return: Whether it parses as a float."""
    try:
        float(text)
        return True
    except ValueError:
        return False


class Sampler:
    """Samples CPU, memory, the process's memory and the GPUs as ``sys/*`` metrics."""

    def __init__(self) -> None:
        """Take the first CPU reading; usage is measured between readings."""
        self.cpu = cpu_times()
        self.gpus = shutil.which("nvidia-smi") is not None

    def sample(self) -> dict[str, float]:
        """Measure the machine now.

        :return: ``sys/cpu`` and ``sys/memory`` (percent of the machine), ``sys/proc_rss`` (MB),
            and ``sys/gpu<i>/util`` and ``sys/gpu<i>/memory`` (percent); whatever is known."""
        out: dict[str, float] = {}
        if (now := cpu_times()) is not None and self.cpu is not None:
            busy, total = now[0] - self.cpu[0], now[1] - self.cpu[1]
            if total > 0:
                out["sys/cpu"] = round(100 * busy / total, 1)
        elif hasattr(os, "getloadavg") and (cores := os.cpu_count()):
            out["sys/cpu"] = round(min(100.0, 100 * os.getloadavg()[0] / cores), 1)
        self.cpu = now
        if (info := meminfo()) and info.get("MemTotal") and "MemAvailable" in info:
            out["sys/memory"] = round(100 * (1 - info["MemAvailable"] / info["MemTotal"]), 1)
        if (rss := process_rss()) is not None:
            out["sys/proc_rss"] = round(rss / 2**20, 1)
        if self.gpus:
            for i, row in enumerate(nvidia_smi(GPU_QUERY)):
                if len(row) == 3 and all(is_number(v) for v in row) and float(row[2]) > 0:
                    out[f"sys/gpu{i}/util"] = float(row[0])
                    out[f"sys/gpu{i}/memory"] = round(100 * float(row[1]) / float(row[2]), 1)
        return out


def cpu_times() -> tuple[float, float] | None:
    """Read the machine's busy and total CPU time from Linux's ``/proc/stat``.

    :return: ``(busy, total)`` jiffies, or ``None`` elsewhere."""
    try:
        with open("/proc/stat") as f:
            fields = [float(x) for x in f.readline().split()[1:]]
    except (OSError, ValueError):
        return None
    idle = fields[3] + (fields[4] if len(fields) > 4 else 0.0)
    return sum(fields) - idle, sum(fields)


def process_rss() -> int | None:
    """Measure this process's resident memory.

    :return: Bytes, or ``None`` where the platform doesn't say."""
    try:
        with open("/proc/self/statm") as f:
            return int(f.read().split()[1]) * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError, AttributeError):
        return None
