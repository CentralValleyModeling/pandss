import unittest
from pathlib import Path

import pandss as pdss

DSS_6 = Path(__file__).parent / "v6.dss"
DSS_7 = Path(__file__).parent / "v7.dss"


class TestPath(unittest.TestCase):
    def test_wildcard(self):
        p = pdss.DatasetPath.from_str(r"/CALSIM/.*/.*/.*/.*/.*/")
        self.assertTrue(p.has_wildcard)
        for src in (DSS_6, DSS_7):
            with pdss.DSS(src) as dss:
                collection = dss.resolve_wildcard(p)

            self.assertIsInstance(collection, pdss.DatasetPathCollection)
            self.assertEqual(len(collection), 22)

    def test_warn_bad_wildcard(self):
        with self.assertWarns(Warning):
            pdss.DatasetPath.from_str(r"///////")


if __name__ == "__main__":
    unittest.main()
