# Copyright 2024 General Atomics
# Licensed under the Apache License, Version 2.0.

"""toksearch_mast — MAST/MAST-U signal classes for TokSearch (FAIR MAST).

Registers the ``mast`` FDP device (``fdp_schema.catalogs`` entry point) and
provides ``MastSignal`` (FAIR MAST level-2 Zarr) plus parquet metadata
helpers. Configure the environment with ``setup_environment()`` (device
``mast``) or ``fdp run``.
"""

from . import _version

__version__ = _version.get_versions()["version"]

from .signal.mast import MastSignal
from .signal.imas import MastImasSignal, list_imas_paths
from .metadata import list_shots, list_signals
from .fdp import setup_environment

__all__ = [
    "__version__",
    "MastSignal",
    "MastImasSignal",
    "list_imas_paths",
    "list_shots",
    "list_signals",
    "setup_environment",
]
