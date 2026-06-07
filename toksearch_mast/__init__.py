# Copyright 2024 General Atomics
# Licensed under the Apache License, Version 2.0.

"""
toksearch_mast — MAST/MAST-U signal classes for the TokSearch framework.

Provides access to MAST and MAST-U experiment data via the public FAIR MAST
Zarr dataset hosted on STFC Echo S3.  Extends ``toksearch`` with two
MAST-specific signal types (``MastSignal``, ``MastImasSignal``) and parquet
metadata helpers.  For core Pipeline documentation see ``help(toksearch)``.

Invocation
==========

**No bearer token is needed** — the FAIR MAST store is publicly readable.

**1. Python-side setup** (preferred for scripts and notebooks)::

    from toksearch_mast import setup_environment
    setup_environment()          # sets MAST_ZARR_* and MAST_CATALOG_* vars

    # Or specify the device explicitly (useful when multiple devices are
    # installed in the same environment):
    setup_environment(device="mast")

**2. CLI wrapper** (preferred when launching a subprocess)::

    fdp run python <script.py>

Both routes apply the same defaults: ``MAST_ZARR_BASE_URL``,
``MAST_ZARR_PROTOCOL``, ``MAST_ZARR_ENDPOINT``, ``MAST_ZARR_FILE_NAME_FORMAT``,
``MAST_CATALOG_URL``, ``MAST_CATALOG_SHOTS_PATH``, and
``MAST_CATALOG_SIGNALS_PATH`` — all read from the ``mast`` device catalog.

Imports
=======

::

    from toksearch import Pipeline
    from toksearch_mast import MastSignal       # group/signal path
    from toksearch_mast import MastImasSignal   # IMAS path access
    from toksearch_mast import list_shots, list_signals   # parquet metadata
    from toksearch_mast import list_imas_paths            # IMAS path discovery

Import ``MastSignal`` and ``MastImasSignal`` from ``toksearch_mast``, not
``toksearch``.

MastSignal
==========

Fetches a FAIR MAST level-2 signal by its ``'group/signal'`` path into the
Zarr store.  FAIR MAST stores time in seconds, but ``times`` is returned in
**milliseconds** by default to match the toksearch convention (DIII-D/PtData);
pass ``time_in_ms=False`` for native seconds::

    sig = MastSignal("summary/ip")
    result = sig.fetch(30420)
    # result: {'data': ndarray, 'times': ndarray (ms), 'units': dict}

Constructor::

    MastSignal(treepath, dims=('times',), fetch_units=True,
               base_url=None, protocol=None, endpoint=None, time_in_ms=True)

- ``treepath``: ``'group/signal'``, e.g. ``'summary/ip'``,
  ``'magnetics/ip'``, ``'thomson_scattering/te'``.
- ``dims``: dimension names mapped onto the stored array's dimensions in
  order.  Default ``('times',)`` renames the store's first (time) axis to
  the toksearch convention.  Override for multi-dim signals, e.g.
  ``dims=('times', 'radius')``.
- ``fetch_units``: include a ``'units'`` dict in the result.  Default True.
- ``base_url``, ``protocol``, ``endpoint``: explicit overrides; default to
  the ``MAST_ZARR_*`` environment variables set by the catalog.

Connection details come from the ``mast`` device catalog
(``s3://mast/level2/shots/{shot}.zarr`` on STFC Echo S3, accessed anon via
fsspec/s3fs with ``asynchronous=True``).

MastImasSignal
==============

Fetches a FAIR MAST level-2 signal by its full IMAS path.  FAIR MAST level-2
is IMAS-native: each diagnostic group is an IMAS IDS and every Zarr variable
carries its IMAS path in ``attrs['imas']``.  ``MastImasSignal`` resolves that
attribute — no ``imas_composer`` needed.  This is the MAST analogue of
``toksearch_d3d.ImasSignal`` (``D3dImasSignal``)::

    sig = MastImasSignal("summary.global_quantities.ip")
    result = sig.fetch(30420)
    # result: {'data': ndarray, 'times': ndarray (ms), 'units': dict}

Constructor::

    MastImasSignal(imas_path, dims=('times',), fetch_units=True,
                   base_url=None, protocol=None, endpoint=None)

- ``imas_path``: full IMAS path string, e.g.
  ``'summary.global_quantities.ip'``.  The IDS (first dotted component)
  is used as the Zarr group.
- Other parameters identical to ``MastSignal``.

If the path is not found in the group, ``MastImasSignal.gather()`` raises
``ValueError`` listing all available IMAS paths in that IDS so you can
quickly discover the correct spelling.

Common IMAS paths::

    summary.global_quantities.ip
    summary.global_quantities.b_field_tor_vacuum_r
    equilibrium.time_slice.global_quantities.ip
    equilibrium.time_slice.global_quantities.beta_normal
    magnetics.ip.data
    thomson_scattering.channel.t_e.data
    thomson_scattering.channel.n_e.data
    charge_exchange.channel.t_i.data

Metadata / Discovery
====================

**Shot list** (FAIR MAST parquet catalog at mastapp.site)::

    from toksearch_mast import list_shots
    shots_df = list_shots()
    # DataFrame: shot_id, timestamp, campaign, …

**Signals for a shot**::

    from toksearch_mast import list_signals
    sigs_df = list_signals(30420)

**IMAS paths for a shot** (scans Zarr groups, one open per group)::

    from toksearch_mast import list_imas_paths
    df = list_imas_paths(30420)              # all IDS groups
    df = list_imas_paths(30420, ids='summary')   # one IDS only (faster)
    # DataFrame columns: imas, ids, variable, units, uda_name

Available Level-2 Diagnostic Groups
====================================

IMAS IDS-named groups (usable directly as the first component of an IMAS
path or as the ``group`` in a ``MastSignal`` path):

=======================  =====================================================
Group / IDS              Contents
=======================  =====================================================
summary                  Global scalar quantities (ip, Bt, stored energy …)
equilibrium              Equilibrium reconstruction (profiles, global quants)
magnetics                Magnetic diagnostics (Rogowski, flux loops, ip)
thomson_scattering       Thomson scattering (Te, ne, pressure)
charge_exchange          Charge-exchange recombination spectroscopy (Ti, vt)
interferometer           Far-infrared interferometer (ne line integrals)
pf_active                Poloidal-field coil currents and voltages
soft_x_rays              Soft X-ray bolometry / camera arrays
spectrometer_visible     Visible spectroscopy diagnostics
wall                     Wall / limiter geometry
=======================  =====================================================

Non-IDS groups also present in some shots:
``gas_injection``, ``pf_passive``, ``pulse_schedule``.

Data Access Facts
=================

- Per-shot Zarr store: ``s3://mast/level2/shots/{shot}.zarr`` on STFC Echo S3
  (``https://s3.echo.stfc.ac.uk``).
- Anonymous access — no token or credentials required.
- Read via fsspec/s3fs with ``asynchronous=True`` (required for zarr's
  FsspecStore; avoids event-loop teardown warnings under Pipeline
  multiprocessing).
- Parquet metadata catalog: ``https://mastapp.site``.

Example
=======

Fetch plasma current for a single shot::

    from toksearch import Pipeline
    from toksearch_mast import MastSignal, setup_environment

    setup_environment()

    shots = [30420]
    pipeline = Pipeline(shots)
    pipeline.fetch('ip', MastSignal('summary/ip'))
    pipeline.keep('ip')
    results = pipeline.compute_serial()

    rec = results[0]
    import numpy as np
    print("Peak Ip:", np.nanmax(np.abs(rec.get('ip', {}).get('data', []))))

For parallel retrieval over many shots use ``compute_multiprocessing``::

    results = pipeline.compute_multiprocessing(num_workers=8)
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

__llm_description__ = (
    "toksearch_mast - MAST/MAST-U signal classes (MastSignal, MastImasSignal) "
    "via the public FAIR MAST Zarr dataset; data access through the `fdp` CLI"
)
