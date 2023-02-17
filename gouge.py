"""Gouge model.

"""

import logging
import math
import numpy
from scipy.interpolate import CubicSpline


class Gouge(object):
    """Class to digitally loft a canoe gouge design."""

    def __init__(self):
        """Initialize Gouge object, optionally read from filename.

        - channel = [x array] [y array] that represents one side
                    the channel profile from the nose to the top
                    of the +ve x side. channel[1][0] is the y
                    position of the nose.

        Sadly, all measurements are in inches because that is the
        way the industry works ;-)
        """
        self.title = "Gouge"
        self.bar_diameter = 0.5      # bar diameter in inches
        self.bar_channel_angle = 1   # angle from vertical to top of channel
        self.channel = [], []        # channel curve from middle bottom to bar edge
        self.profile = [], []        # profile of cutting edge
        # Grinding setup
        self.wheel_diameter = 8.0    # inches
        self.nose_angle = math.radians(50.0)   # degrees
        # Data formatting
        self.units = 'inches'

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

    @property
    def channel_bottom_y(self):
        """Channel bottom y value, also nose y value."""
        return self.channel[1][0]

    def set_channel_parabola(self):
        """Set self.channel to be a parabola.

        Parabola starts 0.1 * bar_diameter below center.
        """
        cx, cy = [], []
        r = self.bar_radius
        last_x, last_y = 0.0, 0.0
        xx, yy = 0.0, 0.0
        for f in numpy.arange(0.0, +1.1, 0.1):
            x = f * r
            y = f*f * r - 0.1 * self.bar_diameter
            # Have we gone outside bar?
            if (x * x + y * y) >= r * r:
                xx, yy, zz = self.bar_intercept(
                                 last_x, last_y, 0.0,
                                 x, y, 0.0)
                break
            # Still inside bar diameter
            cx.append(x)
            cy.append(y)
            last_x = x
            last_y = y
        # Now have angle, add last point exactly on bar edge
        self.bar_channel_angle = math.atan2(xx, yy)
        x = r * math.sin(self.bar_channel_angle)
        y = r * math.cos(self.bar_channel_angle)
        cx.append(x)
        cy.append(y)
        self.channel = cx, cy

    def set_profile_flat(self, angle=30.0):
        """Set up flat wing profile at angle from centerline."""
        # First find bottom of channel
        ybot = self.channel_bottom_y
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

    def cutting_edge_points(self, half=False):
        """Points defining the cutting edge curve.

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

    def cutting_edge_curve(self):
        """Spline curve for the cutting edge.

        Spline interpolation of self.cutting_edge.points()
        that is parametrized from -1.0 to +1.0, where 0.0 is
        the nose. The parameterization is done so that the is
        approximately linear relation to distance along the
        edge.
        """
        cx, cy, cz = self.cutting_edge_points(half=False)
        d_tot = 0.0
        d = [0.0]
        last_x, last_y, last_z = None, None, None
        for ex, ey, ez in zip(cx, cy, cz):
            if last_x is not None:
                d_tot += math.sqrt((ex - last_x) ** 2 + (ey - last_y) ** 2 + (ez - last_z) ** 2)
                d.append(d_tot)
            last_x, last_y, last_z = ex, ey, ez
        scale = 2.0 / d_tot
        d = numpy.add(numpy.multiply(d, scale), -1.0)
        spline = CubicSpline(d, numpy.c_[cx, cy, cz], extrapolate=True)
        #for j in range(0, len(d)):
        #    print(d[j], c(d[j]))
        return spline

    def cutting_edge_curve_points(self, number=21, half=False):
        """Set of evenly spaced points along the cutting edge.

        The set of `number` points (use odd number so there is
        a point at the nose) is approximately eveny distributed
        along the cutting edge, derived fro mthe spline
        curver self.cutting_edge_curve().

        `number` refers to the whole curve whether or not `half`
        is set True. In that case there will be `(number + 1) / 2`
        points.
        """
        spline = self.cutting_edge_curve()
        cx, cy, cz = [], [], []
        if half:
            range = numpy.linspace(-1.0, 0.0, int((number + 1) / 2))
        else:
            range = numpy.linspace(-1.0, 1.0, number)
        for aj in range:
            x, y, z = spline(aj)
            cx.append(x)
            cy.append(y)
            cz.append(z)
        return cx, cy, cz

    def grinding_curve(self, ex, ey, ez):
        """Calculate grining wheel curve from cutting edge to bar edge.

        Starting point on cutting edge is (ex, ey, ez).
        """
        # Calculate z and y distances (+ve) of wheel center from origin
        wcx = 0.0
        wcy = math.cos(self.nose_angle) * self.wheel_diameter - ey
        wcz = math.sin(self.nose_angle) * self.wheel_diameter
        return self.grinding_curve_from_point(ex, ey, ez,
                                              wcx, wcy, wcz)

    def grinding_curve_from_point(self,
                                  ex, ey, ez,
                                  wcx, wcy, wcz):
        max_angle_change = self.bar_diameter / self.wheel_diameter
        gx, gy, gz = [ex], [ey], [ez]
        r = self.bar_radius
        last_x, last_y, last_z = ex, ey, ez
        xx, yy, zz = 0.0, 0.0, 0.0
        for a in numpy.arange(self.nose_angle, self.nose_angle + max_angle_change, max_angle_change / 20.0):
            x = ex
            y = math.cos(a) * self.wheel_diameter - wcy
            z = ez + wcz - math.sin(a) * self.wheel_diameter
            # Have we gone outside bar?
            if (x * x + y * y) >= r * r:
                xx, yy, zz = self.bar_intercept(
                                 last_x, last_y, last_z,
                                 x, y, z)
                break
            # Still inside bar diameter
            gx.append(x)
            gy.append(y)
            gz.append(z)
            last_x = x
            last_y = y
            last_z = z
        # Now have intercept, add last point exactly on bar edge
        # Now calculate angle of intercept with bar
        end_angle = math.atan2(xx, yy)
        x = r * math.sin(end_angle)
        y = r * math.cos(end_angle)
        z = zz
        gx.append(x)
        gy.append(y)
        gz.append(z)
        return gx, gy, gz

    def bar_intercept(self, x1, y1, z1, x2, y2, z2):
        """Calculate intercept with bar surface.

        Find intercept point between (x1,y1,z1) and
        (x2,y2,z2) and the bar surface. Assumes that
        (x1,y1,z1) is inside the bar, (x2,y2,z2)
        outside.
        """
        rsqrd = self.bar_radius * self.bar_radius
        for m in numpy.arange(0.0, 1.0, 0.01):
            x = m * (x2 - x1) + x1
            y = m * (y2 - y1) + y1
            z = m * (z2 - z1) + z1
            if (x * x + y * y) >= rsqrd:
                break
        return x, y, z


class GrindingJig(object):
    """Model for a gouge grinding jig."""

    def __init__(self):
        """Initialize GrindingJig object.

        Properties:
        - length -- point to gouge tip distance in inches
        - angle -- offset angle in radians
        """
        self.length = 8.0           # point to gouge tip
        self.angle = radians(30.0)  # offset angle of bar/flute

    def point_position(self, nose_y, nose_angle):
        """Calculate point position from gouge nose position and angle.

        Assume point is centered and jig upright when on
        gouge nose so that we will have a symmetric
        grind. We thus do not consider x coordinates, just a +ve z
        and a -ve y.
        """
        pass
