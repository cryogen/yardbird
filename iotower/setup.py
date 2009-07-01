#!/usr/bin/python

from distutils.core import setup

from version import sdist_ver

setup(
    name="iotower",
    version=sdist_ver(),
    description="IOTower, a Yardbird replacement for Infobot.",
    author="Nick Moffitt",
    author_email="nick@zork.net",
    license="GPL",
    url="http://zork.net/~nick/yardbird/iotower/",
    package_dir={'iotower': '.'},
    packages=['iotower'],
    package_data={'iotower': ['templates/*.irc']},
)


