import os
import unittest
from toksearch_mast import setup_environment


# Keys that setup_environment may write for the mast device and generic keys
# that could bleed across tests if not isolated.
_MAST_KEYS = (
    "MAST_ZARR_BASE_URL",
    "MAST_ZARR_PROTOCOL",
    "MAST_ZARR_ENDPOINT",
    "MAST_ZARR_FILE_NAME_FORMAT",
    "MAST_CATALOG_URL",
    "MAST_CATALOG_SHOTS_PATH",
    "MAST_CATALOG_SIGNALS_PATH",
)
_GENERIC_KEYS = (
    "BEARER_TOKEN",
    "XRDCP_ALLOW_HTTP",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "FDP_DEFAULT_DEVICE",
)


class TestSetupEnvironmentMastContract(unittest.TestCase):
    """Catalog → env → signal contract: setup_environment('mast') populates
    exactly the env vars that MastSignal/list_shots consume, and does NOT set
    XRootD or auth vars appropriate only for Pelican-backed devices."""

    def setUp(self):
        # Save and clear all keys we intend to assert on so that stale values
        # from earlier tests cannot produce false positives or false negatives.
        self._saved = {}
        for k in _MAST_KEYS + _GENERIC_KEYS:
            self._saved[k] = os.environ.pop(k, None)

    def tearDown(self):
        # Restore original values (or remove keys that were absent).
        for k, v in self._saved.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    def test_setup_environment_populates_mast_contract(self):
        # toksearch_mast is the only device installed in this env, so
        # device auto-detects to 'mast'.
        setup_environment()
        assert os.environ["MAST_ZARR_BASE_URL"] == "s3://mast/level2/shots"
        assert os.environ["MAST_ZARR_PROTOCOL"] == "s3"
        assert os.environ["MAST_ZARR_ENDPOINT"] == "https://s3.echo.stfc.ac.uk"
        assert os.environ["MAST_CATALOG_URL"] == "https://mastapp.site"
        # Public device: no token, no XRootD plumbing.
        assert "BEARER_TOKEN" not in os.environ
        assert "XRDCP_ALLOW_HTTP" not in os.environ
