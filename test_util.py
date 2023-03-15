"""Tests for util.py."""
import unittest

from util import fill_range, round_up, round_down


class TestUtil(unittest.TestCase):

    def test01_fill_range(self):
        self.assertEqual(fill_range([]), [])
        self.assertEqual(fill_range([1.23]), [1.23])
        self.assertEqual(fill_range([1.23]), [1.23])
        self.assertEqual(fill_range([0.0, 1.0]), [0.0, 1.0])
        self.assertEqual(fill_range([1.0, 0.0]), [0.0, 1.0])
        self.assertEqual(fill_range([1.0, 0.0, 2.0, 4.0]), [0.0, 1.0, 2.0, 3.0, 4.0])
        self.assertEqual(fill_range([0.0, 5.5]), [0.0, 1.0, 2.0, 3.0, 4.0, 5.5])

    def test_round_up(self):
        self.assertEqual(round_up(0.0), 0)
        self.assertEqual(round_up(1.0), 1)
        self.assertEqual(round_up(99.0), 99)
        self.assertEqual(round_up(1.9999), 2)
        self.assertEqual(round_up(2.0001), 2)
        self.assertEqual(round_up(2.0001, tolerance=0.0001), 3)
        self.assertEqual(round_up(2.0001, tolerance=0.00011), 2)
        self.assertEqual(round_up(2.5), 3)
        self.assertEqual(round_up(-0.01), 0)
        self.assertEqual(round_up(-1.0), -1)
        self.assertEqual(round_up(-2.6), -2)

    def test_round_down(self):
        self.assertEqual(round_down(0.0), 0)
        self.assertEqual(round_down(1.0), 1)
        self.assertEqual(round_down(99.0), 99)
        self.assertEqual(round_down(1.9999), 2)
        self.assertEqual(round_down(2.0001), 2)
        self.assertEqual(round_down(2.0001, tolerance=0.0001), 2)
        self.assertEqual(round_down(2.0001, tolerance=0.00011), 2)
        self.assertEqual(round_down(2.5), 2)
        self.assertEqual(round_down(-0.01), -1)
        self.assertEqual(round_down(-1.0), -1)
        self.assertEqual(round_down(-2.6), -3)
