"""Grinding Jig Model."""

import logging
import math
import numpy
from scipy.interpolate import CubicSpline
from vector import unit_vector


class GrindingJig(object):
    """Model for a gouge grinding jig."""

    def __init__(self, nose_angle=math.radians(50.0), setup=None):
        """Initialize GrindingJig object.

        Properties:
        - length -- point to gouge tip distance in inches
        - angle -- offset angle in radians
        - nose_angle -- nose angle on gouge which is the grinding
            wheel tangent when the jig is upright/centered
        """
        if setup == 'thompson':
            self.length = 9.37
            self.angle = math.radians(33.7)
        else:
            self.length = 9.0                # point to gouge tip
            self.angle = math.radians(40.0)  # offset angle of bar/flute
        self.nose_angle = nose_angle     # nose angle on gouge (radians)

    def grinding_wheel_normal(self):
        """Unit vector normal to the grinding wheel surface at contact.

        In jig/wheel coordinates. Points "up" -- +ve y.
        """
        return numpy.array([math.cos(self.nose_angle), math.sin(self.nose_angle), 0.0])

    def grinding_wheel_tangent(self):
        """Unit vector tangent to the grinding wheel surface at contact.

        In jig/wheel coordinates. Points "up" -- +ve y.
        """
        return numpy.array([math.sin(self.nose_angle), math.cos(self.nose_angle), 0.0])

    def tool_vectors(self, rotation=0.0):
        """Calculate the tool y and z unit vectors at given jig rotation.

        Vectors are
        """
        wx = self.length * math.cos(self.angle)
        wy = self.length * math.sin(self.angle)
        wz = 0
        f = wx * math.sin(self.angle)
        g = f * math.sin(self.angle)
        h = f * math.cos(self.angle)
        elbow_x = g * (1.0 - math.cos(rotation))
        elbow_y = wy - h * (1.0 - math.cos(rotation))
        elbow_z = f * math.sin(rotation)
        y = numpy.array([elbow_x, elbow_y, elbow_z])
        z = numpy.array([(wx - elbow_x), (wy - elbow_y), (wz - elbow_z)])
        return y, z

    def tool_rotation_matrix(self, rotation=0.0):
        """Matrix to rotate tool coordinates to jig/wheel coords."""
        y, z = self.tool_vectors(rotation)
        y_hat = unit_vector(y)
        z_hat = unit_vector(z)
        x_hat = numpy.cross(y_hat, z_hat)
        # logging.info("   === jig.rot = %.1f" % math.degrees(rotation))
        # logging.info("   x_hat, |x_hat| = %s, %.5f" % (str(x_hat), numpy.linalg.norm(x_hat)))
        # logging.info("   y_hat, |y_hat| = %s, %.5f" % (str(y_hat), numpy.linalg.norm(y_hat)))
        # logging.info("   z_hat, |z_hat| = %s, %.5f" % (str(z_hat), numpy.linalg.norm(z_hat)))
        # logging.info("   y_hat.z_hat = %.5f" % (numpy.dot(y_hat, z_hat)))
        return numpy.matrix([x_hat, y_hat, z_hat])  # .transpose()

    def grinding_wheel_normal_in_tool_coords(self, rotation):
        """Normal to grinding wheel surface in tool coordinates."""
        r = self.tool_rotation_matrix(rotation=math.radians(rotation))
        # logging.info(" r = %s" % str(r))
        # Get grinding wheel normal in tool coords
        return (self.grinding_wheel_normal() * r).transpose()

    def grinding_wheel_tangent_in_tool_coords(self, rotation):
        """Tangent to grinding wheel surface in tool coordinates."""
        r = self.tool_rotation_matrix(rotation=math.radians(rotation))
        # logging.info(" r = %s" % str(r))
        # Get grinding wheel normal in tool coords
        return (self.grinding_wheel_tangent() * r).transpose()
