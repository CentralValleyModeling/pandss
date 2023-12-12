import ctypes as ct
import unittest
from datetime import datetime
from os import remove
from pathlib import Path

import numpy as np

from pandss import DSS, heclib


class Test_DSS(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.dss_file_6 = Path(
            r"C:\Users\zroy\Documents\_Modeling\_2023DCR\_studies\_cartridges\0525-Nile\Adjusted\SV\DCR2023_SV_Nile_Adj_v14.dss"
        )  # Path(__file__).parent / "test.dss"
        cls.dss_file = cls.dss_file_6.with_suffix(".7.dss")

    def test_convert_version(self):
        if self.dss_file.exists():
            remove(self.dss_file)
        heclib.dll.convert_to_version_7(self.dss_file_6, self.dss_file)

    def test_open_close(self):
        try:
            with DSS(self.dss_file):
                pass
        except Exception as e:
            self.fail()

    def test_catalog(self):
        with DSS(self.dss_file) as dss:
            paths, record_types = dss.catalog()
        self.assertIsInstance(paths, np.ndarray)
        self.assertIsInstance(paths, np.ndarray)

    def test_ts_info(self):
        with DSS(self.dss_file) as dss:
            paths, record_types = dss.catalog()
            units, period_type = dss.ts_info(paths[0])
        self.assertIsInstance(units, str)
        self.assertIsInstance(period_type, str)

    def test_get_datetime_range(self):
        with DSS(self.dss_file) as dss:
            paths, record_types = dss.catalog()
            sj, ss, ej, es = dss._get_datetime_range(paths[0].encode())
        self.assertIsInstance(sj, ct.c_long)
        self.assertIsInstance(ss, ct.c_long)
        self.assertIsInstance(ej, ct.c_long)
        self.assertIsInstance(es, ct.c_long)

    def test_date_range_to_datetime(self):
        sj = ct.c_long(7974)
        ss = ct.c_long(86400)
        ej = ct.c_long(10957)
        es = ct.c_long(86400)
        start, stop = heclib.dates.get_datetime_range_pyobj(sj, ss, ej, es)
        self.assertIsInstance(start, datetime)
        self.assertIsInstance(stop, datetime)
        self.assertEqual(start, datetime(1921, 11, 1))

    def test_get_ts_sizes(self):
        with DSS(self.dss_file) as dss:
            paths, record_types = dss.catalog()
            path_bytes = paths[0].encode()
            date_range_julian = dss._get_datetime_range(path_bytes)
            start, end = heclib.dates.get_datetime_range_pyobj(*date_range_julian)
            start_date, start_time = heclib.dates.datetime_encode(start)
            end_date, end_time = heclib.dates.datetime_encode(end)
            time_len, quality_len = dss._get_ts_sizes(
                path_bytes,
                start_date,
                start_time,
                end_date,
                end_time,
            )
        self.assertIsInstance(time_len, ct.c_long)
        self.assertIsInstance(quality_len, ct.c_long)

    def test_ts_retrieve(self):
        with DSS(self.dss_file) as dss:
            paths, record_types = dss.catalog()

            values, q, dates, u, pt = dss.ts_retrieve(paths[0], full_set=True)

        self.assertIsInstance(values, np.ndarray)
        self.assertIsInstance(dates, np.ndarray)
        self.assertEqual(len(values), 1200)

    def test_ts_store(self):
        with self.assertRaises(NotImplementedError):
            with DSS(self.dss_file.with_stem("test_new")) as dss:
                path = "/PANDSS/TEST_STORE/TESTING//1Month/L2023A/"
                dt = [datetime(2023, 1, 1), datetime(2023, 12, 1)]
                vals = list(range(12))
                dss.ts_store_regular(
                    path,
                    dt,
                    vals,
                    quality=list(),
                    period_type="PER-INST",
                    units="COUNT",
                    save_as_float=True,
                )
        #    cat, _t = dss.catalog()
        #self.assertNotEqual(len(cat), 0)


if __name__ == "__main__":
    unittest.main()
