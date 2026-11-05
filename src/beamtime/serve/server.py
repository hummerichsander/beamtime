"""``beamtime serve`` and ``beamtime demo``: the daemon, the web UI and the token."""

import dataclasses
import os
import signal
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

from beamtime.ops import registry as r
from beamtime.ops.context import Context, OpError

PORT_TRIES = 10
WATCH_S = 1.0


def serve(ctx: Context, p: r.ServeParams) -> dict[str, Any]:
    """Run the daemon and, unless ``no_ui``, the web UI until interrupted.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What happened, once stopped."""
    if p.stdio:
        from beamtime.serve.stdio import run

        # stdout belongs to the protocol to the end: no closing answer is printed.
        raise SystemExit(run(logdir=p.logdir or str(ctx.logdir), cache=p.cache))
    try:
        import uvicorn

        from beamtime.serve.app import build
        from beamtime.serve.auth import TokenGuard, load_token
        from beamtime.serve.live import Hub
    except ImportError:
        raise OpError(
            "beamtime serve needs the serve extra: pip install 'beamtime[serve]'"
        ) from None
    from beamtime.index.cache import cache_dir, daemon_status
    from beamtime.index.daemon import Daemon

    if not ctx.logdir.is_dir():
        raise OpError(
            f"no log dir at {ctx.logdir}; runs appear there once a script calls "
            "beamtime.init() (or try `beamtime demo`)",
            code=4,
        )
    cache = cache_dir(ctx.logdir)
    hub = Hub()
    restart = threading.Event()
    sources = start_sources(ctx, p, hub)
    daemon = Daemon(logdir=ctx.logdir, cache=cache, on_change=hub.changed)
    sock = None if p.no_ui else bind(p.port)
    daemon.port = None if sock is None else sock.getsockname()[1]
    if not daemon.start():
        if sock is not None:
            sock.close()
        running = daemon_status(cache) or {}
        where = f" at http://localhost:{running['port']}" if running.get("port") else ""
        raise OpError(
            f"beamtime serve already runs for {ctx.logdir} (pid {running.get('pid')}){where}; "
            "open that one, or stop it first"
        )
    try:
        if sock is None:
            say(f"Beamtime indexes {ctx.logdir} (no UI); Ctrl-C stops.")
            while daemon.thread.is_alive():
                daemon.thread.join(1.0)
            return {"kind": "serve", "lines": ["stopped"]}
        token = load_token(cache)
        url = f"http://localhost:{daemon.port}/f/local?token={token}"
        app = build(ctx=dataclasses.replace(ctx, caller="view", sources=sources), hub=hub)
        guarded = TokenGuard(app, token=token, port=daemon.port)
        say(f"Beamtime serves {ctx.logdir}\n  {url}\nCtrl-C stops.")
        if p.open:
            webbrowser.open(url)
        config = uvicorn.Config(
            guarded, log_level="warning", lifespan="on", timeout_graceful_shutdown=1
        )
        # uvicorn re-raises the signal that stopped it; SIGTERM must still clean up.
        signal.signal(signal.SIGTERM, stop)
        server = server_class()(config, hub=hub)
        if p.watch:
            threading.Thread(target=watch_code, args=(server, restart), daemon=True).start()
            say("--watch: restarts when Beamtime's code changes.")
        server.run(sockets=[sock])
        return {"kind": "serve", "lines": ["stopped"]}
    except (KeyboardInterrupt, SystemExit):
        return {"kind": "serve", "lines": ["stopped"]}
    finally:
        daemon.stop()
        if sources is not None:
            sources.close()
        if sock is not None:
            sock.close()
        if restart.is_set():
            again(daemon.port)


def demo(ctx: Context, p: r.DemoParams) -> dict[str, Any]:
    """Generate the sample log dir (once) and serve it.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What happened, once stopped."""
    from beamtime.synth import generate

    root = Path(p.dir).expanduser().resolve()
    logdir = root / "beamtime"
    if not logdir.is_dir():
        generate(logdir, seed=p.seed)
        say(f"generated a sample log dir in {logdir}")
    demo_ctx = Context.make(root=root, caller="cli")
    return serve(demo_ctx, r.ServeParams(port=p.port, open=p.open))


