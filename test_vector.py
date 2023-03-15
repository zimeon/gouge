"""Tests for vector.py."""
import unittest
import math
import numpy
import numpy.testing as npt

from vector import unit_vector, rotate_point


class TestVector(unittest.TestCase):

    def test01_unit_vector(self):
        npt.assert_allclose(unit_vector(numpy.array([1.0, 0.0, 0.0])),
                            numpy.array([1.0, 0.0, 0.0]))
        npt.assert_allclose(unit_vector(numpy.array([1.0, 1.0, 1.0])),
                            numpy.array([0.57735027, 0.57735027, 0.57735027]))

    def test02_rotate_point_about_orgin(self):
        # Rotation around z with center=(0,0,0)
        point = numpy.array([1.0, 0.0, 0.0])
        center = numpy.array([0.0, 0.0, 0.0])
        axis = numpy.array([0.0, 0.0, 1.0])
        npt.assert_allclose(rotate_point(point, center, axis, 0.0),
                            numpy.array([1.0, 0.0, 0.0]))
        npt.assert_allclose(rotate_point(point, center, axis, math.radians(45.0)),
                            numpy.array([0.707, 0.707, 0.0]), atol=0.001)
        npt.assert_allclose(rotate_point(point, center, axis, math.radians(90.0)),
                            numpy.array([0.0, 1.0, 0.0]), atol=0.001)
        # Rotations around z with center=(0.5,0.5,0.5)
        point = numpy.array([5.5, 0.5, 0.5])
        center = numpy.array([0.5, 0.5, 0.5])
        axis = numpy.array([0.0, 0.0, 10.0])  # not unit vector, fine
        npt.assert_allclose(rotate_point(point, center, axis, 0.0),
                            numpy.array([5.5, 0.5, 0.5]))
        npt.assert_allclose(rotate_point(point, center, axis, math.radians(45.0)),
                            numpy.array([4.036, 4.036, 0.5]), atol=0.001)
        npt.assert_allclose(rotate_point(point, center, axis, math.radians(180.0)),
                            numpy.array([-4.5, 0.5, 0.5]))
        # Rotation around an axis at 30 to x in x-y plane
        point = numpy.array([1.0, 0.0, 0.0])
        center = numpy.array([0.0, 0.0, 0.0])
        axis = numpy.array([math.cos(math.radians(30.0)), math.sin(math.radians(30.0)), 0.0])
        npt.assert_allclose(rotate_point(point, center, axis, math.radians(90.0)),
                            numpy.array([0.75, 0.433, -0.5]), atol=0.001)
        npt.assert_allclose(rotate_point(point, center, axis, math.radians(-90.0)),
                            numpy.array([0.75, 0.433, 0.5]), atol=0.001)
