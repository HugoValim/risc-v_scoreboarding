#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages


def readme():
    with open("README.rst") as f:
        return f.read()


setup(
    name="scoreboarding-sim",
    version="0.0.1",
    description="DThis is a simulator for out of order execution of RISC-V assembly",
    long_description=readme(),
    author="Hugo Campos",
    author_email="hugohevalica@gmail.com",
    url="https://github.com/HugoValim/risc-v_scoreboarding",
    install_requires=["pandas", "tabulate"],
    packages=find_packages(where=".", exclude=["test", "test.*", "tests"]),
    entry_points={
        "console_scripts": [
            "scoreboarding_sim = sbsim.cli_script.run:main",
        ],
    },
)
