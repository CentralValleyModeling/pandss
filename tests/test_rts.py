import unittest
from pathlib import Path
from time import perf_counter
from datetime import datetime

import numpy as np
import pandas as pd

import pandss as pdss

DSS_6 = Path(__file__).parent.resolve() / "v6.dss"
DSS_7 = Path(__file__).parent.resolve() / "v7.dss"
DSS_LARGE = Path(__file__).parent.resolve() / "large_v6.dss"


class TestRegularTimeseries(unittest.TestCase):
    def test_read_type(self):
        for src in (DSS_6, DSS_7):
            catalog = pdss.read_catalog(src)
            p = catalog.paths.pop()
            rts = pdss.read_rts(src, p)
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
        with pdss.DSS(DSS_7) as dss:
            for _ in range(10):
                st = perf_counter()
                _ = dss.read_rts(p)
                et = perf_counter()
                times.append(et - st)
        average = sum(times) / len(times)
        self.assertLessEqual(average, 0.15)

    def test_data_content(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
        for src in (DSS_6, DSS_7):
            with pdss.DSS(src) as dss:
                rts = dss.read_rts(p)
                self.assertEqual(len(rts), len(rts.values))
                self.assertEqual(len(rts.values), len(rts.dates))
                self.assertEqual(rts.path, p)
                self.assertIsInstance(rts.values, np.ndarray)
                self.assertIsInstance(rts.dates, list)
                self.assertIn(
                    rts.period_type, pdss.keywords.PeriodTypes.__members__.values()
                )
                self.assertEqual(rts.dates[0], datetime(1921, 10, 31, 23, 59, 59))
                print(rts.values)
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

    def test_large_dss_to_frame(self):
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
        print(df)
        et = perf_counter()
        tt = et - st
        self.assertLessEqual(tt, 20.0)


if __name__ == "__main__":
    unittest.main()
