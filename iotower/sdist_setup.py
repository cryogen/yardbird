#!/usr/bin/python
"""This is a gross hack required only because of the way I rolled the
iotower development into the main yardbird branch.  It is only run from
the bzr repo, and does not get included into the sdist tarball."""

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
    package_dir={'..': ''},  # Yeah, that's the gross hack right there.
    packages=['iotower'],
    script_name='setup.py', # Put the real setup.py in the tarball
)


