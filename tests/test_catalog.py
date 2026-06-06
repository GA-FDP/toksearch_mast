"""mast.yaml is discoverable and valid via the fdp catalog."""


def test_mast_yaml_loads_via_fdp_schema():
    from fdp_schema import load_tokamak
    from toksearch_mast.data import mast_yaml
    t = load_tokamak(mast_yaml)
    assert t.name == "mast"
    kinds = {l.kind for l in t.locators}
    assert kinds == {"zarr_store", "http_catalog"}


def test_mast_in_fdp_catalog():
    from fdp.catalog import catalog
    assert "mast" in catalog
    handle = catalog["mast"]
    zr = handle.locator("zarr_store", "main")
    assert zr.shot_url(30421) == "s3://mast/level2/shots/30421.zarr"
