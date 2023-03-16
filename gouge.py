"""Gouge model."""

import logging
import math
import numpy
from scipy.interpolate import CubicSpline
from jig import Jig
from vector import unit_vector, rotate_point


class Gouge(object):
    """Class to model a gouge and its ground edge."""

    def __init__(self):
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
        self.nose_angle = math.radians(50.0)   # degrees
        # Data formatting
        self.units = 'inches'
        # Grinding solutions
        self.spline = None           # spline curve of cutting edge
        self.grinding_line = {}      # set of sets of points defininf grinding lines

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

    def solve(self, num_points=21):
        """Solve model ready for plotting etc.."""
        self.num_points = 21
        self.cutting_edge_mid_point = (self.num_points - 1) / 2
        self.spline = self.cutting_edge_curve()
        self.solve_grinding_for_edge_points()

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
        """Find grinding jig angle at each cutting edge point.

        We assert that at each point on the cutting edge the vector
        along the edge must be in the plane of the grinding wheel
        surface in order to be part of the ground curve. From this
        we can find the required grinding jig angle at that point.
        Or, if we can't, then the suggested curve is impossible
        and raise an exception.
        """
        logging.info("Solving for grinding edge...")
        jig = Jig(self.nose_angle)
        for aj in self.cutting_edge_range(half=True):
            logging.info("=== aj = %f" % aj)
            x, y, z = self.spline(aj)
            edge = unit_vector(self.spline(aj, 1))
            logging.info(" edge = %s", str(edge))
            min_dot = 99.0
            jig_rotation = 999.0
            for a in numpy.linspace(0, -120.0, 500):
                gwn = jig.grinding_wheel_normal_in_tool_coords(rotation=math.radians(a))
                # logging.info(" gwn = %s" % str(gwn))
                # Is edge in grinding wheel plane? Dot product is approx zero
                dot = numpy.dot(edge, gwn)
                if abs(dot) < abs(min_dot):
                    min_dot = dot
                    jig_rotation = a
            # Have jig rotation angle, now save grinding line
            logging.info(" rot=%.1f dot = %.4f", jig_rotation, min_dot)
            gwn = jig.grinding_wheel_normal_in_tool_coords(rotation=math.radians(jig_rotation))
            gwt = jig.grinding_wheel_tangent_in_tool_coords(rotation=math.radians(jig_rotation))
            gwaxis = numpy.cross(gwn, gwt)
            edge_point = numpy.array(self.spline(aj))
            logging.info("edge point = %s", str(edge_point))
            self.grinding_line[aj] = self.grinding_curve(edge_point, gwn, gwaxis)

    def grinding_curve(self, edge_point, gwn, gwaxis):
        """Calculate grinding wheel curve from cutting edge to bar edge.

        Starting point on cutting edge is (ex, ey, ez).
        Grinding wheel surface normal or radius vector is gwn
        Girnding wheel axis vector is gwaxis
        Everything is in tool coordinate system
        """
        # Calculate center of wheel in tool coordinate
        wheel_center = edge_point - self.wheel_radius * gwn
        # Translate to have wheel center = (0,0,0)
        ep = edge_point - wheel_center
        logging.info("ep=%s", ep)
        logging.info("radius=%.1f norm=%.1f", self.wheel_radius, numpy.linalg.norm(ep))
        max_angle_change = self.bar_diameter / self.wheel_radius  # radians
        r = self.bar_diameter / 2.0
        gx, gy, gz = [], [], []
        last_x, last_y, last_z = ep
        for rot in numpy.linspace(0.0, max_angle_change, 20):
            # Rotate edge_point about gwaxis at wheel_center by rot radians
            x, y, z = rotate_point(edge_point, wheel_center, gwaxis, rot)
            # Have we gone outside bar?
            if (x * x + y * y) >= r * r:
                x, y, z = self.bar_intercept(last_x, last_y, last_z, x, y, z)
                # Have intercept, add last point
                gx.append(x)
                gy.append(y)
                gz.append(z)
                break
            # Still inside bar diameter
            gx.append(x)
            gy.append(y)
            gz.append(z)
            last_x = x
            last_y = y
            last_z = z
        else:
            logging.info("Failed to find bar edge up to rot=%.2f", rot)
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
        # Now have very close to intercept, return point exactly
        # on bar edge for x and y, with same z as calculated.
        end_angle = math.atan2(x, y)
        x = self.bar_radius * math.sin(end_angle)
        y = self.bar_radius * math.cos(end_angle)
        return x, y, z
