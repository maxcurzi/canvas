#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="invaders",
    version="0.0.5",
    description="Space Invaders Clone for Canvas",
    author="Max Curzi",
    author_email="massimiliano.curzi@gmail.com",
    url="https://github.com/maxcurzi/canvas-game-invaders",
    package_data={"invaders": ["*.png", "assets/*.png", "**/*.png"]},
    include_package_data=True,
    install_requires=[],
    packages=find_packages(exclude=["ez_setup", "tests", "tests.*"]),
)
