# Copyright 2024 General Atomics
# Licensed under the Apache License, Version 2.0.

from setuptools import setup, find_packages
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import versioneer

setup(
    name="toksearch_mast",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(include=["toksearch_mast", "toksearch_mast.*"]),
    include_package_data=True,
    zip_safe=False,
)
