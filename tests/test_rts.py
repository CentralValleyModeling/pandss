import pickle
import unittest
from os import remove
from pathlib import Path
from random import choice
from string import ascii_letters
from time import perf_counter

import numpy as np
import pandas as pd

import pandss as pdss

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
        self.assertLessEqual(average, 0.15)

    def test_data_content_6(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        with pdss.DSS(DSS_6) as dss:
            rts = dss.read_rts(p)
            self.assertEqual(len(rts), len(rts.values))
            self.assertEqual(len(rts.values), len(rts.dates))
            self.assertEqual(rts.path, p)
            self.assertIsInstance(rts.values, np.ndarray)
            self.assertIsInstance(rts.values[0], np.float64)
            self.assertIsInstance(rts.dates, np.ndarray)
            self.assertIn(
                rts.period_type, pdss.keywords.PeriodTypes.__members__.values()
            )
            self.assertEqual(rts.dates[0], np.datetime64("1921-10-31T23:59:59"))
            self.assertEqual(rts.values[0], 31.0)

    @unittest.expectedFailure
    def test_data_content_7(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        with pdss.DSS(DSS_7) as dss:
            rts = dss.read_rts(p)
            self.assertEqual(len(rts), len(rts.values))
            self.assertEqual(len(rts.values), len(rts.dates))
            self.assertEqual(rts.path, p)
            self.assertIsInstance(rts.values, np.ndarray)
            self.assertIsInstance(rts.dates, list)
            self.assertIn(
                rts.period_type, pdss.keywords.PeriodTypes.__members__.values()
            )
            self.assertEqual(rts.dates[0], np.datetime64("1921-10-31T23:59:59"))
            print(rts.values[12:])
            self.assertEqual(rts.values[0], 31.0)

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
                        except PermissionError as e:
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


if __name__ == "__main__":
    unittest.main()
