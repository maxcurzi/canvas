#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="canvas-invaders",
    version="0.0.1",
    description="Space Invaders Clone for Canvas",
    author="Max Curzi",
    author_email="massimiliano.curzi@gmail.com",
    url="https://github.com/maxcurzi/canvas-game-invaders",
    include_package_data=True,
    package_data={"": ["*.png"]},
    install_requires=[],
)
