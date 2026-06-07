---
name: toksearch-mast-imas
description: IMAS-path access to FAIR MAST — MastImasSignal and list_imas_paths; level-2 groups are IMAS IDSs and variables carry imas-path attributes
user-invocable: false
license: Apache-2.0
compatibility: Claude Code
metadata:
  author: GA-FDP
  version: "1.0"
  url: https://github.com/GA-FDP/toksearch_mast
---

# TokSearch MAST IMAS access

The canonical documentation lives in the package docstring.

Access it with: `help(toksearch_mast)` and `help(toksearch_mast.MastImasSignal)`

FAIR MAST level-2 is IMAS-native: each diagnostic group is an IMAS IDS and
every variable carries its full IMAS path in `attrs['imas']`.
`MastImasSignal("summary.global_quantities.ip")` resolves an IMAS path to the
matching variable; `list_imas_paths(shot, ids=None)` discovers the available
IMAS paths for a shot. This is the MAST analogue of
`toksearch_d3d.D3dImasSignal` — direct attribute lookup, no `imas_composer`
needed.
