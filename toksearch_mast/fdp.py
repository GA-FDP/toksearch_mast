# Copyright 2024 General Atomics
# Licensed under the Apache License, Version 2.0.
"""setup_environment convenience for the MAST device."""


def setup_environment(*args, **kwargs):
    from fdp import setup_environment as _se
    kwargs.setdefault("device", "mast")
    return _se(*args, **kwargs)
