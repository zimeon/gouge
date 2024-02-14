"""Gouge model."""

import logging
import math
import numpy
from scipy.linalg import norm
from scipy.interpolate import CubicSpline
from jig import Jig
from util import unit_vector, rotate_point


class NoInterceptException(Exception):
    """Grinding curve does not intercept bar."""


class Gouge(object):
    """Class to model a gouge and its ground edge."""

    def __init__(self, nose_angle_degrees=50.0):
        """Initialize Gouge object.

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
        self.nose_angle = math.radians(nose_angle_degrees)
        self.jig_angle = math.radians(40.0)
        self.jig_length = 9.0        # inches
        # Data formatting
        self.units = 'inches'
        # Parameters for model
        self.num_points = 33
        self.initialize()

    def initialize(self):
        """Initialize calculations for grinding solution."""
        self.spline = None               # spline curve of cutting edge
        self.grinding_edge_point = {}
        self.grinding_edge_tangent = {}
        self.grinding_wheel_normal = {}
        self.grinding_wheel_tangent = {}
        self.grinding_tail_point = {}
        self.grinding_line = {}          # set of sets of points defining grinding lines
        # Extension of grind around bar (not flute)
        self.grinding_extension_curve = list()

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

    @property
    def wheel_radius(self):
        """Return radius of grinding wheel."""
        return self.wheel_diameter / 2.0

    def set_channel_parabola(self):
        """Set self.channel to be a parabola.

        Parabola starts 0.1 * bar_diameter below center.
        """
        cx, cy = [], []
        r = self.bar_radius
        last_x, last_y = 0.0, 0.0
        for f in numpy.arange(0.0, +1.1, 0.1):
            x = f * r
            y = f * f * r - 0.1 * self.bar_diameter
            # Have we gone outside bar?
            if (x * x + y * y) >= r * r:
                x, y, z = self.bar_intercept(last_x, last_y, 0.0, x, y, 0.0)
                # Have intercept add last point on bar edge
                cx.append(x)
                cy.append(y)
                break
            # Still inside bar diameter
            cx.append(x)
            cy.append(y)
            last_x = x
            last_y = y
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
        self.initialize()
        self.cutting_edge_mid_point = (self.num_points - 1) / 2
        self.spline = self.cutting_edge_curve()
        self.solve_grinding_for_edge_points()

    def bar_end_curve(self):
        """Curve of bar end.

        This is the curve of the end of the outside of the bar,
        the trailing edge of the ground area.

        FIXME - no z info yet! This should really be the curve of the trailing
        edge of the grinding curve plus any that wraps around as the leading
        egde on the outside of the bar rather than in the flute.
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
        """Calculate points defining the cutting edge curve.

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
        return CubicSpline(d, numpy.c_[cx, cy, cz], extrapolate=True)

    def cutting_edge_range(self, half=False):
        """Evenly space points in range -1.0 to 1.0.

        Designed to follow the parameterization of the cutting
        edge spline with self.num_points in total

        The set of `number` points (use odd number so there is
        a point at the nose) is approximately eveny distributed
        along the cutting edge, derived from the spline
        curve self.cutting_edge_curve().

        `number` refers to the whole curve whether or not `half`
        is set True. In that case there will be `(number + 1) / 2`
        points.
        """
        if half:
            return numpy.linspace(-1.0, 0.0, int((self.num_points + 1) / 2))
        # else:
        return numpy.linspace(-1.0, 1.0, self.num_points)

    def cutting_edge_curve_points(self, half=False):
        """Set of evenly spaced points along the cutting edge."""
        cx, cy, cz = [], [], []
        for aj in self.cutting_edge_range(half=half):
            x, y, z = self.spline(aj)
            cx.append(x)
            cy.append(y)
            cz.append(z)
        return cx, cy, cz

    def solve_grinding_for_edge_points(self):
        """Calculate as set of grinding lines from the edge points.

        Also, separately populate self.grinding_tail_point with the
        set of points for the tail edges of the grinding lines on
        the outside of the bar.

        Start by finding the grinding jig angle at each cutting edge
        point. We assert that at each point on the cutting edge the
        vector along the edge must be in the plane of the grinding
        wheel surface in order to be part of the ground curve. From
        this we can find the required grinding jig angle at that point.
        Or, if we can't, then the suggested curve is impossible
        and raise an exception.
        """
        logging.info("Solving for grinding edge...")
        jig = Jig(angle=self.jig_angle, length=self.jig_length,
                  nose_angle=self.nose_angle)
        for aj in self.cutting_edge_range(half=True):
            logging.info("=== aj = %f" % aj)
            edge_point = numpy.array(self.spline(aj))
            edge = unit_vector(self.spline(aj, 1))
            logging.info(" edge = %s", str(edge))
            min_dot = 99.0
            jig_rotation = 999.0
            for jig_rot in numpy.linspace(0.0, math.radians(-120.0), 500):
                gwn = jig.to_tool_coords(jig.grinding_wheel_normal(), rotation=jig_rot)
                # logging.info(" gwn = %s" % str(gwn))
                # Is edge in grinding wheel plane? Dot product is approx zero
                dot = numpy.dot(edge, gwn)
                if abs(dot) < min_dot:
                    min_dot = abs(dot)
                    jig_rotation = jig_rot
            # Have jig rotation angle, now save grinding line
            if min_dot > 0.01:
                logging.info(" FAILED rot=%.1f dot = %.4f", math.degrees(jig_rotation), min_dot)
            else:
                logging.info(" SOLVED rot=%.1f dot = %.4f", math.degrees(jig_rotation), min_dot)
                gwn = jig.to_tool_coords(jig.grinding_wheel_normal(), rotation=jig_rotation)
                gwt = jig.to_tool_coords(jig.grinding_wheel_tangent(), rotation=jig_rotation)
                self.grinding_edge_point[aj] = edge_point
                self.grinding_edge_tangent[aj] = edge
                self.grinding_wheel_normal[aj] = gwn
                self.grinding_wheel_tangent[aj] = gwt
                gwaxis = numpy.cross(gwn, gwt)
                logging.info("edge point = %s", str(edge_point))
                self.grinding_line[aj] = self.grinding_curve(edge_point, gwn, gwaxis)
                # Extract last point
                self.grinding_tail_point[aj] = numpy.array([
                    self.grinding_line[aj][0][-1],
                    self.grinding_line[aj][1][-1],
                    self.grinding_line[aj][2][-1]])
                # If this is the top of the flute (aj=-1.0) and the grinding
                # curve has any length, then using the same jig angle extend
                # the curve until it meets the outside of the bar
                grinding_length = norm(edge_point - self.grinding_tail_point[aj])
                logging.info(" length of grinding line = %s", grinding_length)
                if (aj == -1.0) and (grinding_length > 0.01):
                    logging.info(" Calculating extended grinding surface...")
                    self.extended_grinding_surface(edge_point, self.grinding_tail_point[aj], gwn, gwaxis)

    def extended_grinding_surface(self, edge_point, tail_point, gwn, gwaxis):
        """Calculate the entended grinding curve on the outside of the bar.

        Starting from the edge point at the top of the flute (edge_point) we
        move in the direction of the grinding wheel axis (gwaxis) until the
        grinding wheel curve no longer intercepts the bar at all.

        At very sharp nose angles (say 30deg) then we need to be able to extend
        the curve a long way. This case determines the factor 2*bar_radius.

        As we calculate back, we count the number
        """
        lead_points = [edge_point]
        tail_points = [tail_point]
        for m in numpy.linspace(0.01 * self.bar_radius, 2.0 * self.bar_radius, 500):
            offset = m * gwaxis
            logging.info(" EGS: offset = %s", offset)
            start_point = edge_point - offset
            logging.info(" EGS: start_point = %s", start_point)
            try:
                # Need to do this with greater accuracy (more steps) than the usual
                # calculation of a gruinding curve to plot, because we are looking for
                # the intercepts with the bar boundary
                grinding_line = self.grinding_curve(start_point, gwn, gwaxis, start_outside_bar=True, steps=100)
            except NoInterceptException as e:
                logging.info(" EGS: No intercept, edge of BAR!")
                break
            # Pick off leading and trailing points of curve
            lead_points.append(numpy.array([
                grinding_line[0][0],
                grinding_line[1][0],
                grinding_line[2][0]]))
            tail_points.append(numpy.array([
                grinding_line[0][-1],
                grinding_line[1][-1],
                grinding_line[2][-1]]))
            logging.info(" EGS: lead_point = %s", lead_points[-1])
            logging.info(" EGS: tail_point = %s", tail_points[-1])
        # Now assemble as one line from top of flute to tail curve
        tail_points.reverse()
        self.grinding_extension_curve = lead_points + tail_points
        logging.info("Num extension points = %d", len(self.grinding_extension_curve))

    def grinding_curve(self, edge_point, gwn, gwaxis, start_outside_bar=False, steps=20):
        """Calculate grinding wheel curve from cutting edge to bar edge.

        Starting point on cutting edge is (ex, ey, ez).
        Grinding wheel surface normal or radius vector is gwn
        Girnding wheel axis vector is gwaxis
        Everything is in tool coordinate system

        If start_outside_bar if false then we know we are starting outside
        the bar and may or may not intercept it. If there is no intercept then
        raise a NoInterceptException.
        """
        # Calculate center of wheel in tool coordinate
        wheel_center = edge_point - self.wheel_radius * gwn
        logging.debug("Wheel center = %s", wheel_center)
        max_angle_change = self.bar_diameter * 1.5 / self.wheel_radius  # radians
        r = self.bar_diameter / 2.0
        gx, gy, gz = [], [], []
        last_x, last_y, last_z = edge_point
        in_bar = not start_outside_bar
        for rot in numpy.linspace(0.0, -max_angle_change, steps):
            # Rotate edge_point about gwaxis at wheel_center by rot radians
            x, y, z = rotate_point(edge_point, wheel_center, gwaxis, rot)
            # Is this point outside of the bar?
            if (x * x + y * y) >= r * r:
                if in_bar:
                    # We have gone outside bar
                    x, y, z = self.bar_intercept(last_x, last_y, last_z, x, y, z)
                    # Have intercept, add last point
                    gx.append(x)
                    gy.append(y)
                    gz.append(z)
                    break
                else:
                    # Still outside the bar from a start outside
                    pass
            else:
                if not in_bar:
                    # Newly inside the bar diameter, find intercept
                    in_bar = True
                    x, y, z = self.bar_intercept(x, y, z, last_x, last_y, last_z)
                # Inside bar diameter, record point
                gx.append(x)
                gy.append(y)
                gz.append(z)
            last_x = x
            last_y = y
            last_z = z
        else:
            if in_bar:
                logging.info("Failed to find trailing bar edge up to rot=%.2f", rot)
            else:
                logging.info("Never intercepted with bar")
                raise NoInterceptException()
        return list((gx, gy, gz))

    def bar_intercept(self, x1, y1, z1, x2, y2, z2):
        """Calculate intercept with bar surface.

        Find intercept point between (x1,y1,z1) and
        (x2,y2,z2) and the bar surface. Assumes that
        (x1,y1,z1) is inside the bar, (x2,y2,z2)
        outside.
        """
        rsqrd = self.bar_radius * self.bar_radius
        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1
        for m in numpy.arange(0.0, 1.0, 0.01):
            x = m * dx + x1
            y = m * dy + y1
            z = m * dz + z1
            if (x * x + y * y) >= rsqrd:
                break
        # Now have very close to intercept, return point exactly
        # on bar edge for x and y, with same z as calculated.
        end_angle = math.atan2(x, y)
        x = self.bar_radius * math.sin(end_angle)
        y = self.bar_radius * math.cos(end_angle)
        return x, y, z
