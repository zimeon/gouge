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
        return math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)

    def __repr__(self):
        """Return string representation."""
        return "Point(%.3f, %.3f, station=%s, mouse_distance=%.3f)" % (self.x, self.y, self.station, self.mouse_distance)


class Plotter(object):
    """Class to plot pictures of gouge model."""

    def __init__(self, fig=None, gouge=None, view="third_angle"):
        """Initialize Plotter object."""
        if (fig is None):
            self.fig = plt.figure()
        else:
            self.fig = fig
        self.gouge = gouge
        self.bar_length = 1.0
        # Layout and view
        self.view = view
        # Colors
        self.outline_color = "blue"
        self.grinding_line_color = "green"
        # Views we know about, will be an Axes object if we want to plot them
        self.ax_profile_view = None
        self.ax_end_view = None
        self.ax_plan_view = None
        # Control display
        self.show_grinding_edge_arrows = False
        self.show_grinding_edge_angles = True

    def make_plot(self, reset=False, recalc=False):
        """Create the interactive matplotlib plot.

        reset - set True to reset viewport
        recacl - set True to reset gouge calculations (e.g. if internal settings
            have been altered)
        """
        if reset:
            self.gouge.solve()
        self.fig.clear()
        if self.view == 'third_angle':
            self.draw_third_angle()
        else:
            self.draw_one_view()
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
        # self.fig.suptitle('Bowl Gouge Shape')
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

    def draw_one_view(self):
        """Set up draw one view/projections.

        Supported views are 'profile', 'plan' , 'end'.
        """
        logging.info('draw_one_view: %s', self.view)

        # Use gridspec just to keep things similar with third angle plot
        gs = self.fig.add_gridspec(ncols=1, nrows=1)
        ax = self.fig.add_subplot(gs[0], aspect='equal')
        ax.xaxis.set_major_locator(MultipleLocator(0.5))
        ax.xaxis.set_major_formatter(FuncFormatter(format_inches))
        ax.yaxis.set_major_formatter(FuncFormatter(format_inches))
        ax.minorticks_on()
        if self.view == 'profile':
            self.plot_profile_view(ax)
        elif self.view == 'plan':
            self.plot_plan_view(ax)
        elif self.view == 'end':
            self.plot_end_view(ax)
        else:
            logging.warn("Unknown view '%s', nothing to plot!", self.view)

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

        The z-axis is horizonatal, y-axis is vertical.
        """
        zz = [-self.bar_length]
        yy = [self.gouge.bar_top_height]
        cx, cy, cz = self.gouge.cutting_edge_curve_points(half=True)
        zz.extend(cz)
        yy.extend(cy)
        ax.plot(zz, yy, '-', color=self.outline_color)

        # Plot nose and lower edge of bar
        gx, gy, gz = self.gouge.grinding_line[0.0]
        zz = [gz[-1], -self.bar_length]
        yy = [gy[-1], -self.gouge.bar_radius]
        ax.plot(zz, yy, '-', color=self.outline_color)

        self.draw_grinding_edge_arrows(ax, 2, 1)
        self.draw_grinding_lines(ax, 2, 1)
        self.draw_grinding_tail(ax, 2, 1)
        self.draw_grinding_extension(ax, 2, 1)

    def plot_end_view(self, ax):
        """Plot end view gouge on matplotlib axes ax.

        The x-axis is horizonatal, y-axis is vertical.
        """
        bx, by, bz = self.gouge.bar_end_curve()
        ax.plot(bx, by, '-', color=self.outline_color)

        cx, cy, cz = self.gouge.cutting_edge_curve_points()
        ax.plot(cx, cy, '-', color="red")
        ax.plot(cx, cy, 'o', color=self.outline_color)

        self.draw_grinding_edge_arrows(ax, 0, 1)
        self.draw_grinding_lines(ax, 0, 1, add_mirror=True)
        self.draw_grinding_extension(ax, 0, 1, add_mirror=True)

    def plot_plan_view(self, ax):
        """Plot plan view of self.gouge on matplotlib axes ax.

        The z-axis is horizontal, x-axis is vertical.
        """
        # Top of channel and then cutting edge
        zz = [-self.bar_length]
        xx = [-self.gouge.bar_top_width]
        cx, cy, cz = self.gouge.cutting_edge_curve_points()
        zz.extend(cz)
        xx.extend(cx)
        zz.append(-self.bar_length)
        xx.append(self.gouge.bar_top_width)
        ax.plot(zz, xx, '-', color=self.outline_color, linewidth=2)

        # Edge of bar and trailing edge (not all to be seen)
        # Find z of widest point, y=0, of trailing edge
        last_x, last_y, last_z = -self.gouge.bar_radius, 0.0, 0.0
        mid_z = 0.0
        for aj in self.gouge.grinding_tail_point:
            pt = self.gouge.grinding_tail_point[aj]
            logging.info("pt %s", pt)
            x, y, z = pt[0], pt[1], pt[2]
            if y > 0.0:
                mid_z = -last_y * last_z / (y - last_y) + y * z / (y - last_y)
                break
            last_x, last_y, last_z = x, y, z
        # Sides of bar
        zz = [-self.bar_length, mid_z]
        xx = [-self.gouge.bar_radius, -self.gouge.bar_radius]
        ax.plot(zz, xx, '-', color=self.outline_color)
        ax.plot(zz, numpy.multiply(xx, numpy.full_like(xx, -1.0)), '-', color=self.outline_color)

        self.draw_grinding_edge_arrows(ax, 2, 0)
        self.draw_grinding_lines(ax, 2, 0, add_mirror=True)
        self.draw_grinding_tail(ax, 2, 0, add_mirror=True)
        self.draw_grinding_extension(ax, 2, 0, add_mirror=True)

    def draw_grinding_edge_arrows(self, ax, x_index=0, y_index=1, length=0.05):
        """Draw grinding edge arrow and/or angles.

        Display controlled by self.show_grinding_edge_arrows and
        self.show_grinding_edge_angles

        The cutting edge angle is found using the cross product of
        unit vectors of the grinding wheel tangent (=grinding line)
        at the edge and unit vector along the flute (z direction).
        This magnitude of this is the sine of the cutting edge angle.
        The value at the nose is a good check.
        """
        for aj in self.gouge.grinding_line:
            ep = self.gouge.grinding_edge_point[aj]
            et = self.gouge.grinding_edge_tangent[aj]
            gwn = self.gouge.grinding_wheel_normal[aj]
            gwt = self.gouge.grinding_wheel_tangent[aj]
            if self.show_grinding_edge_arrows:
                ax.arrow(ep[x_index], ep[y_index],
                         et[x_index] * length * 0.5, et[y_index] * length * 0.5,
                         color="cyan", head_width=0.01)
                ax.arrow(ep[x_index], ep[y_index],
                         gwn[x_index] * length, gwn[y_index] * length,
                         color="orange", head_width=0.01)
                ax.arrow(ep[x_index], ep[y_index],
                         gwt[x_index] * length, gwt[y_index] * length,
                         color="brown", head_width=0.01)
            if self.show_grinding_edge_angles:
                # Print out the cutting edge angle
                angle = numpy.rad2deg(numpy.arcsin(numpy.linalg.norm(numpy.cross(numpy.array([0, 0, 1]), gwt))))
                logging.info(" GRINDING ANGLE @ %.3f = %.1f degrees", aj, angle)
                # Make the nose angle bold and stand out a little further than all others
                separation = 0.035 if aj == 0.0 else 0.015
                weight = "bold" if aj == 0.0 else "medium"
                ax.text(ep[x_index] + gwt[x_index] * separation,
                        ep[y_index] + gwt[y_index] * separation,
                        ("%d" % int(angle + 0.5)),
                        fontsize=7, fontweight=weight,
                        horizontalalignment="center")

    def draw_grinding_lines(self, ax, x_index=0, y_index=1, add_mirror=False):
        """Draw grinding lines.

        If add_mirror is true then the other side with x>0 is also drawn.
        """
        for aj in self.gouge.grinding_line:
            points = self.gouge.grinding_line[aj]
            ax.plot(points[x_index], points[y_index], '-', color=self.grinding_line_color)
        if add_mirror:
            for aj in self.gouge.grinding_line:
                points = self.gouge.grinding_line[aj]
                flip_x = numpy.multiply(points[0], numpy.full_like(points[0], -1.0))
                points2 = [flip_x, points[1], points[2]]
                ax.plot(points2[x_index], points2[y_index], '-', color=self.grinding_line_color)

    def draw_grinding_tail(self, ax, x_index=0, y_index=1, add_mirror=False):
        """Draw grinding tail line.

        If add_mirror is true then the side with x>0 is also drawn.
        """
        px = []
        py = []
        mx = []
        my = []
        for aj in self.gouge.grinding_tail_point:
            x = self.gouge.grinding_tail_point[aj][x_index]
            y = self.gouge.grinding_tail_point[aj][y_index]
            px.append(x)
            py.append(y)
            if (aj != 0.0 and y_index == 0 and add_mirror):
                mx.append(x)
                my.append(-y)
        px.extend(reversed(mx))
        py.extend(reversed(my))
        ax.plot(px, py, '-', color="orange")

    def draw_grinding_extension(self, ax, x_index=0, y_index=1, add_mirror=False):
        """Draw grinding extension outline and grinding lines.

        If add_mirror is true then the side with x>0 is also drawn.
        """
        px = []
        py = []
        mx = []
        my = []
        for point in self.gouge.grinding_extension_curve:
            x = point[x_index]
            y = point[y_index]
            px.append(x)
            py.append(y)
            if y_index == 0 and add_mirror:
                mx.append(x)
                my.append(-y)
        ax.plot(px, py, '-', color="red")
        if add_mirror:
            ax.plot(mx, my, '-', color="red")
        # and now the grinding lines
        for aj in self.gouge.grinding_extension_line:
            points = self.gouge.grinding_extension_line[aj]
            ax.plot(points[x_index], points[y_index], '-', color=self.grinding_line_color)
        if add_mirror:
            for aj in self.gouge.grinding_extension_line:
                points = self.gouge.grinding_extension_line[aj]
                flip_x = numpy.multiply(points[0], numpy.full_like(points[0], -1.0))
                points2 = [flip_x, points[1], points[2]]
                ax.plot(points2[x_index], points2[y_index], '-', color=self.grinding_line_color)
