#!/usr/bin/python

from distutils.core import setup

from iotower.version import sdist_ver

setup(
    name="iotower",
    version=sdist_ver(),
    description="IOTower, a Yardbird replacement for Infobot.",
    author="Nick Moffitt",
    author_email="nick@zork.net",
    license="GPL",
    url="http://zork.net/~nick/yardbird/iotower/",
    packages=['iotower'],
)


