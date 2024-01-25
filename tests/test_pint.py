import unittest
from pathlib import Path

from pint.errors import DimensionalityError

import pandss as pdss

# Make sure we are using the developer version
assert pdss.__version__ is None

DSS_6 = Path().resolve() / "tests/assets/existing/v6.dss"
DSS_7 = Path().resolve() / "tests/assets/existing/v7.dss"
DSS_LARGE = Path().resolve() / "tests/assets/existing/large_v6.dss"


class TestPath(unittest.TestCase):
    def test_ureg_has_common_units(self):
        for u in ("cfs", "taf", "unknown"):
            self.assertIn(u, pdss.units.ureg)

    def test_fail_inconsistent_units(self):
        with pdss.DSS(DSS_6) as dss:
            days_path = pdss.DatasetPath.from_str("//MONTH_DAYS/////")
            prec_path = pdss.DatasetPath.from_str("//PPT_OROV/////")
            days = tuple(dss.read_multiple_rts(days_path))[0]
            prec = tuple(dss.read_multiple_rts(prec_path))[0]
            with self.assertRaises(DimensionalityError):
                days.values.to(prec.values.units)

    def test_unrecognized_units(self):
        with pdss.DSS(DSS_6) as dss:
            temp_paths = pdss.DatasetPath.from_str("//TEMPERATURE/////")
            for rts in dss.read_multiple_rts(temp_paths):
                self.assertEqual(rts.values.units, "unrecognized")
                with self.assertRaises(DimensionalityError):
                    rts.values.to("unknown")


if __name__ == "__main__":
    unittest.main()
