import unittest
from pathlib import Path

import pandas as pd

import pandss as pdss
from pandss.timeseries.interval import Interval

# Make sure we are using the installed version
assert pdss.__version__ is not None

DSS_6 = Path().resolve() / "tests/assets/existing/v6.dss"
DSS_7 = Path().resolve() / "tests/assets/existing/v7.dss"
DSS_LARGE = Path().resolve() / "tests/assets/existing/large_v6.dss"


class TestInterval(unittest.TestCase):
    def test_ordering(self):
        i_big = Interval(e="1Day")  # version 7 style
        i_small = Interval(e="1MIN")  # versuon 6 style
        self.assertGreater(i_big, i_small)

    def test_to_period_offset_alias(self):
        yearly = Interval("1Year")
        self.assertEqual(yearly.offset, "Y")
        century = Interval("IR-CENTURY")
        self.assertEqual(century.offset, "100Y")

    def test_seconds(self):
        i1 = Interval(e="10MIN")  # version 7 style
        self.assertEqual(i1.seconds, 10 * 60)
        i2 = Interval(e="12Hour")  # version 6 style
        self.assertEqual(i2.seconds, 12 * 60 * 60)

    def test_slots(self):
        yearly = Interval(e="1Year")  # version 7 style
        with self.assertRaises(AttributeError):
            yearly.foo = None

    def test_single_period(self):
        period = pd.Period(
            value=pd.to_datetime("2023-01-01"),
            freq=Interval("1MON").freq,
        )
        self.assertEqual(period.days_in_month, 31)

    def test_period_index(self):
        periods = pd.PeriodIndex(
            data=(
                pd.to_datetime("2023-02-01"),
                pd.to_datetime("2024-02-01"),
            ),
            freq=Interval("1MON").freq,
        )
        self.assertListEqual(list(periods.days_in_month), [28, 29])

    def test_frame_matches_interval_object(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        rts = pdss.read_rts(DSS_6, p)
        frame = rts.to_frame()
        self.assertEqual(str(rts.interval), "1MON")
        self.assertEqual(frame.columns.get_level_values("INTERVAL"), str(rts.interval))

    def test_create_rts_with_str_interval(self):
        rts = pdss.RegularTimeseries(
            path=None,
            values=None,
            dates=None,
            period_type=None,
            units=None,
            interval="1MON",
        )
        self.assertIsInstance(rts.interval, Interval)
