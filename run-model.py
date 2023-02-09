#!/usr/bin/env python
"""Model turning gouge shape."""

from gouge import Gouge
from plotter import Plotter
from user_interface import setup_ui

import argparse
import matplotlib.pyplot as plt
import numpy
import logging
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('--pdf', action='store_true',
               help='Write PDF plans and exit')
p.add_argument("-v", "--verbosity", action="count", default=0)
p.add_argument('gouge', nargs='?', default='default.md')
args = p.parse_args()

# Logging
logging.basicConfig(level=(logging.WARN if args.verbosity == 0 else (
                           logging.INFO if args.verbosity == 1 else
                           logging.DEBUG)))

# Load gouge design
logging.warning("Loading gouge from %s..." % (args.gouge))
gouge = Gouge(args.gouge)
gouge.normalize()

# Draw picture...
fig = plt.figure(figsize=(15, 9))
plotter = Plotter(fig=fig, gouge=gouge)
if (args.pdf): # PDF and exit
    plotter.write_plans('plans.pdf')
    exit()

# Set up interactive mode
plotter.make_plot()
setup_ui(fig, plotter)
plt.show()
