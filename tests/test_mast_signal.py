import os
from unittest import mock
from toksearch_mast import MastSignal


def _env(**over):
    base = {
        "MAST_ZARR_BASE_URL": "s3://mast/level2/shots",
        "MAST_ZARR_PROTOCOL": "s3",
        "MAST_ZARR_ENDPOINT": "https://s3.echo.stfc.ac.uk",
        "MAST_ZARR_FILE_NAME_FORMAT": "{shot}.zarr",
    }
    base.update(over)
    return base


def test_constructs_zarrsignal_from_env():
    with mock.patch.dict(os.environ, _env(), clear=False):
        with mock.patch(
            "toksearch_mast.signal.mast._make_fs", return_value="FS"
        ) as mk:
            sig = MastSignal("summary/ip")
    assert sig.path == "s3://mast/level2/shots"
    assert sig.treepath == "summary/ip"
    assert sig.file_name_format == "{shot}.zarr"
    assert tuple(sig.dims) == ("times",)
    assert sig.fs == "FS"
    mk.assert_called_once_with("s3", "https://s3.echo.stfc.ac.uk")


def test_explicit_overrides_win():
    # Explicit protocol="https" and base_url override the env values.
    # endpoint=None falls through the `or` in MastSignal.__init__ to the
    # env var by design, so _make_fs receives the env endpoint, not None.
    with mock.patch.dict(os.environ, _env(), clear=False):
        with mock.patch(
            "toksearch_mast.signal.mast._make_fs", return_value="FS"
        ) as mk:
            MastSignal("thomson/te", dims=("times", "radius"),
                       base_url="s3://other/path", protocol="https",
                       endpoint=None)
    mk.assert_called_once_with("https", "https://s3.echo.stfc.ac.uk")


def test_multidim_dims_passthrough():
    with mock.patch.dict(os.environ, _env(), clear=False):
        with mock.patch(
            "toksearch_mast.signal.mast._make_fs", return_value="FS"
        ):
            sig = MastSignal("thomson/te", dims=("times", "radius"))
    assert tuple(sig.dims) == ("times", "radius")
