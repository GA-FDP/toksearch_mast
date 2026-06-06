# toksearch_mast

MAST / MAST-U signal classes for the TokSearch framework, backed by the
public [FAIR MAST](https://mastapp.site) Zarr dataset. Registers `mast` as
an FDP device via the `fdp_schema.catalogs` entry point.

```python
from toksearch import Pipeline
from toksearch_mast import MastSignal, list_shots, setup_environment

setup_environment()  # device="mast"
pipe = Pipeline([30421])
pipe.fetch("ip", MastSignal("summary/ip"))
for rec in pipe.compute_serial():
    print(rec["ip"]["data"].shape)
```
