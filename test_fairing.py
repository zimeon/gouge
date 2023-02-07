"""Tests for fairing.py."""
import unittest

import logging
import numpy as np
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt

from fairing import FairCurve


def show_plot(xy, cx, cy):
    """Show plot only if run as script."""
    if (__name__ == '__main__'):
        plt.figure(figsize=(6.5, 4))
        xx, yy = zip(*xy)
        plt.plot(xx, yy, 'o', label='data')
        plt.plot(cx, cy, '-')
        plt.show()


class TestLofting(unittest.TestCase):

    def test01_init(self):
        for tc in ({'pts': [(12.21211, 13.2525), (12.47474, 12.0625), (12.96263, 10.0625), (13.10526, 8.0625), (12.94737, 6.0625), (12.26316, 4.0625), (9.78947, 2.0625), (6.26872, 1.0625), (0.0, 0.0625), [-6.26872, 1.0625], [-9.78947, 2.0625], [-12.26316, 4.0625], [-12.94737, 6.0625], [-13.10526, 8.0625], [-12.96263, 10.0625], [-12.47474, 12.0625], [-12.21211, 13.2525]]},
                   {'pts': [(12.26316, 4.0625), (9.78947, 2.0625), (0.0, 0.0625), [-9.78947, 2.0625], [-12.26316, 4.0625]]},
                   {'pts': [[0, 1], [1, 1], [3, 0], [3, -1]], 'len': 4.4},
                   {'pts': [[0, 1], [1, 1], [3, 0]]},
                   {'pts': [[0, 1], [1, 1]], 'len': 1.0},
                   {'pts': [[0, 1], [0, 1]], 'len': 0.0},
                   {'pts': [[0, 1]], 'len': 0.0},
                   {'pts': [[0, 1], [1, 0], [0, -1], [-1, 0]]},
                   {'pts': [[0, 0], [5, 1], [6, 0]]},
                   {'pts': [[0, 0], [100, 20], [110, 0]]}):
            xy = tc['pts']
            fc = FairCurve(xy)
            cx, cy = fc.curve()
            show_plot(xy, cx, cy)
            if ('len' in tc):
                self.assertAlmostEqual(fc.length(), tc['len'], 1)

    def test02_x(self):
        fc = FairCurve([[0, 0], [1, 1]])
        self.assertAlmostEqual(fc.x(0.0), 0.0)
        self.assertAlmostEqual(fc.x(0.5), 0.5)
        self.assertAlmostEqual(fc.x(1.0), 1.0)
        # Horizontal
        fc = FairCurve([[0, 0], [1, 0]])
        self.assertAlmostEqual(fc.x(0.0), 0.0)
        self.assertRaises(ValueError, fc.x, 1.0)
        # Vertical
        fc = FairCurve([[0, 0], [0, -1]])
        self.assertAlmostEqual(fc.x(0.0), 0.0)
        self.assertAlmostEqual(fc.x(-0.5), 0.0)
        self.assertAlmostEqual(fc.x(-1.0), 0.0)
        self.assertRaises(ValueError, fc.x, 1.0)

    def test02_y(self):
        fc = FairCurve([[0, 0], [1, 1]])
        self.assertAlmostEqual(fc.y(0.0), 0.0)
        self.assertAlmostEqual(fc.y(0.5), 0.5)
        self.assertAlmostEqual(fc.y(1.0), 1.0)
        # Horizontal
        fc = FairCurve([[0, 0], [1, 0]])
        self.assertAlmostEqual(fc.y(0.0), 0.0)
        self.assertAlmostEqual(fc.y(0.1), 0.0)
        self.assertAlmostEqual(fc.y(1.0), 0.0)
        self.assertRaises(ValueError, fc.x, -1.0)
        self.assertRaises(ValueError, fc.x, 1.1)
        # Vertical
        fc = FairCurve([[2, -1], [2, 1]])
        self.assertAlmostEqual(fc.y(2.0), -1.0)
        self.assertRaises(ValueError, fc.x, 2.00001)


if (__name__ == '__main__'):
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
    print("Done")
