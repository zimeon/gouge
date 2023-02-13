"""Gouge model.

"""

import logging
import re
import math
import numpy
import time

from util import format_inches, format_feet_inches, fill_range
from fairing import FairCurve


class Gouge(object):
    """Class to digitally loft a canoe gouge design."""

    def __init__(self):
        """Initialize Gouge object, optionally read from filename.

        Sadly, all measurements are in inches because that is the
        way the industry works
        """
        self.title = "Gouge"
        self.bar_diameter = 0.5      # bar diameter in inches
        self.bar_channel_angle = 1   # angle from vertical to top of channel
        self.channel = [], []        # channel curve from middle bottom to bar edge
        self.profile = [], []        # profile of cutting edge
        # Grinding setup
        self.wheel_diameter = 8.0    # inches
        self.nose_angle = 50.0       # degrees
        # Data formatting
        self.units = 'inches'
        # Initialize stored values for lazy calculation
        self._reset_lazy_calcs()

    @property
    def bar_radius(self):
        """Bar radius."""
        return self.bar_diameter / 2.0

    @property
    def bar_top_height(self):
        """Bar height at top of channel."""
        return math.cos(self.bar_channel_angle) * self.bar_diameter / 2.0

    @property
    def bar_top_width(self):
        """Width in bar at top of channel."""
        return math.sin(self.bar_channel_angle) * self.bar_diameter / 2.0

    def _reset_lazy_calcs(self):
        # Initialize/reset values for lazy eval
        pass

    def set_channel_parabola(self):
        """Set self.channel to be a parabola."""
        cx, cy = [], []
        r = self.bar_radius
        last_x = 0.0
        last_y = 0.0
        for f in numpy.arange(0.0, +1.1, 0.1):
            x = f * r
            y = f*f * r
            # Have we gone outside bar?
            if (x * x + y * y) >= r * r:
                # Calculate intercept for line from last_x, last_y
                # to x, y with the circle of diameter r
                for m in numpy.arange(0.0, 1.0, 0.01):
                    xx = m * (x - last_x) + last_x
                    yy = m * (y - last_y) + last_y
                    if (xx * xx + yy * yy) >= r * r:
                        break
                # Now calculate angle of intercept with bar
                self.bar_channel_angle = math.atan2(xx, yy)
                break
            # Still inside bar diameter
            cx.append(x)
            cy.append(y)
            last_x = x
            last_y = y
        # Now have angle, add last point exactly on bar edge
        x = r * math.sin(self.bar_channel_angle)
        y = r * math.cos(self.bar_channel_angle)
        cx.append(x)
        cy.append(y)
        self.channel = cx, cy

    def set_profile_flat(self, angle=30.0):
        """Set up flat wing profile at angle from centerline."""
        # First find bottom of channel
        ybot = self.channel[1][0]
        logging.info("ybot = %f" % ybot)
        # Find y value at end of wing (=channel top edge)
        ytop = math.sin(self.bar_channel_angle) * self.bar_radius
        dy = ytop - ybot
        dz = dy / math.tan(math.radians(angle))
        # Genetate 100 points aling this line
        py, pz = [], []
        for m in numpy.linspace(0, 1.0, 100):
            y = m * dy + ybot
            z = -m * dz
            py.append(y)
            pz.append(z)
        self.profile = py, pz

    def solve(self):
        """Solve model ready for plotting etc.."""
        pass
        self._reset_lazy_calcs()

    def bar_end_curve(self):
        """Curve of bar end.

        This is the curve of the end of the outside of the bar,
        the trailing edge of the ground area.

        FIXME - no z info yet!
        """
        bx, by, bz = [], [], []
        r = self.bar_radius
        for ang in numpy.linspace(self.bar_channel_angle, 2 * math.pi - self.bar_channel_angle, 100):
            x = math.sin(ang) * r
            y = math.cos(ang) * r
            bx.append(x)
            by.append(y)
            bz.append(0)
        return bx, by, bz

    def cutting_edge_curve(self, half=False):
        """Curve defining the cutting edge.

        This is the curve of the cutting edge. Looking in
        x,y (end view) it follows the channel. Looking in
        z,y (profile view) it follows the grind profile.

        If half is set True then will just return the curve
        from the top left wing (looking end on, +y, -x) down
        to the center of the channel.
        """
        cx, cy, cz = [], [], []
        for j in range(len(self.channel[0]) - 1, 0, -1):
            cx.append(-self.channel[0][j])
            cy.append(self.channel[1][j])
            cz.append(numpy.interp(self.channel[1][j], self.profile[0], self.profile[1]))
        for j in range(0, len(self.channel[0]), 1):
            cx.append(self.channel[0][j])
            cy.append(self.channel[1][j])
            cz.append(numpy.interp(self.channel[1][j], self.profile[0], self.profile[1]))
            if half:
                break  # Stop after bottom middle point
        return cx, cy, cz
