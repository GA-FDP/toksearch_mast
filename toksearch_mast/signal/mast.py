# Copyright 2024 General Atomics
# Licensed under the Apache License, Version 2.0.

"""MastSignal — FAIR MAST level-2 Zarr access as a toksearch Signal."""

import os
import fsspec
from toksearch import ZarrSignal


def _make_fs(protocol, endpoint=None):
    """Build the fsspec filesystem for a zarr_store protocol.

    `asynchronous=True` is required for the s3 backend: zarr's FsspecStore
    drives the filesystem asynchronously, and without it s3fs emits a
    ZarrUserWarning plus noisy event-loop teardown errors (confirmed in the
    Phase 0 spike) — and it matters under Pipeline multiprocessing.
    """
    if protocol == "s3":
        client_kwargs = {"endpoint_url": endpoint} if endpoint else {}
        return fsspec.filesystem(
            "s3", anon=True, asynchronous=True, client_kwargs=client_kwargs
        )
    if protocol == "https":
        return fsspec.filesystem("https", asynchronous=True)
    if protocol == "file":
        return None  # ZarrSignal defaults to a local filesystem
    raise ValueError(f"Unsupported zarr protocol {protocol!r}")


def _times_to_ms(result, key="times"):
    """Convert the time axis in a gather() result from seconds (FAIR MAST's
    native unit) to milliseconds (the toksearch convention, matching
    DIII-D/PtData). No-op if ``key`` is absent. Updates the units entry too.
    """
    if key in result:
        result[key] = result[key] * 1000.0
        units = result.get("units")
        if isinstance(units, dict):
            units[key] = "ms"
    return result


class MastSignal(ZarrSignal):
    """Fetch a FAIR MAST level-2 signal as a toksearch Signal.

    Connection details default to the FDP environment populated by
    ``fdp run`` / ``setup_environment(device='mast')``: ``MAST_ZARR_BASE_URL``,
    ``MAST_ZARR_PROTOCOL``, ``MAST_ZARR_ENDPOINT``,
    ``MAST_ZARR_FILE_NAME_FORMAT``.

    Note: FAIR MAST stores time axes in **seconds**, but by default this
    signal returns ``times`` in **milliseconds** to match the toksearch
    convention (DIII-D/PtData). Pass ``time_in_ms=False`` to keep the
    store's native seconds.

    Args:
        treepath: ``'group/signal'``, e.g. ``'summary/ip'``.
        dims: dimension names mapped onto the stored signal's dimensions,
            in order. Default ``('times',)`` renames the store's first
            (time) dimension to ``times`` (toksearch convention). Override
            for multi-dim signals, e.g. ``('times', 'radius')``.
        fetch_units: include a ``'units'`` entry. Default True.
        time_in_ms: convert the ``times`` axis from the store's seconds to
            milliseconds. Default True.
        base_url, protocol, endpoint: explicit overrides; default to the
            ``MAST_ZARR_*`` environment variables.
    """

    def __init__(self, treepath, dims=("times",), fetch_units=True,
                 base_url=None, protocol=None, endpoint=None,
                 time_in_ms=True):
        base_url = base_url or os.environ["MAST_ZARR_BASE_URL"]
        protocol = protocol or os.environ.get("MAST_ZARR_PROTOCOL", "s3")
        endpoint = endpoint or os.environ.get("MAST_ZARR_ENDPOINT")
        fname = os.environ.get("MAST_ZARR_FILE_NAME_FORMAT", "{shot}.zarr")
        self.time_in_ms = time_in_ms
        super().__init__(
            path=base_url,
            treepath=treepath,
            dims=dims,
            fetch_units=fetch_units,
            file_name_format=fname,
            fs=_make_fs(protocol, endpoint),
        )

    def gather(self, shot):
        result = super().gather(shot)
        if self.time_in_ms:
            _times_to_ms(result)
        return result
