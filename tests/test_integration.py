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
    # default times are in ms (toksearch convention), not native seconds:
    # shot 30421 spans ~0.7 s, so the ms magnitude is >> 1.
    assert abs(ip["times"]).max() > 1.0
    assert ip["units"]["times"] == "ms"


def test_time_in_ms_default_vs_seconds():
    setup_environment()
    ms = MastSignal("summary/ip").gather(30421)["times"]
    sec = MastSignal("summary/ip", time_in_ms=False).gather(30421)["times"]
    # same axis, 1000x scale
    assert abs(ms).max() > 1.0
    assert abs(sec).max() < 10.0
    assert abs(ms[-1] - sec[-1] * 1000.0) < 1e-6


def test_imas_path_matches_treepath():
    from toksearch_mast import MastImasSignal, MastSignal, list_imas_paths
    setup_environment()
    by_imas = MastImasSignal("summary.global_quantities.ip").gather(30421)
    by_tree = MastSignal("summary/ip").gather(30421)
    assert by_imas["data"].shape == by_tree["data"].shape
    assert by_imas["data"].shape[0] > 0
    # both default to ms
    assert by_imas["units"]["times"] == "ms"
    # discovery helper finds the same path
    df = list_imas_paths(30421, ids="summary")
    assert "summary.global_quantities.ip" in set(df["imas"])
