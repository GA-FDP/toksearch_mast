import pytest
from toksearch_mast.signal.mast import _make_fs


def test_s3_anon_filesystem():
    fs = _make_fs("s3", endpoint="https://s3.echo.stfc.ac.uk")
    assert fs.anon is True

def test_https_filesystem():
    fs = _make_fs("https")
    assert fs is not None

def test_file_returns_none():
    assert _make_fs("file") is None

def test_unknown_protocol_raises():
    with pytest.raises(ValueError):
        _make_fs("ftp")
