"""Gouge model plotter."""

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
        self.ax_end_view = None
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
        recacl - set True to reset gouge calculations (e.g. if internal settings
            have been altered)
        """
        if (not reset and self.ax_end_view is not None):
            # https://github.com/openPMD/openPMD-viewer/issues/140
            # though should probably really do image update
            # https://stackoverflow.com/questions/9904849/preserve-zoom-settings-in-interactive-navigation-of-matplotlib-figure
            self.ax_width_lim = self.ax_end_view.get_xlim()
            self.ax_height_lim = self.ax_end_view.get_ylim()
            logging.debug("Current lims = " + str(self.ax_width_lim) + ' ' + str(self.ax_height_lim))
        else:
            min_l, max_l = self.gouge.min_max_length()
            self.ax_length_lim = [min_l - 6.0, max_l + 6.0]
            self.ax_width_lim = None
        if (recalc):
            self.gouge._reset_lazy_calcs()
        self.fig.clear()
        self.draw_orthographic()
        self.fig.canvas.draw()

    def draw_orthographic(self):
        """Set up and orthographic set of plots."""
        logging.info('draw_orthograpic')
        #
        # Construct 2x2 grid with plots organized in orthographic
        # projection
        #
        # [length profile]  [end view]
        # [  plan view   ]
        #
        plt_h = self.gouge.bar_diameter * 1.5
        plt_l = self.gouge.bar_diameter * 3.0
        gs = gridspec.GridSpec(2, 2,
                               width_ratios=[plt_l, plt_w],
                               height_ratios=[plt_w, plt_w])
        self.ax_length_profile = self.fig.add_subplot(gs[0])
        self.ax_end_view = self.fig.add_subplot(gs[1])
        self.ax_plan_view = self.fig.add_subplot(gs[2])
        self.ax_station = None
        self.plot_data()
        self.fig.subplots_adjust(left=0.05, right=0.95, bottom=0.05, top=0.95,
                                 wspace=0.07, hspace=0.07)

    def plot_data(self):
        """Plot/update all datasets for which axis is not None."""
        if (self.ax_length_profile is not None):
            self.ax_length_profile.clear()
            self.plot_length_profile(self.ax_length_profile)
        if (self.ax_end_view is not None):
            self.ax_end_view.clear()
            self.plot_end_view(self.ax_end_view)
        if (self.ax_plan_view is not None):
            self.ax_plan_view.clear()
            self.plot_plan_view(self.ax_plan_view)
        if (self.ax_station is not None):
            self.ax_station.clear()
            self.plot_station(self.station, self.ax_station)

    def plot_length_profile(self, ax):
        """Plot length profile of gouge on atplotlib axes ax."""

        # Size and axes
        ax.set_aspect('equal', 'datalim')
        if (self.ax_length_lim is not None):
            ax.set_xlim(self.ax_length_lim)
        ax.xaxis.set_major_locator(MultipleLocator(1.0))
        ax.minorticks_on()
        ax.xaxis.set_major_formatter(FuncFormatter(format_inches))
        ax.yaxis.set_major_formatter(FuncFormatter(format_inches))

    def plot_end_view(self, ax):
        """Plot end view gouge on matplotlib axes ax."""
        # Bar
        bx = []
        by = []
        r = self.gouge.bar_diameter / 2.0
        for angle in numpy.arange(0.0, 360.0, 5.0):
            ar = angle / 180.0 * 3.141529
            #logging.warn("Angle %f" % ar)
            x = math.cos(ar) * r
            y = math.sin(ar) * r
            bx.append(x)
            by.append(y)
        ax.plot(bx, by, 'o', color=self.mid_point_color)

        fx = []
        fy = []
        for f in numpy.arange(-1.0, +1.1, 0.1):
            x = f * r
            y = f*f * r
            fx.append(x)
            fy.append(y)
        ax.plot(fx, fy, '-', color=self.mid_point_color)

        # Size and axes
        ax.set_aspect('equal', 'datalim')
        if (self.ax_width_lim is not None):
            ax.set_xlim(self.ax_width_lim)
        if (self.ax_height_lim is not None):
            ax.set_ylim(self.ax_height_lim)
        ax.minorticks_on()
        ax.xaxis.set_major_formatter(FuncFormatter(format_inches))
        ax.yaxis.set_major_formatter(FuncFormatter(format_inches))
        # Selected point?
        if (self.selected is not None):
            ax.plot([self.selected.x], [self.selected.y], marker='x', markersize=10, color="red")

    def plot_plan_view(self, ax):
        """Plot plan view of self.gouge on matplotlib axes ax."""

        # Size and axes
        ax.set_aspect('equal', 'datalim')
        if (self.ax_length_lim is not None):
            ax.set_xlim(self.ax_length_lim)
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

        Width profile points can be moved only in x axis, sheer points can be moved
        in x and y.
        """
        w = self.selected.x
        y = self.selected.y
        s = self.selected.station
        for j, wy in enumerate(self.gouge.breadths[s]):
            if (wy[0] == w and wy[1] == y):
                self.selected.x += dx
                self.gouge.breadths[s][j] = [self.selected.x, y]
                self.gouge._reset_lazy_calcs()
                return
            if (wy[0] == -w and wy[1] == y):
                self.selected.x += dx
                self.gouge.breadths[s][j] = [-self.selected.x, y]
                self.gouge._reset_lazy_calcs()
                return
        # else sheer point?
        if (w == self.gouge.sheer_breadth[s] and y == self.gouge.sheer_height[s]):
                self.selected.x += dx
                self.selected.y += dy
                self.gouge.sheer_breadth[s] = self.selected.x
                self.gouge.sheer_height[s] = self.selected.y
                self.gouge._reset_lazy_calcs()
                return
        if (w == -self.gouge.sheer_breadth[s] and y == self.gouge.sheer_height[s]):
                self.selected.x += dx
                self.selected.y += dy
                self.gouge.sheer_breadth[s] = -self.selected.x
                self.gouge.sheer_height[s] = self.selected.y
                self.gouge._reset_lazy_calcs()
                return
        logging.warn("Failed to match point in move_point_width_profile")

    def plot_station(self, station, ax, region=None):
        """Plot one station of gouge on matplotlib axes ax.

        This plot is designed for printing so fit onto some mutliple of
        9 by 15 sheets.
        """
        xx, yy = self.gouge.breadth_curve(station)
        # What are x & y limits at this station if not given
        if (region is None):
            region = Region(xx, yy, mirror_x=True)
            logging.info("Station plot area [%d -- %d, %d -- %d]" %
                         (region.min_x, region.max_x, region.min_y, region.max_y))
        # Defined widths as points, station label inside right sheer
        ax.text(xx[-1] - 2.0, yy[-1] - 1.0, "Station %d" % station)
        # Interpolated line
        x2, y2 = self.gouge.breadth_fairer(station).curve()
        ax.plot(xx, yy, 'x', color="red")
        ax.plot([-x for x in xx], yy, 'x', color="red")
        ax.plot(x2, y2, '-', color="black")
        ax.set_aspect('equal', 'datalim')
        ax.grid(color='black', linewidth=1)
        ax.xaxis.set_major_formatter(FuncFormatter(format_inches))
        ax.yaxis.set_major_formatter(FuncFormatter(format_inches))

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
            for station in self.gouge.stations:
                xx, yy = self.gouge.breadth_curve(station)
                first_or_last = (station == min(self.gouge.stations) or station == max(self.gouge.stations))
                for ax, sheet_region in self.multi_sheet_ax_generator(pdf, xx, yy, mirror_x=True, add_form_lines=first_or_last):
                    self.plot_station(station, ax, sheet_region)
                    plt.title("Station %d, sheet %s" % (station, str(sheet_region)))
            # Profile curve
            xp, yp = self.gouge.profile_fairer.curve()
            xsp, ysp = self.gouge.sheer_profile_fairer.curve()
            # Bow profile
            br = min(self.gouge.station_positions) + 1
            brl = self.gouge.station_positions[br]
            brl2 = self.gouge.station_positions[br - 1] - brl
            xx = []
            yy = []
            for x, y in self.gouge.bow_profile:
                xx.append(x - brl)
                yy.append(y)
            # and kheel line at station br - 1 and br
            xx.append(0.0)
            yy.append(self.gouge.profile_height[br])
            xx.append(0.0)
            yy.append(self.gouge.profile_height[br])
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
            sr = max(self.gouge.station_positions) - 1
            srl = self.gouge.station_positions[sr]
            srl2 = srl - self.gouge.station_positions[sr + 1]
            xx = []
            yy = []
            for x, y in self.gouge.stern_profile:
                xx.append(srl - x)
                yy.append(y)
            # and kheel line at station sr
            xx.append(0.0)
            yy.append(self.gouge.profile_height[sr])
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
