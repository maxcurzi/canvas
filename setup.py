#!/usr/bin/env python
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="place",
    version="0.0.1",
    description="Reddit Place Clone for Canvas",
    author="Max Curzi",
    author_email="massimiliano.curzi@gmail.com",
    url="https://github.com/maxcurzi/canvas-place",
    install_requires=requirements,
    packages=find_packages(exclude=["ez_setup", "tests", "tests.*"]),
)
