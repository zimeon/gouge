"""Gouge model plotter."""

import datetime
import numpy
import math
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter, MultipleLocator
import logging
import sys

from util import format_inches, format_feet_inches, fill_range, round_up, round_down


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
        self.view = 'orthographic'
        self.station = 0
        self.selected = None
        self.bar_length = 1.0
        # Colors
        self.profile_color = "navy"
        self.profile_point_color = "grey"
        self.mid_color = "darkgreen"
        self.mid_point_color = "grey"
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
        self.fig.clear()
        self.draw_orthographic()
        self.fig.canvas.draw()

    def draw_orthographic(self):
        """Set up and orthographic set of plots."""
        logging.info('draw_orthograpic')
        #
        # Construct 2x2 grid with plots organized in
        # orthographic projection
        #
        # [length profile]  [end view]
        # [  plan view   ]
        #
        #plt_w = self.gouge.bar_diameter * 1.5
        #plt_l = self.gouge.bar_diameter * self.bar_length
        gs = gridspec.GridSpec(2, 2)
        #,
        #                       width_ratios=[plt_l, plt_w],
        #                       height_ratios=[plt_w, plt_w])
        self.ax_profile_view = self.fig.add_subplot(gs[0])
        self.ax_end_view = self.fig.add_subplot(gs[1])
        self.ax_plan_view = self.fig.add_subplot(gs[2])
        self.plot_data()
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95,
                                 wspace=0.07, hspace=0.07)

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
        cx, cy, cz = self.gouge.cutting_edge_curve(half=True)
        zz.extend(cz)
        yy.extend(cy)
        gx, gy, gz = self.gouge.grinding_curve()
        zz.extend(gz)
        yy.extend(gy)
        zz.append(-self.bar_length)
        yy.append(-self.gouge.bar_radius)
        ax.plot(zz, yy, 'o', color=self.mid_point_color)
        ax.plot(zz, yy, '-', color=self.mid_point_color)
        # Size and axes
        ax.set_aspect('equal', 'datalim')
        ax.xaxis.set_major_locator(MultipleLocator(1.0))
        ax.minorticks_on()
        ax.xaxis.set_major_formatter(FuncFormatter(format_inches))
        ax.yaxis.set_major_formatter(FuncFormatter(format_inches))

    def plot_end_view(self, ax):
        """Plot end view gouge on matplotlib axes ax."""
        bx, by, bz = self.gouge.bar_end_curve()
        ax.plot(bx, by, '-', color=self.mid_point_color)

        cx, cy, cz = self.gouge.cutting_edge_curve()
        ax.plot(cx, cy, '-', color=self.mid_point_color)
        ax.plot(cx, cy, 'o', color=self.mid_point_color)

        # Size and axes
        ax.set_aspect('equal', 'datalim')
        ax.xaxis.set_major_locator(MultipleLocator(1.0))
        ax.minorticks_on()
        ax.xaxis.set_major_formatter(FuncFormatter(format_inches))
        ax.yaxis.set_major_formatter(FuncFormatter(format_inches))
        # Selected point?
        if (self.selected is not None):
            ax.plot([self.selected.x], [self.selected.y], marker='x', markersize=10, color="red")

    def plot_plan_view(self, ax):
        """Plot plan view of self.gouge on matplotlib axes ax.

        In model space this has -z horizontal and +x vertical.
        """
        # Top of channel and then curring edge
        zz = [-self.bar_length]
        xx = [-self.gouge.bar_top_width]
        cx, cy, cz = self.gouge.cutting_edge_curve()
        zz.extend(cz)
        xx.extend(cx)
        zz.append(-self.bar_length)
        xx.append(self.gouge.bar_top_width)
        ax.plot(zz, xx, '-', color=self.mid_point_color, linewidth=2)

        # Edge of bar and trailing edge (not all to be seen)
        zz = [-self.bar_length]
        xx = [-self.gouge.bar_radius]
        zz.extend([0.0, 0.0])  # FIXME - need curve
        xx.extend([-self.gouge.bar_radius, -self.gouge.bar_radius / 2.0])
        ax.plot(zz, xx, '-', color=self.mid_point_color)
        ax.plot(zz, numpy.multiply(xx, numpy.full_like(xx, -1.0)), '-', color=self.mid_point_color)

        # Size and axes
        ax.set_aspect('equal', 'datalim')
        ax.xaxis.set_major_locator(MultipleLocator(1.0))
        ax.minorticks_on()
        ax.xaxis.set_major_formatter(FuncFormatter(format_inches))
        ax.yaxis.set_major_formatter(FuncFormatter(format_inches))

    def select_point_width_profile(self, w, y, ratio=1.5):
        """Select point most closely matching w,y in sections view.

        Require that the closest point is at least `ratio` times closer than the
        next closest point.
        """
        mouse = Point(w, y)
        closest = Point()
        next_closest = Point()
        # Bow to mid station
        for s in self.gouge.bow_to_mid_stations():
            # Defined widths as points, station labels above
            xx, yy = self.gouge.breadth_curve(s)
            for x, y in zip(xx, yy):
                d = mouse.distance(x, y)
                if (d < closest.mouse_distance):
                    # New closest poi
                    next_closest = closest
                    closest = Point(x, y, station=s, mouse_distance=d)
        # Stern to mid station
        for s in self.gouge.stern_to_mid_stations():
            # Defined widths as points, station labels above
            xx, yy = self.gouge.breadth_curve(s, flip_x=True)
            for x, y in zip(xx, yy):
                d = mouse.distance(x, y)
                if (d < closest.mouse_distance):
                    # New closest point
                    next_closest = closest
                    closest = Point(x, y, station=s, mouse_distance=d)
        if (closest.mouse_distance < (next_closest.mouse_distance / ratio)):
            self.selected = closest
            logging.warn("Got new point " + str(closest))
        else:
            self.selected = None
            logging.warn("No point selected")

    def move_point_width_profile(self, dx=0.0, dy=0.0):
        """Move selection point in width profile by specified amount of width.

        Width profile points can be moved only in x axis.
        """
        w = self.selected.x
        y = self.selected.y
        s = self.selected.station
        for j, wy in enumerate(self.gouge.breadths[s]):
            if (wy[0] == w and wy[1] == y):
                self.selected.x += dx
                self.gouge.breadths[s][j] = [self.selected.x, y]
                return
            if (wy[0] == -w and wy[1] == y):
                self.selected.x += dx
                self.gouge.breadths[s][j] = [-self.selected.x, y]
                return
        logging.warn("Failed to match point in move_point_width_profile")
