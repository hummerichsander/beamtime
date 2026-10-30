"""The sources besides this machine: remotes from the settings or the command line, each with
its connection."""

import atexit
from collections.abc import Callable
from typing import Any

from beamtime.ops.context import Context, OpError
from beamtime.remote.client import RemoteClient, Spec, Unreachable


def spec_of(name: str, conf: dict[str, Any]) -> Spec:
    """Turn a remote's settings into a spec.

    :param name: The remote's name.
    :param conf: Its merged settings: ``host``, ``command``, ``cache``, ``path``, ``transport``.
    :return: The spec.
    :raises OpError: Without a ``path``."""
    if not conf.get("path"):
        raise OpError(
            f"remote {name!r} has no path; set it in beamtime.yaml: "
            f"remotes: {{{name}: {{path: /scratch/.../beamtime}}}}",
            code=2,
        )
    return Spec(
        name=name,
        path=str(conf["path"]),
        host=conf.get("host"),
        command=str(conf.get("command") or "beamtime"),
        cache=conf.get("cache"),
        transport=conf.get("transport") or "ssh",
    )


def parse_arg(arg: str, configured: dict[str, Any]) -> Spec:
    """Read a source named on the command line.

    :param arg: ``cluster``, ``cluster:scaling`` (narrowed to a group) or ``host:/abs/path``.
    :param configured: The remotes from the settings.
    :return: The spec."""
    name, _, rest = arg.partition(":")
    if name in configured:
        spec = spec_of(name, configured[name])
        if rest:
            spec.scope = rest.strip("/") or "."
        return spec
    if rest.startswith("/") or rest.startswith("~") or rest.startswith("$"):
        return Spec(name=name.split("@")[-1].split(".")[0], host=name, path=rest)
    known = ", ".join(sorted(configured)) or "none configured"
    raise OpError(
        f"no remote {name!r} (configured: {known}); name one from the settings or give "
        "host:/absolute/path/to/beamtime",
        code=2,
    )


class Sources:
    """The remotes one process talks to, by name."""

    def __init__(self, specs: list[Spec], on_event: Callable[[str, dict], None] | None = None):
        """Prepare a connection per remote; each connects on first use.

        :param specs: The remotes.
        :param on_event: Called with the source's name and each event it sends."""
        self.clients: dict[str, RemoteClient] = {}
        for spec in specs:
            callback = (lambda e, n=spec.name: on_event(n, e)) if on_event is not None else None
            self.clients[spec.name] = RemoteClient(spec=spec, on_event=callback)

    def get(self, name: str) -> RemoteClient:
        """Find a source by name.

        :param name: Without the ``@``.
        :return: Its client.
        :raises OpError: If there is no such source here."""
        if (client := self.clients.get(name)) is None:
            known = ", ".join(f"@{n}" for n in self.clients) or "none"
            raise OpError(f"no source @{name} here (sources: {known})", code=4)
        return client

    def close(self) -> None:
        """Close every connection."""
        for client in self.clients.values():
            client.close()


# remotes a one-shot call connected to, kept until the process ends.
opened: dict[str, RemoteClient] = {}


def client_for(ctx: Context, name: str) -> RemoteClient:
    """Find the connection for a source: the running serve's, else a new one for this process.

    :param ctx: The operation context, for the remotes in its settings.
    :param name: The source, without the ``@``.
    :return: Its client."""
    from beamtime import remote

    if remote.active is not None and name in remote.active.clients:
        return remote.active.get(name)
    if name not in opened:
        configured = ctx.settings.get("remotes") or {}
        if name not in configured:
            known = ", ".join(f"@{n}" for n in sorted(configured)) or "none configured"
            # a pulled snapshot may still answer for a remote that isn't configured here.
            raise Unreachable(
                f"no source @{name} (remotes: {known}); add it under remotes: in the settings",
                code=4,
            )
        if not opened:
            atexit.register(lambda: [c.close() for c in opened.values()])
        opened[name] = RemoteClient(spec=spec_of(name, configured[name]))
    return opened[name]
