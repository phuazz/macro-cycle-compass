"""Unit tests for the growth-axis classification.

The module does no manual month arithmetic — observation dates come straight
from FRED and momentum is computed by index offset, not by date math — but the
two date-boundary tests below (a month boundary and a year boundary) guard the
history selection per the vault date rule.

Run:  python -m unittest discover -s tests
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import growth_axis as g  # noqa: E402


class TestLevelBucket(unittest.TestCase):
    def test_around_trend_inclusive_inner(self):
        self.assertEqual(g.level_bucket(0.0), "around trend")
        self.assertEqual(g.level_bucket(0.20), "around trend")
        self.assertEqual(g.level_bucket(-0.20), "around trend")

    def test_below_and_above(self):
        self.assertEqual(g.level_bucket(0.21), "above trend")
        self.assertEqual(g.level_bucket(-0.21), "below trend")
        self.assertEqual(g.level_bucket(0.69), "above trend")
        self.assertEqual(g.level_bucket(-0.69), "below trend")

    def test_well_beyond_outer_inclusive(self):
        self.assertEqual(g.level_bucket(0.70), "well above trend")
        self.assertEqual(g.level_bucket(-0.70), "well below trend")
        self.assertEqual(g.level_bucket(3.0), "well above trend")
        self.assertEqual(g.level_bucket(-7.54), "well below trend")

    def test_none(self):
        self.assertEqual(g.level_bucket(None), "n/a")


class TestMomentum(unittest.TestCase):
    def test_three_step(self):
        vals = [0.0, 0.1, 0.2, 0.3, 0.4]
        self.assertAlmostEqual(g.momentum(vals, 3), 0.4 - 0.1)

    def test_too_short_is_none(self):
        self.assertIsNone(g.momentum([0.1, 0.2], 3))


class TestConfirmedDirection(unittest.TestCase):
    def test_rising(self):
        vals = [0.0, 0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
        self.assertEqual(g.confirmed_direction(vals), "rising")

    def test_falling(self):
        vals = [0.0, 0.0, 0.0, -0.5, -1.0, -1.5, -2.0, -2.5]
        self.assertEqual(g.confirmed_direction(vals), "falling")

    def test_flat_is_steady(self):
        self.assertEqual(g.confirmed_direction([0.0] * 10), "steady")

    def test_single_down_print_holds_rising(self):
        # A confirmed rising run, then one month whose 3m momentum turns negative.
        # One beyond-band print must not flip the axis (needs two consecutive).
        vals = [0.0, 0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 0.5]
        self.assertEqual(g.confirmed_direction(vals), "rising")

    def test_two_down_prints_flip_to_falling(self):
        vals = [0.0, 0.0, 0.0, 0.5, 1.0, 1.5, 2.0, 0.5, 0.0]
        self.assertEqual(g.confirmed_direction(vals), "falling")

    def test_too_short_is_na(self):
        self.assertEqual(g.confirmed_direction([0.1, 0.2]), "n/a")


class TestDateBoundaries(unittest.TestCase):
    def test_year_boundary_trim_keeps_latest(self):
        dates = ["2025-10-01", "2025-11-01", "2025-12-01", "2026-01-01", "2026-02-01"]
        vals = [0.1, 0.2, 0.3, 0.4, 0.5]
        hist = g._trim_history(dates, vals, months=3)
        self.assertEqual([d for d, _ in hist], ["2025-12-01", "2026-01-01", "2026-02-01"])
        self.assertEqual(hist[-1], ["2026-02-01", 0.5])

    def test_month_boundary_last_is_reference(self):
        dates = ["2026-04-01", "2026-05-01"]
        vals = [0.07, -0.03]
        hist = g._trim_history(dates, vals, months=12)
        self.assertEqual(hist[-1][0], "2026-05-01")


if __name__ == "__main__":
    unittest.main()
