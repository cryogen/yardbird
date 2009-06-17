#!/usr/bin/python

from distutils.core import setup

from yardbird.bot import VERSION

setup(
    name="YardBird",
    version=VERSION,
    description="YardBird, a Django-based chat bot system.",
    author="Nick Moffitt",
    author_email="nick@zork.net",
    url="http://zork.net/~nick/yardbird/",
    packages=['yardbird'],
)
