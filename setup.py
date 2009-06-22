#!/usr/bin/python

from distutils.core import setup

from yardbird.version import VERSION

setup(
    name="yardbird",
    version=VERSION.replace('-','').lower(),
    description="YardBird, a Django-based chat bot system.",
    author="Nick Moffitt",
    author_email="nick@zork.net",
    license="BSD",
    url="http://zork.net/~nick/yardbird/",
    packages=['yardbird', 'yardbird.management', 'yardbird.management.commands'],
)
