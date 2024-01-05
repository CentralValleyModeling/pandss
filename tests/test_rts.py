import unittest
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

import pandss as pdss

DSS_6 = Path(__file__).parent / "v6.dss"
DSS_7 = Path(__file__).parent / "v7.dss"


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
        with pdss.DSS(DSS_6) as dss:
            rts = dss.read_rts(p)
            self.assertEqual(len(rts), len(rts.values))
            self.assertEqual(len(rts.values), len(rts.dates))
            self.assertEqual(rts.path, p)
            self.assertIsInstance(rts.values, np.ndarray)
            self.assertIsInstance(rts.dates, list)
            self.assertIn(
                rts.period_type, pdss.keywords.PeriodTypes.__members__.values()
            )

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


if __name__ == "__main__":
    unittest.main()
