import unittest
from pathlib import Path

import pandss as pdss
from pandss.timeseries.interval import Interval

# Make sure we are using the developer version
assert pdss.__version__ is None

DSS_6 = Path().resolve() / "tests/assets/existing/v6.dss"
DSS_7 = Path().resolve() / "tests/assets/existing/v7.dss"
DSS_LARGE = Path().resolve() / "tests/assets/existing/large_v6.dss"


class TestInterval(unittest.TestCase):
    def test_ordering(self):
        yearly = Interval(e="1Year")  # version 7 style
        monthly = Interval(e="1MON")  # versuon 6 style
        self.assertGreater(yearly, monthly)

    def test_to_period_offset_alias(self):
        yearly = Interval("1Year")
        self.assertEqual(yearly.offset, "Y")
        century = Interval("IR-CENTURY")
        self.assertEqual(century.offset, "100Y")

    def test_seconds(self):
        yearly = Interval(e="1Year")  # version 7 style
        self.assertEqual(yearly.seconds, 365 * 24 * 60 * 60)
        monthly = Interval(e="1MON")  # version 6 style
        self.assertEqual(monthly.seconds, 30 * 24 * 60 * 60)

    def test_slots(self):
        yearly = Interval(e="1Year")  # version 7 style
        with self.assertRaises(AttributeError):
            yearly.foo = None
