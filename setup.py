#!/usr/bin/python

from distutils.core import setup

from yardbird.version import sdist_ver

setup(
    name="yardbird",
    version=sdist_ver(),
    description="YardBird, a Django-based chat bot system.",
    author="Nick Moffitt",
    author_email="nick@zork.net",
    license="GPL",
    url="http://zork.net/~nick/yardbird/",
    packages=['yardbird', 'yardbird.utils', 'yardbird.contrib',
        'yardbird.management', 'yardbird.management.commands'],
    package_data={'yardbird': ['templates/*.irc']},
)
