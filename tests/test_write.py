import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

import pandss as pdss


class TestWrite(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ind = pd.date_range(
            start="01JAN1990 0100",
            periods=201,
            freq="15T",
            name="PERIOD",
        )
        vone = np.sin(np.linspace(-np.pi, np.pi, 201))
        cls.one = pd.DataFrame(columns=["VALUE"], data=vone, index=ind)
        cls.one["PATH"] = "/SAMPLE/SIN/WAVE//15MIN/SAMPLE1/"
        cls.one["UNITS"] = "UNIT-X"
        cls.one["PERIOD-TYPE"] = "INST-VAL"
        vtwo = np.cos(np.linspace(-np.pi, np.pi, 201))
        cls.two = pd.DataFrame(columns=["VALUE"], data=vtwo, index=ind)
        cls.two["PATH"] = "/SAMPLE/SIN/WAVE//15MIN/SAMPLE2/"
        cls.two["UNITS"] = "UNIT-X"
        cls.two["PERIOD-TYPE"] = "INST-VAL"

        cls.bad = pd.DataFrame(columns=["VALUE"], data=vtwo, index=ind)

        cls.temp = TemporaryDirectory()
        cls.dir = Path(cls.temp.name)

        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()
        return super().tearDownClass()

    def test_single(self):
        dst = self.dir / "single.dss"
        pdss.write_dss(dst, self.one)
        self.assertTrue(dst.exists())

    def test_multiple(self):
        both = pd.concat([self.one, self.two])
        dst = self.dir / "multiple.dss"
        pdss.write_dss(dst, both)
        self.assertTrue(dst.exists())

    def test_accessor(self):
        both = pd.concat([self.one, self.two])
        dst = self.dir / "accessor.dss"
        both.dss.write(dst)
        self.assertTrue(dst.exists())

    def test_fail_on_duplicate(self):
        dst = self.dir / "raises.dss"
        pdss.write_dss(dst, self.one)
        with self.assertRaises(ValueError):
            pdss.write_dss(dst, self.one)

    def test_fail_on_columns(self):
        dst = self.dir / "should_not_exist.oops"
        with self.assertRaises(ValueError):
            pdss.write_dss(dst, self.bad)
        self.assertFalse(dst.exists())


if __name__ == "__main__":
    unittest.main()
