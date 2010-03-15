#!/usr/bin/python
import doctest

def suite():
    return doctest.DocFileSuite('doc/spec.rst', module_relative=True,
            optionflags=doctest.ELLIPSIS)
