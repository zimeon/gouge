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
p.add_argument('-s', '--sections', action='store_true',
               help='Show sections only')
p.add_argument('--scale-to-length', type=float, default=None,
               help='Scale length to given outside length (inches)')
p.add_argument('--scale-to-beam', type=float, default=None,
               help='Scale width to given outside beam (inches)')
p.add_argument('--scale-to-depth', type=float, default=None,
               help='Scale center depth to given outside depth (inches)')
p.add_argument('--add-breadths-at-height', type=float, nargs='*',
               help='Add interpolated breadths at given height to every appropriate station')
p.add_argument('--set-stations', action='store_true',
               help='Set new station positions')
p.add_argument('--start-station-pos', type=float, default=6.0,
               help="First (stern) station position for --set-stations")
p.add_argument('--station-sep', type=float, default=12.0,
               help="Station separation for --set-stations")
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
if (args.scale_to_length):
    gouge.offset_scale_length(0.0, args.scale_to_length / gouge.outside_length)
if (args.scale_to_beam):
    gouge.scale_width(args.scale_to_beam / gouge.outside_max_beam)
if (args.scale_to_depth):
    gouge.offset_scale_vertical(scale=(args.scale_to_depth / gouge.outside_center_depth))

if (args.add_breadths_at_height is not None):
    for height in args.add_breadths_at_height:
        gouge.add_breadths_at_height(height)

if (args.set_stations):
    stations = numpy.arange(args.start_station_pos,
                            (gouge.min_max_length(round_out=False)[1] - 6.0),
                            args.station_sep)
    heights = [1.0, 2.0, 3.0, 4.5, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0]
    print("Calling set_stations(\n  stations=" + str(stations) +
          ",\n  height=" + str(heights) + " )")
    gouge.set_stations(stations, heights)

# Draw picture...
fig = plt.figure(figsize=(15, 9))
plotter = Plotter(fig=fig, hull=gouge)
if (args.pdf):
    plotter.show_waterline = False
    plotter.write_plans('plans.pdf')
    exit()
plotter.view = 'sections' if args.sections else None
plotter.make_plot()

# Attach UI to figure and plotter
setup_ui(fig, plotter)

# Use standard interaction mode
plt.show()
