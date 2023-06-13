#!/usr/bin/env python3

from setuptools import setup, find_packages  # type:ignore
from mastko.version import __version__

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="mastko",
    version=__version__,
    entry_points={"console_scripts": ["mastko=mastko.mastko:main"]},
    packages=find_packages(),
    include_package_data=True,
    long_description=open("README.md").read(),
    python_requires=">=3.9",
    install_requires=required,
)
