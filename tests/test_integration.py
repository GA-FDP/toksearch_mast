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
