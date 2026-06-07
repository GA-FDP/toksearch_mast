import pytest
from toksearch import Pipeline
from toksearch_mast import MastSignal, setup_environment

pytestmark = pytest.mark.integration


def test_fetch_ip_for_known_shot():
    setup_environment()
    pipe = Pipeline([30421])
    pipe.fetch("ip", MastSignal("summary/ip"))
    pipe.keep(["ip"])
    records = list(pipe.compute_serial())
    assert len(records) == 1
    ip = records[0]["ip"]
    assert ip["data"].shape[0] > 0
    assert "times" in ip
    assert ip["times"].shape[0] == ip["data"].shape[0]


def test_imas_path_matches_treepath():
    from toksearch_mast import MastImasSignal, MastSignal, list_imas_paths
    setup_environment()
    by_imas = MastImasSignal("summary.global_quantities.ip").gather(30421)
    by_tree = MastSignal("summary/ip").gather(30421)
    assert by_imas["data"].shape == by_tree["data"].shape
    assert by_imas["data"].shape[0] > 0
    # discovery helper finds the same path
    df = list_imas_paths(30421, ids="summary")
    assert "summary.global_quantities.ip" in set(df["imas"])
