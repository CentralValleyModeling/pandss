import unittest
from pathlib import Path

import pandss as pdss

DSS_6 = Path(__file__).parent / "v6.dss"
DSS_7 = Path(__file__).parent / "v7.dss"


class TestDSS(unittest.TestCase):
    def test_multiple_paths(self):
        p = pdss.DatasetPath.from_str("/CALSIM/.*/.*/.*/.*/.*/")
        for src in (DSS_6, DSS_7):
            matched_timeseries = 0
            for rts in pdss.read_multiple_rts(src, p):
                self.assertIsInstance(rts, pdss.RegularTimeseries)
                matched_timeseries += 1
            self.assertEqual(matched_timeseries, 2)
        
        p = pdss.DatasetPath.from_str("/CALSIM/MO.*DAYS/.*/.*/.*/.*/")
        for src in (DSS_6, DSS_7):
            matched_timeseries = 0
            for rts in pdss.read_multiple_rts(src, p):
                self.assertIsInstance(rts, pdss.RegularTimeseries)
                matched_timeseries += 1
            self.assertEqual(matched_timeseries, 1)


if __name__ == "__main__":
    unittest.main()
