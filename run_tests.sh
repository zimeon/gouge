#!/bin/bash
#
# Tests will not run with plain py.test as need to run matplotlib
# as a framework (with pythonw)
pythonw -m unittest test*
