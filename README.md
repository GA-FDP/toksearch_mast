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

## Releasing

Two tags, one version.

```bash
git tag staging-X.Y.Z && git push origin staging-X.Y.Z   # builds, uploads to staging
git tag release-X.Y.Z && git push origin release-X.Y.Z   # promotes those bytes to main
```

`staging-X.Y.Z` builds the package and uploads it to `ga-fdp/label/staging`,
where nothing installs it by default. `release-X.Y.Z` performs **no build**:
it relabels the artifact that already exists, so what users install is
byte-identical to what was verified. A rebuild on promotion would destroy
the only property promotion provides.

`tag_prefix` is `staging-`, so versioneer reads the staging tag and the
*version* is identical across both events — only the prefix differs.

Two things that will bite otherwise:

- **Tag a fresh commit.** `git describe` picks one tag when a commit carries
  several, so a second staging tag on the same commit builds the *earlier*
  version. The build refuses when what it produced does not match the tag.
- **Do not cut `release-*` by hand once fdp-core drives promotion.** It is
  cut by the bless job that verified the set, which is what stops a release
  tag asserting something nobody checked.

See `fdp-core/docs/specs/2026-09-15-staging-and-promotion.md`.
