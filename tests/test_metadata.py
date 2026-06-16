import os
from unittest import mock
import pytest
from toksearch_mast import list_shots, list_signals


def _env():
    return {
        "MAST_CATALOG_URL": "https://mastapp.site",
        "MAST_CATALOG_SHOTS_PATH": "parquet/level2/shots",
        "MAST_CATALOG_SIGNALS_PATH": "parquet/level2/signals",
    }


def test_list_shots_url():
    with mock.patch.dict(os.environ, _env(), clear=False):
        with mock.patch("toksearch_mast.metadata.pd.read_parquet",
                        return_value="DF") as rp:
            out = list_shots()
    assert out == "DF"
    rp.assert_called_once_with("https://mastapp.site/parquet/level2/shots")


def test_list_signals_url():
    with mock.patch.dict(os.environ, _env(), clear=False):
        with mock.patch("toksearch_mast.metadata.pd.read_parquet",
                        return_value="DF") as rp:
            list_signals(30421)
    rp.assert_called_once_with(
        "https://mastapp.site/parquet/level2/signals?shot_id=30421"
    )


def test_list_signals_without_path_raises():
    env = _env()
    del env["MAST_CATALOG_SIGNALS_PATH"]
    with mock.patch.dict(os.environ, env, clear=True):
        with pytest.raises(RuntimeError):
            list_signals(30421)


def test_list_shots_without_env_raises_actionable_error():
    # No MAST_* env at all: should point the user at setup_environment,
    # not raise a bare KeyError.
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError) as exc:
            list_shots()
    msg = str(exc.value)
    assert "setup_environment" in msg
    assert "MAST_CATALOG_URL" in msg
