"""Tests for Jig."""
import unittest
import math
import numpy
import numpy.testing as npt

from gouge import Jig


class TestJig(unittest.TestCase):

    def test01_init(self):
        j = Jig()

    def test02_tool_vectors(self):
        j = Jig()
        j.length = 1.0
        j.angle = math.radians(30.0)
        # Centered, rotation=0.0
        y, z = j.tool_vectors(rotation=0.0)
        npt.assert_allclose(y, numpy.array([0.0, 1.0, 0.0]), atol=0.001)
        npt.assert_allclose(z, numpy.array([0.0, 0.0, 1.0]), atol=0.001)
        # All the way over, rotation=90.0
        y, z = j.tool_vectors(rotation=math.radians(90.0))
        npt.assert_allclose(y, numpy.array([-0.866, 0.250, 0.433]), atol=0.001)
        npt.assert_allclose(z, numpy.array([0.500, 0.433, 0.750]), atol=0.001)

    def test03_tool_rotation_matrix(self):
        j = Jig()
        j.length = 1.0
        j.angle = math.radians(30.0)
        # Centered, rotation=0.0, identity matrix
        r = j.tool_rotation_matrix(rotation=0.0)
        npt.assert_allclose(r, numpy.array([[1.0, 0.0, 0.0],
                                            [0.0, 1.0, 0.0],
                                            [0.0, 0.0, 1.0]]), atol=0.001)
        # All the way over, rotation=90.0
        r = j.tool_rotation_matrix(rotation=math.radians(90.0))
        npt.assert_allclose(r, numpy.array([[0.000, -0.866, 0.500],
                                            [0.866, 0.250, 0.433],
                                            [-0.500, 0.433, 0.750]]), atol=0.001)
