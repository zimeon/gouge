"""Canoe hull design plotter."""

import datetime
import numpy
import math
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter, MultipleLocator
from matplotlib.backends.backend_pdf import PdfPages
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


class Region(object):
    """Class to handle plotting region on multiple sheets."""

    def __init__(self, xx=None, yy=None, mirror_x=False,
                 min_x=0.0, max_x=1.0, min_y=0.0, max_y=1.0,
                 title=None):
        """Initialize plot area, will size from xx, yy curve if given."""
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.title = title
        if (xx is not None and yy is not None):
            self.max_x = round_up(max(xx))
            self.min_x = -self.max_x if mirror_x else round_down(min(xx))
            self.min_y = round_down(min(yy))
            self.max_y = round_up(max(yy))

    def sheet_regions(self, paper_x, paper_y):
        """Generator for sheet regions to plot this region."""
        x_sheets = math.ceil((self.max_x - self.min_x) / (1. * paper_x))
        y_sheets = math.ceil((self.max_y - self.min_y) / (1. * paper_y))
        logging.info("Plan area [%d -- %d, %d -- %d] in %d x %d sheets" %
                     (self.min_x, self.max_x, self.min_y, self.max_y,
                      x_sheets, y_sheets))
        # Arrange to center design on the set of sheets
        x_start = int((self.max_x + self.min_x - x_sheets * paper_x) / 2.0)
        y_start = int((self.max_y + self.min_y - y_sheets * paper_y) / 2.0)
        # Loop over all sheets
        num = 0
        tot = x_sheets * y_sheets
        for y_num in range(0, y_sheets):
            for x_num in range(0, x_sheets):
                num += 1
                r = Region(min_x=(x_start + x_num * paper_x),
                           max_x=(x_start + (x_num + 1) * paper_x),
                           min_y=(y_start + y_num * paper_y),
                           max_y=(y_start + (y_num + 1) * paper_y),
                           title="%d of %d" % (num, tot))
                yield(r)

    def __eq__(self, other):
        """Define equality based on limits with other Region or list."""
        if (isinstance(other, Region)):
            return(self.min_x == other.min_x and self.max_x == other.max_x and
                   self.min_y == other.min_y and self.max_y == other.max_y)
        else:  # assume list
            return(self.min_x == other[0] and self.max_x == other[1] and
                   self.min_y == other[2] and self.max_y == other[3])

    def __repr__(self):
        """String representation."""
        return("Region(%d, %d, %d, %d)" % (self.min_x, self.max_x, self.min_y, self.max_y))

    def __str__(self):
        """Title or string representation."""
        if (self.title is not None):
            return(self.title)
        else:
            return(repr(self))


