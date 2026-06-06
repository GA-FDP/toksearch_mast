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


class MastSignal(ZarrSignal):
    """Fetch a FAIR MAST level-2 signal as a toksearch Signal.

    Connection details default to the FDP environment populated by
    ``fdp run`` / ``setup_environment(device='mast')``: ``MAST_ZARR_BASE_URL``,
    ``MAST_ZARR_PROTOCOL``, ``MAST_ZARR_ENDPOINT``,
    ``MAST_ZARR_FILE_NAME_FORMAT``.

    Note: FAIR MAST time axes are in **seconds** (unlike DIII-D's
    milliseconds); the returned ``times`` array is in seconds.

    Args:
        treepath: ``'group/signal'``, e.g. ``'summary/ip'``.
        dims: dimension names mapped onto the stored signal's dimensions,
            in order. Default ``('times',)`` renames the store's first
            (time) dimension to ``times`` (toksearch convention). Override
            for multi-dim signals, e.g. ``('times', 'radius')``.
        fetch_units: include a ``'units'`` entry. Default True.
        base_url, protocol, endpoint: explicit overrides; default to the
            ``MAST_ZARR_*`` environment variables.
    """

    def __init__(self, treepath, dims=("times",), fetch_units=True,
                 base_url=None, protocol=None, endpoint=None):
        base_url = base_url or os.environ["MAST_ZARR_BASE_URL"]
        protocol = protocol or os.environ.get("MAST_ZARR_PROTOCOL", "s3")
        endpoint = endpoint or os.environ.get("MAST_ZARR_ENDPOINT")
        fname = os.environ.get("MAST_ZARR_FILE_NAME_FORMAT", "{shot}.zarr")
        super().__init__(
            path=base_url,
            treepath=treepath,
            dims=dims,
            fetch_units=fetch_units,
            file_name_format=fname,
            fs=_make_fs(protocol, endpoint),
        )
