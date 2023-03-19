"""Grinding Jig Model."""

import logging
import math
import numpy
from scipy.interpolate import CubicSpline
from vector import unit_vector


class Jig(object):
    """Model for a gouge grinding jig."""

    def __init__(self, nose_angle=math.radians(50.0), setup=None):
        """Initialize Jig object.

        Properties:
        - length -- point to gouge tip distance in inches
        - angle -- offset angle in radians
        - nose_angle -- nose angle on gouge which is the grinding
            wheel tangent when the jig is upright/centered

        Jig coordinate system has tip of jig at 0,0,0. With x perpendicular
        to the jig when centered (thus x=0 for tip, elbow, wheel contact and
        wheel center); y is up; and z is from tip to tool to wheel center. This
        is the same axes directions as the tool when the tool is centered.
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

        In jig/wheel coordinates. Points "up" -- 0 x, +ve y, -ve z.
        """
        return numpy.array([0.0, math.cos(self.nose_angle), -math.sin(self.nose_angle)])

    def grinding_wheel_tangent(self):
        """Unit vector tangent to the grinding wheel curve at contact.

        In jig/wheel coordinates. Points "up" -- 0 x, +ve y, +ve z.
        """
        return numpy.array([0.0, math.sin(self.nose_angle), math.cos(self.nose_angle)])

    def tool_vectors(self, rotation=0.0):
        """Calculate the tool y and z unit vectors at given jig rotation.

        Rotation is in radians. Vectors are not normalized to unit length
        and define the tool y and z directions.
        """
        wx = 0.0
        wy = self.length * math.sin(self.angle)
        wz = self.length * math.cos(self.angle)
        f = wy * math.cos(self.angle)
        elbow_x = -f * math.sin(rotation)
        elbow_y = wy * (1.0 - math.cos(self.angle) ** 2.0 * (1.0 - math.cos(rotation)))
        elbow_z = f * math.sin(self.angle) * (1.0 - math.cos(rotation))
        tool_y = numpy.array([elbow_x, elbow_y, elbow_z])
        tool_z = numpy.array([(wx - elbow_x), (wy - elbow_y), (wz - elbow_z)])
        return unit_vector(tool_y), unit_vector(tool_z)

    def tool_rotation_matrix(self, rotation=0.0):
        """Matrix to rotate a vector in tool coordinates to jig/wheel coords.

        Rotation is in radians. This is just a rotation and cannot not deal
        with the translation for a point.

        x = y cross z
        """
        y_hat, z_hat = self.tool_vectors(rotation)
        x_hat = numpy.cross(y_hat, z_hat)
        return numpy.array([x_hat, y_hat, z_hat]).transpose()

    def to_tool_coords(self, vector, rotation):
        """Rotate vector in jig/wheel coordinates to tool coordiates.

        For case where jig is at given rotation (radians). rotation=0.0
        is symmetic/stright up-down.
        """
        return numpy.matmul(self.tool_rotation_matrix(rotation), vector)
