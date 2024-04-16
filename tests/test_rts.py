import pickle
import unittest
from os import remove
from pathlib import Path
from random import choice
from string import ascii_letters
from time import perf_counter
from warnings import catch_warnings

import numpy as np
import pandas as pd

import pandss as pdss
from pandss import timeseries
from pandss.timeseries.period_type import PeriodTypeStandard

# Make sure we are using the dev version
assert pdss.__version__ is None

ASSETS = Path().resolve() / "tests/assets"
TEST_CREATED = ASSETS / "created"
DSS_6 = ASSETS / "existing/v6.dss"
DSS_7 = ASSETS / "existing/v7.dss"
DSS_LARGE = ASSETS / "existing/large_v6.dss"


class TestRegularTimeseries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DSS_6.exists():
            raise FileNotFoundError(DSS_6)
        if not DSS_7.exists():
            raise FileNotFoundError(DSS_7)
        if not DSS_LARGE.exists():
            raise FileNotFoundError(DSS_LARGE)

    def test_read_type_6(self):
        catalog = pdss.read_catalog(DSS_6)
        p = catalog.paths.pop()
        rts = pdss.read_rts(DSS_6, p)
        self.assertIsInstance(rts, pdss.RegularTimeseries)

    @unittest.expectedFailure
    def test_read_type_7(self):
        catalog = pdss.read_catalog(DSS_7)
        p = catalog.paths.pop()
        rts = pdss.read_rts(DSS_7, p)
        self.assertIsInstance(rts, pdss.RegularTimeseries)

    def test_read_time_6(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        times = list()
        with pdss.DSS(DSS_6) as dss:
            for _ in range(10):
                st = perf_counter()
                _ = dss.read_rts(p)
                et = perf_counter()
                times.append(et - st)
        average = sum(times) / len(times)
        self.assertLessEqual(average, 0.11)

    @unittest.expectedFailure
    def test_read_time_7(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        times = list()
        with pdss.DSS(DSS_7) as dss:
            for _ in range(10):
                st = perf_counter()
                _ = dss.read_rts(p)
                et = perf_counter()
                times.append(et - st)
        average = sum(times) / len(times)
        self.assertLessEqual(average, 0.15)

    def test_data_content_6(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        with pdss.DSS(DSS_6) as dss:
            rts = dss.read_rts(p)
            self.assertEqual(len(rts), len(rts.values))
            self.assertEqual(len(rts.values), len(rts.dates))
            self.assertEqual(rts.path, p)
            self.assertTrue(hasattr(rts.values, "__array_ufunc__"))
            self.assertTrue(hasattr(rts.values, "__array_function__"))
            value = rts.values[0]
            self.assertIsInstance(value, np.float64)
            self.assertIsInstance(rts.dates, np.ndarray)
            self.assertIn(
                rts.period_type,
                PeriodTypeStandard(),
            )
            self.assertEqual(rts.dates[0], np.datetime64("1921-10-31T23:59:59"))
            self.assertEqual(value, 31.0)

    @unittest.expectedFailure
    def test_data_content_7(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        with pdss.DSS(DSS_7) as dss:
            rts = dss.read_rts(p)
            self.assertEqual(len(rts), len(rts.values))
            self.assertEqual(len(rts.values), len(rts.dates))
            self.assertEqual(rts.path, p)
            self.assertTrue(hasattr(rts.values, "__array_ufunc__"))
            self.assertTrue(hasattr(rts.values, "__array_function__"))
            value = rts.values[0]
            self.assertIsInstance(value, np.float64)
            self.assertIsInstance(rts.dates, np.ndarray)
            self.assertIn(
                rts.period_type,
                PeriodTypeStandard(),
            )
            self.assertEqual(rts.dates[0], np.datetime64("1921-10-31T23:59:59"))
            self.assertEqual(value, 31.0)

    def test_interval_6(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        interval = pdss.timeseries.Interval(e="1MON")
        with pdss.DSS(DSS_6) as dss:
            rts = dss.read_rts(p)
            self.assertIsInstance(rts.interval, timeseries.Interval)
            self.assertEqual(rts.interval, interval)

    def test_to_frame(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        with pdss.DSS(DSS_6) as dss:
            rts = dss.read_rts(p)
            df = rts.to_frame()
            self.assertIsInstance(df, pd.DataFrame)
            self.assertListEqual(
                df.columns.names,
                ["A", "B", "C", "D", "E", "F", "UNITS", "PERIOD_TYPE", "INTERVAL"],
            )
            self.assertEqual(len(rts), len(df))

    def test_multiple_to_frame(self):
        p = pdss.DatasetPath.from_str("/CALSIM/.*/.*/.*/.*/.*/")
        with pdss.DSS(DSS_6) as dss:
            p = dss.resolve_wildcard(p)
            frames = [obj.to_frame() for obj in dss.read_multiple_rts(p)]
            df = pd.concat(frames)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertListEqual(
                df.columns.names,
                ["A", "B", "C", "D", "E", "F", "UNITS", "PERIOD_TYPE", "INTERVAL"],
            )

    def test_add_rts(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        with pdss.DSS(DSS_6) as dss:
            rts = dss.read_rts(p)
            double_month = rts + rts
            self.assertEqual(double_month.values[0], 62)

    def test_add_with_misaligned_dates(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        with pdss.DSS(DSS_6) as dss:
            rts = dss.read_rts(p)
            dates = pd.to_datetime(rts.dates)
            # offset by four years to avoid leap year weirdness in this test
            dates = dates + pd.DateOffset(years=4)
            rts_2 = pdss.RegularTimeseries(
                path=pdss.DatasetPath.from_str(
                    "/CALSIM/MONTH_DAYS_OFFSET/DAY//1MON/L2020A/"
                ),
                values=rts.values,
                dates=dates.values,
                units=rts.units,
                period_type=rts.period_type,
                interval=rts.interval,
            )
            rts_add_LR = rts + rts_2
            self.assertEqual(rts_add_LR.values[0], 62)
            self.assertEqual(len(rts_add_LR.values), len(rts_add_LR.dates))
            self.assertEqual(len(rts_add_LR), 1200 - 48)
            rts_add_RL = rts_2 + rts  # Swap places
            self.assertEqual(rts_add_RL.values[0], 62)
            self.assertEqual(len(rts_add_RL.values), len(rts_add_RL.dates))
            self.assertEqual(len(rts_add_RL), 1200 - 48)

    @unittest.skip("skipping long test, only run if targeted individually")
    def test_large_dss_to_frame_6(self):
        p = pdss.DatasetPath.from_str("/CALSIM/.*/.*/.*/1MON/.*/")
        st = perf_counter()
        with pdss.DSS(DSS_LARGE) as dss:
            p = dss.resolve_wildcard(p)
            self.assertEqual(len(p), 18_700)
            p = pdss.DatasetPathCollection(paths=set(list(p.paths)[:100]))
            df = pd.concat(obj.to_frame() for obj in dss.read_multiple_rts(p))
            self.assertIsInstance(df, pd.DataFrame)
            self.assertListEqual(
                df.columns.names,
                ["A", "B", "C", "D", "E", "F", "UNITS", "PERIOD_TYPE", "INTERVAL"],
            )
        et = perf_counter()
        tt = et - st
        self.assertLessEqual(tt, 20.0)

    def test_read_single_with_wildcard(self):
        p1 = pdss.DatasetPath(b="MONTH_DAYS")
        rts = pdss.read_rts(DSS_6, p1)
        self.assertIsInstance(rts, pdss.RegularTimeseries)
        with self.assertRaises(pdss.errors.UnexpectedDSSReturn):
            p2 = pdss.DatasetPath(f="L2020A")
            _ = pdss.read_rts(DSS_6, p2)

    def test_to_json(self):
        p1 = pdss.DatasetPath(b="MONTH_DAYS")
        rts = pdss.read_rts(DSS_6, p1)
        j = rts.to_json()
        self.assertEqual(j["path"], str(rts.path))

    def test_from_json(self):
        obj = dict(
            path="/.*/MONTH_DAYS/",
            values=(31, 28, 31),
            dates=("1921-01-31", "1921-02-28", "1921-03-31"),
            period_type="PER-CUM",
            units="days",
            interval="1MON",
        )
        rts = pdss.RegularTimeseries.from_json(obj)
        self.assertEqual(rts.units, obj["units"])

    def test_json_pipeline(self):
        p1 = pdss.DatasetPath(b="MONTH_DAYS")
        rts_1 = pdss.read_rts(DSS_6, p1)
        rts_2 = pdss.RegularTimeseries.from_json(rts_1.to_json())
        self.assertEqual(rts_1, rts_2)
        self.assertNotEqual(id(rts_1), id(rts_2))


class TestRegularTimeseriesWriting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.created = list()

    def setUp(self):
        def random_name():
            return "".join(choice(ascii_letters) for _ in range(10))

        self.src_6 = DSS_6
        self.dst_6 = TEST_CREATED / f"{random_name()}.dss"
        self.created.append(self.dst_6)
        self.src_7 = DSS_7
        self.dst_7 = TEST_CREATED / f"{random_name()}.dss"
        self.created.append(self.dst_7)

    @classmethod
    def tearDownClass(cls) -> None:
        for dss in cls.created:
            if dss.exists():
                remove(dss)
        if cls.created:
            for obj in cls.created[0].parent.iterdir():
                if obj.suffix in [".dsd", ".dsc", ".dsk"]:
                    attempts = 0
                    while (obj.exists()) and (attempts < 100):
                        try:
                            remove(obj)
                        except PermissionError:
                            attempts += 1

    def test_write_rts_6(self):
        p_old = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        with pdss.DSS(self.src_6) as dss:
            rts = dss.read_rts(p_old)
        rts.values = rts.values + 1
        p_new = pdss.DatasetPath.from_str(
            "/CALSIM/MONTH_DAYS_PLUS_ONE/DAY//1MON/L2020A/"
        )
        with pdss.DSS(self.dst_6) as dss_new:
            dss_new.write_rts(p_new, rts)
            catalog = dss_new.read_catalog()
        self.assertEqual(len(catalog), 1)

    def test_copy_rts_6(self):
        p_old = pdss.DatasetPath.from_str(
            "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",
        )
        p_new = pdss.DatasetPath.from_str(
            "/CALSIM/MONTH_DAYS_PLUS_ONE/DAY//1MON/L2020A/",
        )
        with catch_warnings(action="error"):
            pdss.copy_rts(self.src_6, self.dst_6, (p_old, p_new))
        self.assertTrue(self.dst_6.exists())
        catalog = pdss.read_catalog(self.dst_6)
        self.assertEqual(len(catalog), 1)

    def test_copy_multiple_rts_6(self):
        p_old = (
            "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",
            "/CALSIM/PPT_OROV/PRECIP//1MON/L2020A/",
        )
        p_new = (
            "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",
            "/CALSIM/PPT_OROV/PRECIP//1MON/L2020A/",
        )
        with catch_warnings(action="error"):
            pdss.copy_multiple_rts(self.src_6, self.dst_6, tuple(zip(p_old, p_new)))
        self.assertTrue(self.dst_6.exists())
        catalog = pdss.read_catalog(self.dst_6)
        self.assertEqual(len(catalog), 2)

    def test_pickle_rts_6(self):
        pickle_location = TEST_CREATED / "month_days.pkl"
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        with pdss.DSS(DSS_6) as dss:
            rts = dss.read_rts(p)
        with open(pickle_location, "wb") as OUT:
            pickle.dump(rts, OUT)
        with open(pickle_location, "rb") as IN:
            rts_salty = pickle.load(IN)
        self.assertEqual(rts, rts_salty)

    def test_update_rts(self):
        p1 = pdss.DatasetPath(b="MONTH_DAYS")
        rts_1 = pdss.read_rts(DSS_6, p1)
        rts_2 = rts_1.update(units="MOON-DAY")
        # Basic attr tests
        self.assertEqual(rts_1.path, rts_2.path)
        self.assertNotEqual(id(rts_1), id(rts_2))
        self.assertNotEqual(rts_1, rts_2)
        self.assertEqual(rts_1.units, "DAYS")
        self.assertEqual(rts_2.units, "MOON-DAY")
        # Test bad update of values without update of dates
        with self.assertRaises(ValueError):
            rts_1.update(values=[0])
        # Test update of values with same len dates
        rts_3 = rts_2.update(values=[31], dates=["2000-01-31"])
        self.assertEqual(rts_3.path, rts_2.path)
        # Test changing values
        rts_1.values[0] = -1000
        self.assertNotEqual(rts_1.values[0], rts_2.values[0])


if __name__ == "__main__":
    unittest.main()
