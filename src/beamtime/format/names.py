"""Readable run names from high-energy physics vocabulary."""

import random

ADJECTIVES = (
    "boosted", "prompt", "displaced", "collinear", "soft", "hard", "polarized",
    "charmed", "strange", "virtual", "forward", "central", "isolated", "leading",
    "resonant", "transverse", "diffractive", "inclusive", "exclusive", "radiative",
)  # fmt: skip
PARTICLES = (
    "kaon", "photon", "muon", "pion", "gluon", "quark", "lepton", "boson", "tau",
    "neutrino", "hadron", "jet", "positron", "baryon", "meson", "higgs", "proton",
    "neutron", "electron", "upsilon",
)  # fmt: skip


def random_name(rng: random.Random | None = None) -> str:
    """Make a run name such as ``boosted-kaon-42``.

    :param rng: The random source; defaults to the module's.
    :return: The name."""
    rng = rng or random.Random()
    return f"{rng.choice(ADJECTIVES)}-{rng.choice(PARTICLES)}-{rng.randint(1, 99)}"
