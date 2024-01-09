import unittest
from pathlib import Path
from time import perf_counter

import pyhecdss

import pandss as pdss

DSS_6 = Path(__file__).parent / "v6.dss"
DSS_7 = Path(__file__).parent / "v7.dss"


class TestCatalog(unittest.TestCase):
    def test_read_type_6(self):
        catalog = pdss.read_catalog(DSS_6)
        self.assertIsInstance(catalog, pdss.Catalog)

    def test_read_type_7(self):
        catalog = pdss.read_catalog(DSS_7)
        self.assertIsInstance(catalog, pdss.Catalog)

    def test_read_time_6(self):
        times = list()
        for _ in range(100):
            st = perf_counter()
            _ = pdss.read_catalog(DSS_6)
            et = perf_counter()
            times.append(et - st)
        average = sum(times) / len(times)
        self.assertLessEqual(average, 0.02)

    def test_read_time_7(self):
        times = list()
        for _ in range(100):
            st = perf_counter()
            _ = pdss.read_catalog(DSS_7)
            et = perf_counter()
            times.append(et - st)
        average = sum(times) / len(times)
        self.assertLessEqual(average, 0.02)

    def test_from_frame_6(self):
        with pyhecdss.DSSFile(str(DSS_6)) as dss:
            df_cat = dss.read_catalog()
        cat = pdss.Catalog.from_frame(df_cat, DSS_6)
        self.assertIsInstance(cat, pdss.Catalog)
        self.assertEqual(len(cat), len(df_cat))

    @unittest.expectedFailure
    def test_from_frame_7(self):
        with pyhecdss.DSSFile(str(DSS_7)) as dss:
            df_cat = dss.read_catalog()
        cat = pdss.Catalog.from_frame(df_cat, DSS_7)
        self.assertIsInstance(cat, pdss.Catalog)
        self.assertEqual(len(cat), len(df_cat))


if __name__ == "__main__":
    unittest.main()