class Plotter(object):
    """Class to plot hull design."""

    def __init__(self, fig=None, hull=None):
        """Initialize Plotter object."""
        if (fig is None):
            self.fig = plt.figure()
        else:
            self.fig = fig
        self.hull = hull
        self.view = 'orthographic'
        self.station = 0
        self.selected = None
        self.waterline_y = 4.1  # inches
        self.show_waterline = True
        self.use_feet = True
        # Colors
        self.sheer_color = "firebrick"
        self.sheer_point_color = "grey"
        self.profile_color = "navy"
        self.profile_point_color = "grey"
        self.mid_color = "darkgreen"
        self.mid_point_color = "grey"
        # Views we know about, will be an Axes object if we want to plot them
        self.ax_length_profile = None
        self.ax_width_profile = None
        self.ax_plan_view = None
        # Limits for length, width, height
        self.ax_length_lim = None
        self.ax_width_lim = None
        self.ax_height_lim = None
        # Mold construction details
        self.mold_sheet_thickness = 0.75  # inches
        # Paper dimensions (inches), plot area will be
        # paper_x-2*margin, paper_y-2*margin
        self.paper_x = 11.0
        self.paper_y = 17.0
        self.margin = 1.0

    def make_plot(self, reset=False, recalc=False):
        """Create the interactive matplotlib plot.

        reset - set True to reset viewport
        recacl - set True to reset hull calculations (e.g. if internal settings
            have been altered)
        """
        if (not reset and self.ax_width_profile is not None):
            # https://github.com/openPMD/openPMD-viewer/issues/140
            # though should probably really do image update
            # https://stackoverflow.com/questions/9904849/preserve-zoom-settings-in-interactive-navigation-of-matplotlib-figure
            self.ax_width_lim = self.ax_width_profile.get_xlim()
            self.ax_height_lim = self.ax_width_profile.get_ylim()
            logging.debug("Current lims = " + str(self.ax_width_lim) + ' ' + str(self.ax_height_lim))
        else:
            min_l, max_l = self.hull.min_max_length()
            self.ax_length_lim = [min_l - 6.0, max_l + 6.0]
            self.ax_width_lim = None
        if (recalc):
            self.hull._reset_lazy_calcs()
        self.fig.clear()
        if (self.view == 'sections'):
            self.draw_sections()
        elif (self.view == 'station'):
            self.draw_station()
        else:  # default
            self.draw_orthographic()
        self.fig.canvas.draw()

    def draw_orthographic(self):
        """Set up and orthographic set of plots."""
        logging.info('draw_orthograpic')
        max_width = self.hull.max_width
        (min_y, max_y) = self.hull.min_max_vertical()
        (min_l, max_l) = self.hull.min_max_length()
        #
        # Construct 2x2 grid with plots organized in orthographic
        # projection
        #
        # [length profile]  [width profile]
        # [  plan view   ]
        #
        plt_h = max_y - min_y
        plt_l = max_l - min_l + 12.0
        plt_w = max_width * 2.0 + 12.0
        gs = gridspec.GridSpec(2, 2,
                               width_ratios=[plt_l, plt_w],
                               height_ratios=[plt_h, plt_w])
        self.ax_length_profile = self.fig.add_subplot(gs[0])
        self.ax_width_profile = self.fig.add_subplot(gs[1])
        self.ax_plan_view = self.fig.add_subplot(gs[2])
        self.ax_station = None
        self.plot_data()
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95,
                                 wspace=0.07, hspace=0.07)

    def draw_sections(self):
        """Set up just end-view of sections."""
        logging.warn("Drawing sections")
        self.ax_length_profile = None
        self.ax_width_profile = self.fig.add_subplot(111)
        self.ax_plan_view = None
        self.ax_station = None
        self.plot_data()

    def draw_station(self):
        """Set up just end-view of sections."""
        logging.warn("Drawing sections")
        self.ax_length_profile = None
        self.ax_width_profile = None
        self.ax_plan_view = None
        self.ax_station = self.fig.add_subplot(111)
        self.plot_data()

    def plot_data(self):
        """Plot/update all datasets for which axis is not None."""
        if (self.ax_length_profile is not None):
            self.ax_length_profile.clear()
            self.plot_length_profile(self.ax_length_profile)
        if (self.ax_width_profile is not None):
            self.ax_width_profile.clear()
            self.plot_width_profile(self.ax_width_profile)
        if (self.ax_plan_view is not None):
            self.ax_plan_view.clear()
            self.plot_plan_view(self.ax_plan_view)
        if (self.ax_station is not None):
            self.ax_station.clear()
            self.plot_station(self.station, self.ax_station)

    def plot_length_profile(self, ax):
        """Plot length profile of hull l on atplotlib axes ax."""
        # Sheer points
        xx, yy, labels = self.hull.sheer_profile_curve()
        ax.plot(xx, yy, 'o', color=self.sheer_point_color)
        for j, label in enumerate(labels):
            ax.text(xx[j] - 1.0, yy[j] + 1.5, label)
        # Faired sheer
        x2, y2 = self.hull.sheer_profile_fairer.curve()
        ax.plot(x2, y2, '-', color=self.sheer_color)
        # Profile (bottom) points
        xx, yy = self.hull.profile_curve()
        ax.plot(xx, yy, 'o', color=self.profile_point_color)
        # Faired profile
        x2, y2 = self.hull.profile_fairer.curve()
        ax.plot(x2, y2, '-', color=self.profile_color)
        # Size and axes
        ax.set_aspect('equal', 'datalim')
        if (self.ax_length_lim is not None):
            ax.set_xlim(self.ax_length_lim)
        ax.xaxis.set_major_locator(MultipleLocator(12.0 if self.use_feet else 2.0))
        ax.minorticks_on()
        ax.xaxis.set_major_formatter(FuncFormatter(format_feet_inches if self.use_feet else format_inches))
        ax.yaxis.set_major_formatter(FuncFormatter(format_inches))
        # Waterline?
        if (self.show_waterline):
            (x1, x2) = self.hull.min_max_length()
            ax.plot([x1, x2], [self.waterline_y, self.waterline_y], '-', color="blue")
            ax.text(x2, self.waterline_y + 0.1, 'WL %.1f"' % self.waterline_y)
        # Center of buoyancy
        drafts, displacements, cobs = self.hull.displacement_table(1.0, 8.0, 0.5)
        ax.plot(cobs, drafts, '-', color="green")
        ax.text(cobs[-1], drafts[-1] + 1.0, 'COB')

    def plot_width_profile(self, ax):
        """Plot width profile of hull on matplotlib axes ax."""
        # Bow to mid station
        for s in self.hull.bow_to_mid_stations():
            # Defined widths as points, station labels above
            xx, yy = self.hull.breadth_curve(s)
            ax.text(xx[-1] - 0.15, yy[-1] + 0.5, s)
            # Interpolated line
            f = self.hull.breadth_fairer(s)
            x2, y2 = f.curve(end=f.mid_index)
            if (s == self.hull.mid_station):
                ax.plot(xx, yy, 'o', color=self.mid_point_color)
                ax.plot(x2, y2, '-', color=self.mid_color)
            else:
                ax.plot(xx, yy, 'o')
                ax.plot(x2, y2, '-')
        # Stern to mid station
        for s in self.hull.stern_to_mid_stations():
            # Defined widths as points, station labels above
            xx, yy = self.hull.breadth_curve(s, flip_x=True)
            ax.text(xx[-1] - 0.15, yy[-1] + 0.5, s)
            # Interpolated line
            f = self.hull.breadth_fairer(s)
            x2, y2 = f.curve(start=f.mid_index)
            if (s == self.hull.mid_station):
                ax.plot(xx, yy, 'o', color=self.mid_point_color)
                ax.plot(x2, y2, '-', color=self.mid_color)
            else:
                ax.plot(xx, yy, 'o')
                ax.plot(x2, y2, '-')
        # Bow and stern (just lines)
        xx, yy = self.hull.profile_curve()
        xx = [0.0 for y in yy]  # Centerline has x=0 in end view!
        ax.plot(xx, yy, '-', color=self.profile_color)
        ax.plot(xx, yy, 'o', color=self.profile_point_color)
        # Sheer line
        w3, y3 = self.hull.sheer_breadth_profile_curve(bow_to_mid=True)
        ax.plot(w3, y3, '-', color=self.sheer_color)
        w4, y4 = self.hull.sheer_breadth_profile_curve(mid_to_stern=True, flip_x=True)
        ax.plot(w4, y4, '-', color=self.sheer_color)
        # Size and axes
        ax.set_aspect('equal', 'datalim')
        if (self.ax_width_lim is not None):
            ax.set_xlim(self.ax_width_lim)
        if (self.ax_height_lim is not None):
            ax.set_ylim(self.ax_height_lim)
        ax.minorticks_on()
        ax.xaxis.set_major_formatter(FuncFormatter(format_inches))
        ax.yaxis.set_major_formatter(FuncFormatter(format_inches))
        # Waterline?
        if (self.show_waterline):
            wl_x = self.hull.max_width * 1.15
            ax.plot([-wl_x, wl_x], [self.waterline_y, self.waterline_y], '-', color="blue")
            ax.text(self.hull.max_width * 1.05, self.waterline_y + 0.1, 'WL %.1f"' % self.waterline_y)
        # Selected point?
        if (self.selected is not None):
            ax.plot([self.selected.x], [self.selected.y], marker='x', markersize=10, color="red")

    def plot_plan_view(self, ax):
        """Plot plan view of self.hull on matplotlib axes ax."""
        # Set of waterline curves at different depths (upper)
        for height in [0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
            try:
                xx, ww = self.hull.outline_at_height(height)
                ax.plot(xx, ww, '-', color='#8CCDFF')
            except Exception as e:
                logging.warn("Failed to plot waterline curve at height %.2f (%s) " %
                             (height, str(e)))
        # And hull curves at regular heights (lower)
        for w, height in self.hull.breadths[self.hull.mid_station]:
            try:
                xx, ww = self.hull.outline_at_height(height)
                ww = [-w for w in ww]
                ax.plot(xx, ww, '-', color='#8FB645')
            except Exception as e:
                logging.warn("Failed to plot hull curves at height %.1f (%s)" %
                             (height, str(e)))
        # Sheer curves (last so on top)
        xx, ww, labels = self.hull.sheer_breadth_plan_curve()
        ax.plot(xx, ww, 'o', color=self.sheer_point_color)
        ax.plot(xx, [-w for w in ww], 'o', color=self.sheer_point_color)
        for x, w, label in zip(xx, ww, labels):
            ax.text(x - 1.0, w + 1.5, label)
        # Fairer sheer
        x2, w2 = self.hull.sheer_breadth_fairer.curve()
        ax.plot(x2, w2, '-', color=self.sheer_color)
        ax.plot(x2, [-w for w in w2], '-', color=self.sheer_color)
        # Size and axes
        ax.set_aspect('equal', 'datalim')
        if (self.ax_length_lim is not None):
            ax.set_xlim(self.ax_length_lim)
        ax.xaxis.set_major_locator(MultipleLocator(12.0 if self.use_feet else 2.0))
        ax.minorticks_on()
        ax.xaxis.set_major_formatter(FuncFormatter(format_feet_inches if self.use_feet else format_inches))
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
        for s in self.hull.bow_to_mid_stations():
            # Defined widths as points, station labels above
            xx, yy = self.hull.breadth_curve(s)
            for x, y in zip(xx, yy):
                d = mouse.distance(x, y)
                if (d < closest.mouse_distance):
                    # New closest poi
                    next_closest = closest
                    closest = Point(x, y, station=s, mouse_distance=d)
        # Stern to mid station
        for s in self.hull.stern_to_mid_stations():
            # Defined widths as points, station labels above
            xx, yy = self.hull.breadth_curve(s, flip_x=True)
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

        Width profile points can be moved only in x axis, sheer points can be moved
        in x and y.
        """
        w = self.selected.x
        y = self.selected.y
        s = self.selected.station
        for j, wy in enumerate(self.hull.breadths[s]):
            if (wy[0] == w and wy[1] == y):
                self.selected.x += dx
                self.hull.breadths[s][j] = [self.selected.x, y]
                self.hull._reset_lazy_calcs()
                return
            if (wy[0] == -w and wy[1] == y):
                self.selected.x += dx
                self.hull.breadths[s][j] = [-self.selected.x, y]
                self.hull._reset_lazy_calcs()
                return
        # else sheer point?
        if (w == self.hull.sheer_breadth[s] and y == self.hull.sheer_height[s]):
                self.selected.x += dx
                self.selected.y += dy
                self.hull.sheer_breadth[s] = self.selected.x
                self.hull.sheer_height[s] = self.selected.y
                self.hull._reset_lazy_calcs()
                return
        if (w == -self.hull.sheer_breadth[s] and y == self.hull.sheer_height[s]):
                self.selected.x += dx
                self.selected.y += dy
                self.hull.sheer_breadth[s] = -self.selected.x
                self.hull.sheer_height[s] = self.selected.y
                self.hull._reset_lazy_calcs()
                return
        logging.warn("Failed to match point in move_point_width_profile")

    def plot_station(self, station, ax, region=None):
        """Plot one station of hull on matplotlib axes ax.

        This plot is designed for printing so fit onto some mutliple of
        9 by 15 sheets.
        """
        xx, yy = self.hull.breadth_curve(station)
        # What are x & y limits at this station if not given
        if (region is None):
            region = Region(xx, yy, mirror_x=True)
            logging.info("Station plot area [%d -- %d, %d -- %d]" %
                         (region.min_x, region.max_x, region.min_y, region.max_y))
        # Defined widths as points, station label inside right sheer
        ax.text(xx[-1] - 2.0, yy[-1] - 1.0, "Station %d" % station)
        # Interpolated line
        x2, y2 = self.hull.breadth_fairer(station).curve()
        ax.plot(xx, yy, 'x', color="red")
        ax.plot([-x for x in xx], yy, 'x', color="red")
        ax.plot(x2, y2, '-', color="black")
        ax.set_aspect('equal', 'datalim')
        ax.grid(color='black', linewidth=1)
        ax.xaxis.set_major_formatter(FuncFormatter(format_inches))
        ax.yaxis.set_major_formatter(FuncFormatter(format_inches))
        # Waterline?
        if (self.show_waterline):
            wl_x = self.hull.max_width * 1.15
            ax.plot([-wl_x, wl_x], [self.waterline_y, self.waterline_y], '-', color="blue")
            ax.text(self.hull.max_width * 1.05, self.waterline_y + 0.1, 'WL %.1f"' % self.waterline_y)

    def multi_sheet_ax_generator(self, pdf, xx, yy, mirror_x=False, add_form_lines=False):
        """Generator giving axes and Region() for multi-sheet plot to cover xx, yy.

        If mirror_x is true will use a Region that includes mirror of x data.

        If add_form_lines is true then will plot form lines around y=0
        """
        region = Region(xx, yy, mirror_x)
        plot_x = self.paper_x - 2.0 * self.margin
        plot_y = self.paper_y - 2.0 * self.margin
        for r in region.sheet_regions(plot_x, plot_y):
            fig = plt.figure(figsize=(self.paper_x, self.paper_y))
            ax = fig.add_subplot(111)
            yield(ax, r)
            ax.plot([0.0, 0.0], [-100.0, 100.0], '-', color="red")
            ax.plot([-100.0, 100.0], [0.0, 0.0], '-', color="red")
            if (add_form_lines):
                dx = self.mold_sheet_thickness / 2.0
                ax.plot([dx, dx], [-100.0, 100.0], '-', color="red")
                ax.plot([-dx, -dx], [-100.0, 100.0], '-', color="red")
            ax.set_xlim(r.min_x, r.max_x)
            ax.set_ylim(r.min_y, r.max_y)
            ax.set_xticks(numpy.arange(r.min_x, r.max_x + 1.0, 1.0))
            ax.set_yticks(numpy.arange(r.min_y, r.max_y + 1.0, 1.0))
            ax.grid(color='black', linewidth=1)
            ax.xaxis.set_major_formatter(FuncFormatter(format_inches))
            ax.yaxis.set_major_formatter(FuncFormatter(format_inches))
            fig.subplots_adjust(left=(self.margin / self.paper_x),
                                bottom=(self.margin / self.paper_y),
                                right=(1.0 - self.margin / self.paper_x),
                                top=(1.0 - self.margin / self.paper_y))
            pdf.savefig()
            plt.close()

    def write_plans(self, plansfile):
        """Write out a set of plans for self.paper_x x self.paper_y paper.

        See example at
        https://matplotlib.org/examples/pylab_examples/multipage_pdf.html
        """
        logging.warn("Writing plans to %s" % (plansfile))
        with PdfPages(plansfile) as pdf:
            # Station sections (complete from side to side)
            for station in self.hull.stations:
                xx, yy = self.hull.breadth_curve(station)
                first_or_last = (station == min(self.hull.stations) or station == max(self.hull.stations))
                for ax, sheet_region in self.multi_sheet_ax_generator(pdf, xx, yy, mirror_x=True, add_form_lines=first_or_last):
                    self.plot_station(station, ax, sheet_region)
                    plt.title("Station %d, sheet %s" % (station, str(sheet_region)))
            # Profile curve
            xp, yp = self.hull.profile_fairer.curve()
            xsp, ysp = self.hull.sheer_profile_fairer.curve()
            # Bow profile
            br = min(self.hull.station_positions) + 1
            brl = self.hull.station_positions[br]
            brl2 = self.hull.station_positions[br - 1] - brl
            xx = []
            yy = []
            for x, y in self.hull.bow_profile:
                xx.append(x - brl)
                yy.append(y)
            # and kheel line at station br - 1 and br
            xx.append(0.0)
            yy.append(self.hull.profile_height[br])
            xx.append(0.0)
            yy.append(self.hull.profile_height[br])
            xb = [x - brl for x in xp]
            xsb = [x - brl for x in xsp]
            for ax, sheet_region in self.multi_sheet_ax_generator(pdf, xx, yy, add_form_lines=True):
                ax.plot(xx, yy, 'x', color="red")
                ax.plot(xb, yp, '-', color="black")
                ax.plot(xsb, ysp, '-', color="grey")
                # Vertical line at half mold sheet thichkness from station br
                dx = self.mold_sheet_thickness / 2.0
                ax.plot([brl2 + dx, brl2 + dx], [-100.0, 100.0], '-', color="red")
                ax.plot([brl2 - dx, brl2 - dx], [-100.0, 100.0], '-', color="red")
                plt.title("Bow profile relative to station %d, sheet %s" % (br, str(sheet_region)))
            # Stern profile
            sr = max(self.hull.station_positions) - 1
            srl = self.hull.station_positions[sr]
            srl2 = srl - self.hull.station_positions[sr + 1]
            xx = []
            yy = []
            for x, y in self.hull.stern_profile:
                xx.append(srl - x)
                yy.append(y)
            # and kheel line at station sr
            xx.append(0.0)
            yy.append(self.hull.profile_height[sr])
            xs = [srl - x for x in xp]
            xss = [srl - x for x in xsp]
            for ax, sheet_region in self.multi_sheet_ax_generator(pdf, xx, yy, add_form_lines=True):
                ax.plot(xx, yy, 'x', color="red")
                ax.plot(xs, yp, '-', color="black")
                ax.plot(xss, ysp, '-', color="grey")
                # Vertical line at half mold sheet thichkness from station sr
                dx = self.mold_sheet_thickness / 2.0
                ax.plot([srl2 + dx, srl2 + dx], [-100.0, 100.0], '-', color="red")
                ax.plot([srl2 - dx, srl2 - dx], [-100.0, 100.0], '-', color="red")
                plt.title("Stern profile relative to station %d, sheet %s" % (sr, str(sheet_region)))
            #
            # PDF metadata
            d = pdf.infodict()
            d['Title'] = 'Canoe Plans'
            # d['Author'] = 'Me'
            # d['Subject'] = 'Blah'
            d['CreationDate'] = datetime.datetime.today()
            d['ModDate'] = datetime.datetime.today()
