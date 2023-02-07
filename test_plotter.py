"""Tests for plotter.py."""
import unittest

from plotter import Region


class TestLofting(unittest.TestCase):

    def test_region_init(self):
        r = Region()

    def test_sheet_regions(self):
        r = Region(min_x=0.0, max_x=3.0, min_y=0.0, max_y=7.0)
        sr = r.sheet_regions(paper_x=9, paper_y=15)
        self.assertEqual(next(sr), [-3, 6, -4, 11])
        self.assertRaises(StopIteration, next, sr)
        r = Region(min_x=-11.0, max_x=11.0, min_y=0.0, max_y=19.0)
        sr = r.sheet_regions(paper_x=9, paper_y=15)
        self.assertEqual(next(sr), [-13, -4, -5, 10])
        self.assertEqual(next(sr), [-4, 5, -5, 10])
        self.assertEqual(next(sr), [5, 14, -5, 10])
        self.assertEqual(next(sr), [-13, -4, 10, 25])
        self.assertEqual(next(sr), [-4, 5, 10, 25])
        self.assertEqual(next(sr), [5, 14, 10, 25])
        self.assertRaises(StopIteration, next, sr)
