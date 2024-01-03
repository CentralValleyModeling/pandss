import unittest
from pathlib import Path
from time import perf_counter

from pandas import DataFrame, Series

import pandss as pdss

DSS_6 = Path(__file__).parent / "v6.dss"
DSS_7 = Path(__file__).parent / "v7.dss"


class TestCatalog(unittest.TestCase):
    def test_read_type(self):
        catalog = pdss.read_catalog(DSS_6)
        self.assertIsInstance(catalog, pdss.Catalog)
        catalog = pdss.read_catalog(DSS_7)
        self.assertIsInstance(catalog, pdss.Catalog)

    def test_read_time(self):
        times = list()
        for _ in range(100):
            st = perf_counter()
            _ = pdss.read_catalog(DSS_6)
            et = perf_counter()
            times.append(et - st)
        average = sum(times) / len(times)
        self.assertLessEqual(average, 0.005)


if __name__ == "__main__":
    unittest.main()
