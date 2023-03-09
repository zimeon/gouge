"""Tests for GrindingJig."""
import unittest
import math

from gouge import GrindingJig


class TestJig(unittest.TestCase):

    def test01_init(self):
        j = GrindingJig()

    def test02_parse_dimension(self):
        j = GrindingJig()
        j.length = 1.0
        j.angle = math.radians(30.0)
        # Centered, rotation=0.0
        ex, ey, ez, tx, ty, tz = j.tool_vectors(rotation=0.0)
        self.assertAlmostEqual(ex, 0.0)
        self.assertAlmostEqual(ey, 0.5, 3)
        self.assertAlmostEqual(ez, 0.0)
        self.assertAlmostEqual(tx, 0.866, 3)
        self.assertAlmostEqual(ty, 0.0)
        self.assertAlmostEqual(tz, 0.0)
        # All the way over, rotation=90.0
        ex, ey, ez, tx, ty, tz = j.tool_vectors(rotation=math.radians(90.0))
        self.assertAlmostEqual(ex, 0.217, 3)
        self.assertAlmostEqual(ey, 0.125, 3)
        self.assertAlmostEqual(ez, 0.433, 3)
        self.assertAlmostEqual(tx, 0.650, 3)
        self.assertAlmostEqual(ty, 0.375, 3)
        self.assertAlmostEqual(tz, -0.433, 3)
