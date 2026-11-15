"""What changed between releases that a person may notice, for the end of an update."""

from beamtime.setup.plan import release

# per release: the few changes someone updating would notice; the changelog has the rest.
CHANGES: dict[str, tuple[str, ...]] = {
    "0.2.0": (
        "Charts: pin main metrics in the UI; a colormap is chosen per chart.",
        "`series --json` gives each curve y, lo, hi and n.",
        "A run is named by its id, its name, or an id suffix of four characters or more.",
    ),
    "0.3.0": (
        "`beamtime init` sets up a project and `beamtime init --check` lists what is stale.",
        "`beamtime status` says when the setup is older than the installed release.",
    ),
}


def since(setup: str, current: str) -> list[str]:
    """List the noticeable changes of the releases after a setup's and up to the current one.

    :param setup: The release that set the project up, e.g. ``0.1.1``.
    :param current: The installed release.
    :return: The lines, oldest release first; empty when nothing was kept for them."""
    return [
        line
        for version, lines in sorted(CHANGES.items(), key=lambda kv: release(kv[0]))
        if release(setup) < release(version) <= release(current)
        for line in lines
    ]
