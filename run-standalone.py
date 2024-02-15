#!/usr/bin/env python
"""Model turning gouge shape."""

from gouge import Gouge
from plotter import Plotter
from standalone_ui import setup_ui

import argparse
import matplotlib.pyplot as plt
import numpy
import logging
import sys
import time

p = argparse.ArgumentParser()
p.add_argument("-n", "--nose-angle", type=float, default=40.0)
p.add_argument("-v", "--verbosity", action="count", default=0)
args = p.parse_args()

# Logging
logging.basicConfig(level=(logging.WARN if args.verbosity == 0 else (
                           logging.INFO if args.verbosity == 1 else
                           logging.DEBUG)))

# Load gouge design
gouge = Gouge()
if args.nose_angle:
    gouge.set_nose_angle(args.nose_angle)
gouge.set_channel_parabola()
gouge.set_profile_flat()
gouge.solve()

# Draw picture...
fig = plt.figure(figsize=(6, 6), layout="constrained")
plotter = Plotter(fig=fig, gouge=gouge, view="profile")

# Set up interactive mode
plotter.make_plot()
setup_ui(fig, plotter)
plt.show()
