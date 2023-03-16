"""Tests for GrindingJig."""
import unittest
import math
import numpy
import numpy.testing as npt

from gouge import GrindingJig


class TestJig(unittest.TestCase):

    def test01_init(self):
        j = GrindingJig()

    def test02_parse_dimension(self):
        j = GrindingJig()
        j.length = 1.0
        j.angle = math.radians(30.0)
        # Centered, rotation=0.0
        x, y = j.tool_vectors(rotation=0.0)
        npt.assert_allclose(x, numpy.array([0.0, 0.5, 0.0]), atol=0.001)
        npt.assert_allclose(y, numpy.array([0.866, 0.0, 0.0]), atol=0.001)
        # All the way over, rotation=90.0
        x, y = j.tool_vectors(rotation=math.radians(90.0))
        npt.assert_allclose(x, numpy.array([0.217, 0.125, 0.433]), atol=0.001)
        npt.assert_allclose(y, numpy.array([0.650, 0.375, -0.433]), atol=0.001)
