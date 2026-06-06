# Copyright 2024 General Atomics
# Licensed under the Apache License, Version 2.0.

"""Shot/signal metadata helpers for FAIR MAST.

Read the FAIR MAST parquet catalog endpoints described by the device's
http_catalog locator (exposed via MAST_CATALOG_* env vars set by
fdp.setup_environment / fdp run). The MAST analogue of D3D's
connect_d3drdb().
"""

import os
import pandas as pd


def _catalog_url() -> str:
    return os.environ["MAST_CATALOG_URL"]


def list_shots() -> pd.DataFrame:
    """Return the FAIR MAST shot metadata table as a DataFrame."""
    url = f"{_catalog_url()}/{os.environ['MAST_CATALOG_SHOTS_PATH']}"
    return pd.read_parquet(url)


def list_signals(shot) -> pd.DataFrame:
    """Return the signals available for `shot` as a DataFrame."""
    path = os.environ.get("MAST_CATALOG_SIGNALS_PATH")
    if not path:
        raise RuntimeError(
            "MAST_CATALOG_SIGNALS_PATH is not set; run under fdp / "
            "setup_environment(device='mast') with a signals_path in mast.yaml"
        )
    url = f"{_catalog_url()}/{path}?shot_id={shot}"
    return pd.read_parquet(url)
