import sys, time, tempfile, os
from pathlib import Path
base = Path(sys.argv[1]); (base / "tmp").mkdir(exist_ok=True)
tempfile.tempdir = str(base / "tmp")
os.environ.pop("BEAMTIME_CACHE", None)
from beamtime.synth import generate
from beamtime.settings import Settings
from beamtime.index.daemon import Daemon
from beamtime.index.index import Index
logdir = base / "proj" / "beamtime"
generate(logdir, seed=0)
s = Settings(values={"cache": "memory"}, levels={"cache": "project"})
with Index(logdir=logdir, settings=s) as idx:
    f=idx.catch_up(".", 5.0); print("no daemon:", f.daemon, tuple(idx.store.db.execute("select count(*) from runs").fetchone()))
d = Daemon(logdir=logdir, settings=s, poll_s=0.2); assert d.start(); time.sleep(3)
with Index(logdir=logdir, settings=s) as idx:
    f=idx.catch_up(".", 5.0); print("daemon running:", f.daemon, tuple(idx.store.db.execute("select count(*) from runs").fetchone()))
d.stop()
