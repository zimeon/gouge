"""Gouge model plotter."""

import numpy
import math
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter, MultipleLocator
import logging
import sys

from util import format_inches


def select_projection(points, proj):
    """Select coordinate sets for given projection.

    `proj` options: `xy`, `yz`, `xz`
    """
    a, b = [], []
    for point in points:
        if proj == 'xy':
            a.append(point[0])
            b.append(point[1])
        elif proj == 'yz':
            a.append(point[1])
            b.append(point[2])
        elif proj == 'xz':
            a.append(point[0])
            b.append(point[2])
        else:
            logging.warn("Unknown projection '%s'" % proj)
            sys.exit(1)
    return a, b


class Point(object):
    """Class to represent selected point."""

    def __init__(self, x=-999.0, y=-999.0, station='-', mouse_distance=99999.0):
        """Initialize Point object."""
        self.x = x
        self.y = y
        self.station = station
        self.mouse_distance = mouse_distance

    def distance(self, x, y):
        """Distance of this point from x,y."""
        return(math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2))

    def __repr__(self):
        """String representation."""
        return("Point(%.3f, %.3f, station=%s, mouse_distance=%.3f)" % (self.x, self.y, self.station, self.mouse_distance))


class Plotter(object):
    """Class to plot pictures of gouge model."""

    def __init__(self, fig=None, gouge=None):
        """Initialize Plotter object."""
        if (fig is None):
            self.fig = plt.figure()
        else:
            self.fig = fig
        self.gouge = gouge
        self.bar_length = 1.0
        # Colors
        self.outline_color = "blue"
        self.grinding_line_color = "green"
        # Views we know about, will be an Axes object if we want to plot them
        self.ax_profile_view = None
        self.ax_end_view = None
        self.ax_plan_view = None

    def make_plot(self, reset=False, recalc=False):
        """Create the interactive matplotlib plot.

        reset - set True to reset viewport
        recacl - set True to reset gouge calculations (e.g. if internal settings
            have been altered)
        """
        # self.gouge.solve()
        self.fig.clear()
        self.draw_third_angle()
        self.fig.canvas.draw()

    def draw_third_angle(self):
        """Set up and third angle set of projections."""
        logging.info('draw_orthograpic')
        #
        # Construct 2x2 grid with plots organized in
        # third_angle projection
        #
        # [ plan view    gs[0]]  (would be gs[1])
        # [ profile view gs[2]]  [end view gs[3]]
        #
        gs = self.fig.add_gridspec(ncols=2, nrows=2)
        #self.fig.suptitle('Bowl Gouge Shape')
        # Profile view (top left)
        self.ax_profile_view = self.fig.add_subplot(gs[2], aspect='equal')
        self.ax_profile_view.xaxis.set_major_locator(MultipleLocator(0.5))
        self.ax_profile_view.xaxis.set_major_formatter(FuncFormatter(format_inches))
        self.ax_profile_view.yaxis.set_major_formatter(FuncFormatter(format_inches))
        self.ax_profile_view.minorticks_on()
        # End view (top right)
        self.ax_end_view = self.fig.add_subplot(gs[3], sharey=self.ax_profile_view, aspect='equal')
        self.ax_end_view.xaxis.set_major_locator(MultipleLocator(0.5))
        self.ax_end_view.xaxis.set_major_formatter(FuncFormatter(format_inches))
        self.ax_end_view.minorticks_on()
        # Plan view (bottom left)
        self.ax_plan_view = self.fig.add_subplot(gs[0], sharex=self.ax_profile_view, aspect='equal')
        self.ax_plan_view.xaxis.set_major_locator(MultipleLocator(0.5))
        self.ax_plan_view.yaxis.set_major_formatter(FuncFormatter(format_inches))
        #
        self.plot_data()

    def plot_data(self):
        """Plot/update all datasets for which axis is not None."""
        if (self.ax_profile_view is not None):
            self.ax_profile_view.clear()
            self.plot_profile_view(self.ax_profile_view)
        if (self.ax_end_view is not None):
            self.ax_end_view.clear()
            self.plot_end_view(self.ax_end_view)
        if (self.ax_plan_view is not None):
            self.ax_plan_view.clear()
            self.plot_plan_view(self.ax_plan_view)

    def plot_profile_view(self, ax):
        """Plot length profile of gouge on matplotlib axes ax.

        Draws the profile along bar top, down cutting edge,
        down ground edge, and then back along the bar.
        """
        zz = [-self.bar_length]
        yy = [self.gouge.bar_top_height]
        cx, cy, cz = self.gouge.cutting_edge_curve_points(half=True)
        zz.extend(cz)
        yy.extend(cy)
        ax.plot(zz, yy, '-', color=self.outline_color)

        # Plot nose and lower edge of bar
        #gx, gy, gz = self.gouge.grinding_curve(cx[-1], cy[-1], cz[-1])
        #zz = [gz[-1], -self.bar_length]
        #yy = [gy[-1], -self.gouge.bar_radius]
        #ax.plot(zz, yy, '-', color=self.outline_color)

        # Grinding lines
        #for ex, ey, ez in zip(cx, cy, cz):
        #    gx, gy, gz = self.gouge.grinding_curve(ex, ey, ez)
        #    ax.plot(gz, gy, '-', color=self.grinding_line_color)

    def plot_end_view(self, ax):
        """Plot end view gouge on matplotlib axes ax."""
        bx, by, bz = self.gouge.bar_end_curve()
        ax.plot(bx, by, '-', color=self.outline_color)

        cx, cy, cz = self.gouge.cutting_edge_curve_points()
        ax.plot(cx, cy, '-', color="red")
        ax.plot(cx, cy, 'o', color=self.outline_color)

        # Grinding lines
        #for ex, ey, ez in zip(cx, cy, cz):
        #    gx, gy, gz = self.gouge.grinding_curve(ex, ey, ez)
        #    ax.plot(gx, gy, '-', color=self.grinding_line_color)

    def plot_plan_view(self, ax):
        """Plot plan view of self.gouge on matplotlib axes ax.

        In model space this has -z horizontal and +x vertical.
        """
        # Top of channel and then curring edge
        zz = [-self.bar_length]
        xx = [-self.gouge.bar_top_width]
        cx, cy, cz = self.gouge.cutting_edge_curve_points()
        zz.extend(cz)
        xx.extend(cx)
        zz.append(-self.bar_length)
        xx.append(self.gouge.bar_top_width)
        ax.plot(zz, xx, '-', color=self.outline_color, linewidth=2)

        # Edge of bar and trailing edge (not all to be seen)
        zz = [-self.bar_length]
        xx = [-self.gouge.bar_radius]
        zz.extend([0.0, 0.0])  # FIXME - need curve
        xx.extend([-self.gouge.bar_radius, -self.gouge.bar_radius / 2.0])
        ax.plot(zz, xx, '-', color=self.outline_color)
        ax.plot(zz, numpy.multiply(xx, numpy.full_like(xx, -1.0)), '-', color=self.outline_color)
