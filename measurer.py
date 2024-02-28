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
import os.path
from PIL import Image
import re
import sys
import time

from util import format_inches
from measurer_ui import setup_ui


def get_ax_size(fig, ax):
    """Returns the size of a given axes in pixels

    Args:
       fig (matplotlib figure) - the figure to which the axes belong
       ax (matplotlib axes) - the axes to return size for
    """
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width = bbox.width * fig.dpi
    height = bbox.height * fig.dpi
    return width, height


def get_extent(fig, ax, img, xsize, xpos, ypos):
    '''
    Calculate extent image on a given axes whilst maintaining its aspect ratio

    Args:
        fig (matplotlib figure)
        ax (matplotlib axes)
        img (numpy.ndarray): image data
        xsize (float): size of the x-dimension of object given as fraction of the axes length
        xpos (float): x-coordinate of image center in axes coordinates
        ypos (float): y-coordinate of image center in axes coordinates

    Returns:
        xmin, xmax, ymin, ymax (float): min and max x & y specifying image extent in axes coodinates

    '''
    img_aspect = img.shape[0] / img.shape[1]
    xrange = ax.get_xlim()[1] - ax.get_xlim()[0]
    yrange = ax.get_ylim()[1] - ax.get_ylim()[0]

    ysize = xsize * img_aspect * get_ax_size(fig,ax)[0] / get_ax_size(fig,ax)[1]

    xsize *= xrange
    ysize *= yrange

    xmin = xpos - xsize/2
    ymin = ypos - ysize/2
    return xmin, xmin + xsize, ymin, ymin + ysize


class InteractiveDisplay(object):
    """Class to plot gouge end photo and measure on that."""

    def __init__(self, image_file=None, bar_size=None):
        """Initialize Plotter object."""
        # Load image
        self.img = numpy.asarray(Image.open(image_file))
        self.fig = None
        self.image_center_x = 0.0
        self.image_center_y = 0.0
        # Bar cicle. Start with center at middle of image, diameter is 80%
        # of the image width
        (width, height, bits) = self.img.shape
        self.bar_center_x = 0.0
        self.bar_center_y = 0.0
        self.bar_radius = 0.8
        # Set up plot
        self.fig, self.ax = plt.subplots()
        self.set_title(image_file, bar_size)
        self.lines, = self.ax.plot([],[], 'o')
        self.ax.set_xlim(-1.0,1.0)
        self.ax.set_ylim(-1.0,1.0)
        self.ax.grid()
        self.ax.set_aspect('equal', adjustable='box')
        self.fig.canvas.draw()
        # Line
        self.line_x = 1.0
        # Record elements plotted so we can erase them
        self.elements = []

    def set_title(self, image_file, bar_size):
        """Set the title to the file name and the gouge size.

        Args:
            image_file (string): name of image file
            bar_size (float or None): explicit setting of bar size

        Use last element of the file name and the bar size in inches
        if given in the filename or explicitly specified.
        """
        title = os.path.basename(image_file)
        if bar_size is None:
            m = re.search(r'''_(\d+)_(\d+)_''', image_file)
            if m:
                title += '   (' + m.group(1) + '/' + m.group(2) + '" bar diameter)'
        else:
            title += '   (%.3f" bar diameter)' % bar_size
        self.ax.set_title(title)

    def erase(self):
        """Erase all elements from the plot."""
        for element in self.elements:
            print("Removing", element)
            element.remove()
        self.elements = []

    def draw(self):
        """Create or refresh the interactive matplotlib plot.
        """
        self.erase()

        # Calculate circle for outside of bar
        bar_circle_x = []
        bar_circle_y = []
        for angle in numpy.linspace(0.0, 2.0 * math.pi, 50):
            bar_circle_x.append(math.cos(angle) * self.bar_radius + self.bar_center_x)
            bar_circle_y.append(math.sin(angle) * self.bar_radius + self.bar_center_y)

        # And now plot current view
        extent=get_extent(self.fig, self.ax, self.img, 1.0, self.image_center_x, self.image_center_y)
        print(extent)
        self.elements.append(self.ax.imshow(self.img, aspect='auto', extent=extent,
                                            interpolation='none', zorder=0))
        self.elements.append(self.ax.plot([0.0, 1.0], [self.line_x, 0.0],
                                          color="red", linewidth=1)[0])
        self.elements.append(self.ax.plot(bar_circle_x, bar_circle_y, color="yellow", linewidth=1)[0])
        self.ax.set_aspect('equal', adjustable='box') # Have to keep doing this!
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def run(self):
        for it in range(100):
            self.draw()
            print(plt.waitforbuttonpress())

p = argparse.ArgumentParser()
p.add_argument("-v", "--verbosity", action="count", default=0)
p.add_argument("-i", "--image", action="store", default="flute_photos/robust_1_2_2022.jpg",
               help="File name of image to load")
p.add_argument("-b", "--bar-size", action="store", type=float, default=None,
               help="Specify bar diameter overriding any indication in the file name")
args = p.parse_args()

# Logging
logging.basicConfig(level=(logging.WARN if args.verbosity == 0 else (
                           logging.INFO if args.verbosity == 1 else
                           logging.DEBUG)))

# Draw picture...
plt.ion()  # Interactive mode
display = InteractiveDisplay(image_file=args.image, bar_size=args.bar_size)
setup_ui(display.fig, display)
display.run()
