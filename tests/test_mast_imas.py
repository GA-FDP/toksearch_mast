import os
from unittest import mock
import numpy as np
import xarray as xr
import pytest
from toksearch_mast import MastImasSignal


def _fake_summary_ds():
    # mimics a FAIR MAST 'summary' group: vars carry attrs['imas']
    time = np.array([0.0, 0.1, 0.2])
    ip = xr.DataArray(np.array([1.0, 2.0, 3.0]), dims=("time",),
                      coords={"time": time},
                      attrs={"imas": "summary.global_quantities.ip", "units": "A"})
    ne = xr.DataArray(np.array([4.0, 5.0, 6.0]), dims=("time",),
                      coords={"time": time},
                      attrs={"imas": "summary.line_average.n_e.value", "units": "1 / m ** 3"})
    ds = xr.Dataset({"ip": ip, "line_average_n_e": ne})
    ds["time"].attrs["units"] = "s"
    return ds


def _env():
    return {
        "MAST_ZARR_BASE_URL": "s3://mast/level2/shots",
        "MAST_ZARR_PROTOCOL": "s3",
        "MAST_ZARR_ENDPOINT": "https://s3.echo.stfc.ac.uk",
        "MAST_ZARR_FILE_NAME_FORMAT": "{shot}.zarr",
    }


def test_ids_parsed_from_path():
    with mock.patch.dict(os.environ, _env(), clear=False):
        sig = MastImasSignal("summary.global_quantities.ip")
    assert sig.ids == "summary"
    assert sig.imas_path == "summary.global_quantities.ip"


def test_resolves_variable_by_imas_attr():
    with mock.patch.dict(os.environ, _env(), clear=False):
        sig = MastImasSignal("summary.global_quantities.ip")
        with mock.patch("toksearch_mast.signal.imas.xr.open_zarr",
                        return_value=_fake_summary_ds()) as oz:
            result = sig.gather(30421)
    # opened the correct IDS/group
    assert oz.call_args.kwargs.get("group") == "summary"
    assert list(result["data"]) == [1.0, 2.0, 3.0]      # the 'ip' variable
    assert "times" in result
    # default: store seconds [0, 0.1, 0.2] -> ms [0, 100, 200]
    assert list(result["times"]) == [0.0, 100.0, 200.0]
    assert result["units"]["data"] == "A"
    assert result["units"]["times"] == "ms"


def test_time_in_ms_false_keeps_seconds():
    with mock.patch.dict(os.environ, _env(), clear=False):
        sig = MastImasSignal("summary.global_quantities.ip", time_in_ms=False)
        with mock.patch("toksearch_mast.signal.imas.xr.open_zarr",
                        return_value=_fake_summary_ds()):
            result = sig.gather(30421)
    assert list(result["times"]) == [0.0, 0.1, 0.2]      # native seconds
    assert result["units"]["times"] == "s"


def test_no_match_raises_with_available_paths():
    with mock.patch.dict(os.environ, _env(), clear=False):
        sig = MastImasSignal("summary.does_not_exist")
        with mock.patch("toksearch_mast.signal.imas.xr.open_zarr",
                        return_value=_fake_summary_ds()):
            with pytest.raises(ValueError) as exc:
                sig.gather(30421)
    msg = str(exc.value)
    assert "summary.global_quantities.ip" in msg   # lists what IS available
