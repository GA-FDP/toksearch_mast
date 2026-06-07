# Copyright 2024 General Atomics
# Licensed under the Apache License, Version 2.0.

"""toksearch_mast.llm -- contributor module for toksearch.llm.

Exposes ``skills_path``, the directory of MAST SKILL.md files, registered
via the ``toksearch.llm.skills`` entry point.
"""

from pathlib import Path

skills_path: Path = Path(__file__).parent.parent / "skills"

__all__ = ["skills_path"]
