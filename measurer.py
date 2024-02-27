#!/usr/bin/env python
"""Gouge flute measuring tool.

Matplotlib image tutorial:
https://matplotlib.org/stable/tutorials/images.html
"""

import argparse
import numpy
import math
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter, MultipleLocator
import logging
from PIL import Image
import sys
import time

from util import format_inches
from measurer_ui import setup_ui


class Display(object):
    """Class to plot gouge end photo and measure on that."""

    def __init__(self, image_file=None):
        """Initialize Plotter object."""
        # Load image
        self.img = numpy.asarray(Image.open(image_file))
        self.fig = None
        # Bar cicle. Start with center at middle of image, diameter is 80%
        # of the image width
        (width, height, bits) = self.img.shape
        self.bar_center_x = width // 2
        self.bar_center_y = height // 2
        self.bar_radius = int(min(width, height) * 0.4)

    def make_plot(self):
        """Create or refresh the interactive matplotlib plot.
        """
        #if self.fig is not None:
        #    self.fig.clear()
        plt.clf()
        #self.fig.canvas.draw()
        x = [200, 500]
        y = [300, 100]
        plt.plot(x, y, color="red", linewidth=1)
        print(self.bar_center_x, self.bar_center_y)
        circle1 = plt.Circle((self.bar_center_x, self.bar_center_y), self.bar_radius, color='y',linewidth=2, fill=False)
        plt.gca().add_patch(circle1)
        self.fig = plt.imshow(self.img)


p = argparse.ArgumentParser()
p.add_argument("-v", "--verbosity", action="count", default=0)
p.add_argument("-i", "--image", action="store", default="flute_photos/robust_1_2_2022.jpg",
               help="File name of image to load")
args = p.parse_args()

# Logging
logging.basicConfig(level=(logging.WARN if args.verbosity == 0 else (
                           logging.INFO if args.verbosity == 1 else
                           logging.DEBUG)))

# Draw picture...
#fig = plt.figure(figsize=(6, 6), layout="constrained")
display = Display(image_file=args.image)

# Set up interactive mode
display.make_plot()
setup_ui(plt.gcf(), display)
plt.show()
