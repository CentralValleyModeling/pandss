import unittest
from pathlib import Path

import pandss as pdss

DSS_6 = Path(__file__).parent / "v6.dss"
DSS_7 = Path(__file__).parent / "v7.dss"


class TestDSS(unittest.TestCase):
    def test_multiple_with_wildcard_6(self):
        p = pdss.DatasetPath.from_str("/.*/.*/.*/.*/.*/.*/")
        matched_timeseries = 0
        for rts in pdss.read_multiple_rts(DSS_6, p):
            self.assertIsInstance(rts, pdss.RegularTimeseries)
            matched_timeseries += 1
        self.assertEqual(matched_timeseries, 2)

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

    def test_pydsstools_engine_6(self):
        with pdss.DSS(DSS_6, engine="pydsstools") as dss:
            catalog = dss.read_catalog()
            self.assertIsInstance(catalog, pdss.Catalog)
            self.assertEqual(len(catalog), 2)
            for rts in dss.read_multiple_rts(catalog):
                self.assertIsInstance(rts, pdss.RegularTimeseries)

    def test_pydsstools_engine_7(self):
        with pdss.DSS(DSS_7, engine="pydsstools") as dss:
            catalog = dss.read_catalog()
            self.assertIsInstance(catalog, pdss.Catalog)
            self.assertEqual(len(catalog), 2)
            for rts in dss.read_multiple_rts(catalog):
                self.assertIsInstance(rts, pdss.RegularTimeseries)


if __name__ == "__main__":
    unittest.main()