def server_class() -> type:
    """Define the uvicorn server that ends live streams when asked to stop.

    :return: The class; defined lazily because uvicorn is an optional dependency."""
    import uvicorn

    class Server(uvicorn.Server):
        """A uvicorn server that closes the hub's streams first on exit."""

        def __init__(self, config: uvicorn.Config, *, hub: Any) -> None:
            """Create the server.

            :param config: The uvicorn configuration.
            :param hub: The live-update hub."""
            super().__init__(config)
            self.hub = hub

        def handle_exit(self, sig: int, frame: Any) -> None:
            """Close the streams, then shut down as usual.

            :param sig: The signal.
            :param frame: The interrupted frame."""
            self.hub.close()
            super().handle_exit(sig, frame)

    return Server


def bind(port: int) -> socket.socket:
    """Bind the UI's socket on localhost, moving to the next ports if one is taken.

    :param port: The first port to try.
    :return: The bound socket."""
    for candidate in range(port, port + PORT_TRIES):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", candidate))
        except OSError:
            sock.close()
            continue
        sock.listen(128)
        return sock
    raise OpError(f"ports {port} to {port + PORT_TRIES - 1} are taken; pass --port")


def forward_remote_change(hub: Any, name: str, event: dict[str, Any]) -> None:
    """Prefix a remote's changed paths with its source name and hand them to the hub.

    :param hub: The live-update hub.
    :param name: The source's name.
    :param event: The remote's ``changed`` event, ``{changed: {path: [kind, ...]}}``."""
    changed = event.get("changed") or {}
    hub.changed(
        {
            (f"@{name}" if path in (".", "") else f"@{name}/{path}"): set(kinds)
            for path, kinds in changed.items()
        }
    )


def start_sources(ctx: Context, p: r.ServeParams, hub: Any) -> Any:
    """Register the remotes this serve talks to: those named, else all from the settings.

    Each connects on first use; its change events reach the pages with the source's prefix.

    :param ctx: The operation context.
    :param p: The parameters.
    :param hub: The live-update hub.
    :return: The sources, or ``None`` without remotes."""
    from beamtime.remote.sources import Sources, parse_arg, spec_of

    configured = ctx.settings.get("remotes") or {}
    if p.sources:
        specs = [parse_arg(arg, configured) for arg in p.sources]
    else:
        specs = [spec_of(name, conf) for name, conf in sorted(configured.items())]
    if not specs:
        return None
    for spec in specs:
        if p.cache and spec.cache is None:
            spec.cache = p.cache

    sources = Sources(specs, on_event=lambda name, event: forward_remote_change(hub, name, event))
    shown = [
        f"@{s.name} ({s.host or s.name}:{s.path})"
        if s.transport == "ssh"
        else f"@{s.name} ({s.path})"
        for s in specs
    ]
    say("Sources: " + ", ".join(shown))
    return sources


def code_files() -> dict[str, int]:
    """Stamp Beamtime's own files: its Python modules, guide, themes and the built frontend.

    :return: Modification times by path."""
    root = Path(__file__).resolve().parents[1]
    out = {}
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for name in names:
            path = os.path.join(d, name)
            try:
                out[path] = os.stat(path).st_mtime_ns
            except OSError:
                pass
    return out


def watch_code(server: Any, restart: threading.Event) -> None:
    """Stop the server for a restart once Beamtime's code changes.

    :param server: The uvicorn server.
    :param restart: Set when a restart is due."""
    before = code_files()
    while not server.should_exit:
        time.sleep(WATCH_S)
        if code_files() != before:
            # a build writes many files: wait until they stop changing.
            time.sleep(WATCH_S)
            say("Beamtime's code changed; restarting.")
            restart.set()
            server.handle_exit(signal.SIGTERM, None)
            return


def again(port: int | None) -> None:
    """Replace this process with the same command on the same port, without opening a browser.

    :param port: The port the UI ran on."""
    args = [a for a in sys.orig_argv[1:] if a != "--open"]
    if port is not None:
        args += ["--port", str(port)]
    os.execv(sys.executable, [sys.executable, *args])


def stop(signum: int, frame: Any) -> None:
    """Turn SIGTERM into a normal exit, so the daemon releases its lock.

    :param signum: The signal.
    :param frame: The interrupted frame."""
    raise SystemExit(0)


def say(text: str) -> None:
    """Print a progress message for the user.

    :param text: The message."""
    print(text, file=sys.stderr, flush=True)
