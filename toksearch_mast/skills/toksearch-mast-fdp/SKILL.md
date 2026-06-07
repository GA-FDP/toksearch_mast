---
name: toksearch-mast-fdp
description: MAST/MAST-U data access via FAIR MAST — the mast FDP device, MastSignal, list_shots/list_signals, and the public Zarr-on-S3 store
user-invocable: false
license: Apache-2.0
compatibility: Claude Code
metadata:
  author: GA-FDP
  version: "1.0"
  url: https://github.com/GA-FDP/toksearch_mast
---

# TokSearch MAST (FAIR MAST)

The canonical toksearch_mast documentation lives in the package docstring.

Access it with: `help(toksearch_mast)` or `python -c "help(toksearch_mast)"`

Covers: the `mast` FDP device (`fdp run` / `setup_environment(device="mast")`),
`MastSignal("group/signal")`, shot/metadata helpers (`list_shots`,
`list_signals`), the public FAIR MAST Zarr store on STFC Echo S3 (no token),
available level-2 diagnostic groups, and the seconds (not milliseconds) time
convention.
