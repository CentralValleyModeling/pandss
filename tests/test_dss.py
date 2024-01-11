import unittest
from importlib.util import find_spec
from pathlib import Path

import pandss as pdss

DSS_6 = Path().resolve() / "tests/assets/existing/v6.dss"
DSS_7 = Path().resolve() / "tests/assets/existing/v7.dss"
DSS_LARGE = Path().resolve() / "tests/assets/existing/large_v6.dss"

HAS_PYDSSTOOLS = find_spec("pydsstools") is not None


class TestDSS(unittest.TestCase):
    def test_multiple_with_wildcard_6(self):
        p = pdss.DatasetPath.from_str("/.*/.*/.*/.*/.*/.*/")
        matched_timeseries = 0
        for rts in pdss.read_multiple_rts(DSS_6, p):
            self.assertIsInstance(rts, pdss.RegularTimeseries)
            matched_timeseries += 1
        self.assertEqual(matched_timeseries, 2)

    @unittest.expectedFailure
    def test_multiple_with_wildcard_7(self):
        p = pdss.DatasetPath.from_str("/.*/.*/.*/.*/.*/.*/")
        matched_timeseries = 0
        for rts in pdss.read_multiple_rts(DSS_7, p):
            self.assertIsInstance(rts, pdss.RegularTimeseries)
            matched_timeseries += 1
        self.assertEqual(matched_timeseries, 2)

    def test_multiple_with_partial_wildcard_6(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MO.*DAYS/.*/.*/.*/.*/")
        matched_timeseries = 0
        for rts in pdss.read_multiple_rts(DSS_6, p):
            self.assertIsInstance(rts, pdss.RegularTimeseries)
            matched_timeseries += 1
        self.assertEqual(matched_timeseries, 1)

    @unittest.expectedFailure
    def test_multiple_with_partial_wildcard_7(self):
        p = pdss.DatasetPath.from_str("/CALSIM/MO.*DAYS/.*/.*/.*/.*/")
        matched_timeseries = 0
        for rts in pdss.read_multiple_rts(DSS_7, p):
            self.assertIsInstance(rts, pdss.RegularTimeseries)
            matched_timeseries += 1
        self.assertEqual(matched_timeseries, 1)

    def test_pyhecdss_engine_6(self):
        with pdss.DSS(DSS_6, engine="pyhecdss") as dss:
            catalog = dss.read_catalog()
            self.assertIsInstance(catalog, pdss.Catalog)
            self.assertEqual(len(catalog), 2)
            for rts in dss.read_multiple_rts(catalog):
                self.assertIsInstance(rts, pdss.RegularTimeseries)

    @unittest.expectedFailure
    def test_pyhecdss_engine_7(self):
        with pdss.DSS(DSS_7, engine="pyhecdss") as dss:
            catalog = dss.read_catalog()
            self.assertIsInstance(catalog, pdss.Catalog)
            self.assertEqual(len(catalog), 2)
            for rts in dss.read_multiple_rts(catalog):
                self.assertIsInstance(rts, pdss.RegularTimeseries)

    @unittest.skipUnless(HAS_PYDSSTOOLS, "pydsstools is an optional dependency")
    def test_pydsstools_engine_6(self):
        with pdss.DSS(DSS_6, engine="pydsstools") as dss:
            catalog = dss.read_catalog(drop_date=True)
            self.assertIsInstance(catalog, pdss.Catalog)
            self.assertEqual(len(catalog), 2)
            for rts in dss.read_multiple_rts(catalog):
                self.assertIsInstance(rts, pdss.RegularTimeseries)

    @unittest.skipUnless(HAS_PYDSSTOOLS, "pydsstools is an optional dependency")
    def test_pydsstools_engine_7(self):
        with pdss.DSS(DSS_7, engine="pydsstools") as dss:
            catalog = dss.read_catalog(drop_date=True)
            self.assertIsInstance(catalog, pdss.Catalog)
            self.assertEqual(len(catalog), 2)
            for rts in dss.read_multiple_rts(catalog):
                self.assertIsInstance(rts, pdss.RegularTimeseries)

    def test_multiple_open_close(self):
        dss_1 = pdss.DSS(DSS_6)
        dss_2 = pdss.DSS(DSS_6)
        with dss_1 as obj_1, dss_2 as obj_2:
            self.assertIsInstance(obj_1, pdss.DSS)
            self.assertIsInstance(obj_2, pdss.DSS)
        self.assertFalse(dss_1.is_open)
        self.assertFalse(dss_2.is_open)


if __name__ == "__main__":
    unittest.main()
