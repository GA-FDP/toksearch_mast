# Copyright 2024 General Atomics
# Licensed under the Apache License, Version 2.0.

"""IMAS-path access to FAIR MAST level-2 data.

FAIR MAST level-2 stores are IMAS-structured: each diagnostic group is an
IMAS IDS, and every variable carries its full IMAS path in attrs['imas'].
``MastImasSignal`` resolves an IMAS path to the matching variable and
fetches it. It is the MAST analogue of ``toksearch_d3d.D3dImasSignal`` /
``ImasSignal``, but by direct attribute lookup rather than imas_composer
composition (FAIR MAST is already IMAS-native).
"""

import os
import zarr
import xarray as xr
from toksearch import Signal

from .mast import _make_fs


def _open_shot_group(base_url, file_name_format, protocol, endpoint, shot, group):
    """Open one IDS group of a shot's level-2 Zarr store as an xarray Dataset."""
    fs = _make_fs(protocol, endpoint)
    fname = file_name_format.format(shot=shot)
    shot_url = f"{base_url}/{fname}"
    _proto, file_path = str(shot_url).split("://", maxsplit=1)
    store = zarr.storage.FsspecStore(fs=fs, path=file_path)
    return xr.open_zarr(store, group=group)


class MastImasSignal(Signal):
    """Fetch a FAIR MAST level-2 signal by its IMAS path.

    Args:
        imas_path: full IMAS path, e.g. ``'summary.global_quantities.ip'``.
            The IDS (group) is the first dotted component.
        dims: output dim names mapped onto the variable's dims, in order.
            Default ``('times',)`` renames the store's first (time) dim to
            ``times`` (toksearch convention). Time values are in seconds.
        fetch_units: include a ``'units'`` entry. Default True.
        base_url/protocol/endpoint: explicit overrides; default to the
            ``MAST_ZARR_*`` environment variables.
    """

    def __init__(self, imas_path, dims=("times",), fetch_units=True,
                 base_url=None, protocol=None, endpoint=None):
        super().__init__()
        self.imas_path = imas_path
        self.ids = imas_path.split(".")[0]
        self.with_units = fetch_units
        self.base_url = base_url or os.environ["MAST_ZARR_BASE_URL"]
        self.protocol = protocol or os.environ.get("MAST_ZARR_PROTOCOL", "s3")
        self.endpoint = endpoint or os.environ.get("MAST_ZARR_ENDPOINT")
        self.file_name_format = os.environ.get(
            "MAST_ZARR_FILE_NAME_FORMAT", "{shot}.zarr")
        self.set_dims(dims)

    def gather(self, shot):
        ds = _open_shot_group(self.base_url, self.file_name_format,
                              self.protocol, self.endpoint, shot, self.ids)
        matches = [name for name in ds.data_vars
                   if ds[name].attrs.get("imas") == self.imas_path]
        if not matches:
            available = sorted(
                ds[n].attrs["imas"] for n in ds.data_vars
                if "imas" in ds[n].attrs)
            raise ValueError(
                f"No variable in IDS {self.ids!r} has imas path "
                f"{self.imas_path!r}. Available in this group: {available}"
            )
        signal = ds[matches[0]]
        result = dict(data=signal.values)
        for new_dim, dim in zip(self.dims, signal.sizes.keys()):
            if dim in ds:
                result[new_dim] = ds[dim].values
        if self.with_units:
            units = {"data": signal.attrs.get("units", "")}
            for new_dim, dim in zip(self.dims, signal.sizes.keys()):
                if dim in ds:
                    units[new_dim] = ds[dim].attrs.get("units", "")
            result["units"] = units
        return result

    def cleanup_shot(self, shot):
        pass

    def cleanup(self):
        pass


def list_imas_paths(shot, ids=None):
    """List the IMAS paths available for ``shot`` as a pandas DataFrame.

    Columns: ``imas``, ``ids``, ``variable``, ``units``, ``uda_name``.
    If ``ids`` is given, only that IDS group is scanned; otherwise all
    groups in the shot store are scanned (one open per group — slower).
    """
    import pandas as pd

    base_url = os.environ["MAST_ZARR_BASE_URL"]
    protocol = os.environ.get("MAST_ZARR_PROTOCOL", "s3")
    endpoint = os.environ.get("MAST_ZARR_ENDPOINT")
    fname = os.environ.get("MAST_ZARR_FILE_NAME_FORMAT", "{shot}.zarr")

    if ids is not None:
        groups = [ids]
    else:
        fs = _make_fs(protocol, endpoint)
        shot_url = f"{base_url}/{fname.format(shot=shot)}"
        _proto, file_path = str(shot_url).split("://", maxsplit=1)
        root = zarr.open_group(zarr.storage.FsspecStore(fs=fs, path=file_path),
                               mode="r")
        groups = sorted(root.group_keys())

    rows = []
    for group in groups:
        ds = _open_shot_group(base_url, fname, protocol, endpoint, shot, group)
        for name in ds.data_vars:
            attrs = ds[name].attrs
            if "imas" in attrs:
                rows.append({
                    "imas": attrs["imas"],
                    "ids": group,
                    "variable": name,
                    "units": attrs.get("units", ""),
                    "uda_name": attrs.get("uda_name", ""),
                })
    return pd.DataFrame(rows, columns=["imas", "ids", "variable", "units", "uda_name"])
