import unittest
from pathlib import Path

import pandss as pdss

DSS_6 = Path().resolve() / "tests/assets/existing/v6.dss"
DSS_7 = Path().resolve() / "tests/assets/existing/v7.dss"
DSS_LARGE = Path().resolve() / "tests/assets/existing/large_v6.dss"


class TestPath(unittest.TestCase):
    def test_wildcard_6(self):
        p = pdss.DatasetPath.from_str(r"/CALSIM/.*/.*/.*/.*/.*/")
        self.assertTrue(p.has_wildcard)

        with pdss.DSS(DSS_6) as dss:
            collection = dss.resolve_wildcard(p)
            collection = collection.collapse_dates()

        self.assertIsInstance(collection, pdss.DatasetPathCollection)
        self.assertEqual(
            collection.paths,
            {
                pdss.DatasetPath.from_str("/CALSIM/PPT_OROV/PRECIP//1MON/L2020A/"),
                pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY/*/1MON/L2020A/"),
            },
        )
        self.assertEqual(len(collection), 2)

    def test_wildcard_7(self):
        p = pdss.DatasetPath.from_str(r"/CALSIM/.*/.*/.*/.*/.*/")
        self.assertTrue(p.has_wildcard)
        with pdss.DSS(DSS_7) as dss:
            collection = dss.resolve_wildcard(p)
            collection = collection.collapse_dates()
        self.assertIsInstance(collection, pdss.DatasetPathCollection)
        self.assertEqual(
            collection.paths,
            {
                pdss.DatasetPath.from_str("/CALSIM/PPT_OROV/PRECIP//1Month/L2020A/"),
                pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY/*/1Month/L2020A/"),
            },
        )
        self.assertEqual(len(collection), 2)

    def test_replace_bad_wildcard(self):
        blank = pdss.DatasetPath.from_str(r"///////")
        star = pdss.DatasetPath.from_str(r"/*/*/*/*/*/*/")
        with pdss.DSS(DSS_6) as dss:
            blank = dss.resolve_wildcard(blank)
            star = dss.resolve_wildcard(star)
        self.assertEqual(blank, star)

    def test_warn_findall_if_wildcard_in_set(self):
        star = pdss.DatasetPath.from_str(r"/*/*/*/*/*/*/")
        with pdss.DSS(DSS_6) as dss:
            catalog = dss.read_catalog()
            catalog = catalog.collapse_dates()
            with self.assertWarns(Warning):
                catalog.resolve_wildcard(star)


if __name__ == "__main__":
    unittest.main()
