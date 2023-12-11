import ctypes as ct
import unittest
from datetime import datetime

import numpy as np

from pandss import DSS_Handle, heclib


class Test_DSS_Handle(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.dss_file = "C:/Users/zroy/Documents/_Python/pandss/tests/test.dss"

    def _test_all(self):
        with DSS_Handle(self.dss_file) as DSS:
            # paths, record_types = DSS.catalog()
            # result = DSS.ts_info(paths[0])
            # result = DSS.ts_retrieve(paths[0])
            # result = DSS.ret()
            new_path = "/PANDSS/NEW_TS_2/TESTING//1MON/L2023A"
            units = "HOPE"
            period_type = "PER-AVER"
            values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            quality = []
            result = DSS.ts_store_regular(
                new_path,
                date_range=[datetime(2023, 1, 1), datetime(2023, 12, 1)],
                values=values,
                quality=quality,
                units=units,
                period_type=period_type,
            )

            print(result)

    def test_open_close(self):
        try:
            with DSS_Handle(self.dss_file) as DSS:
                pass
        except Exception as e:
            self.fail()

    def test_catalog(self):
        with DSS_Handle(self.dss_file) as DSS:
            paths, record_types = DSS.catalog()
        self.assertIsInstance(paths, np.ndarray)
        self.assertIsInstance(paths, np.ndarray)

    def test_ts_info(self):
        with DSS_Handle(self.dss_file) as DSS:
            paths, record_types = DSS.catalog()
            units, period_type = DSS.ts_info(paths[0])
        self.assertIsInstance(units, str)
        self.assertIsInstance(period_type, str)

    def test_get_datetime_range(self):
        with DSS_Handle(self.dss_file) as DSS:
            paths, record_types = DSS.catalog()
            sj, ss, ej, es = DSS._get_datetime_range(paths[0].encode())
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
        with DSS_Handle(self.dss_file) as DSS:
            paths, record_types = DSS.catalog()
            path_bytes = paths[0].encode()
            date_range_julian = DSS._get_datetime_range(path_bytes)
            start, end = heclib.dates.get_datetime_range_pyobj(*date_range_julian)
            start_date, start_time = heclib.dates.datetime_encode(start)
            end_date, end_time = heclib.dates.datetime_encode(end)
            time_len, quality_len = DSS._get_ts_sizes(
                path_bytes,
                start_date,
                start_time,
                end_date,
                end_time,
            )
        self.assertIsInstance(time_len, ct.c_long)
        self.assertIsInstance(quality_len, ct.c_long)

    def test_ts_retrieve(self):
        with DSS_Handle(self.dss_file) as DSS:
            paths, record_types = DSS.catalog()

            values, dates = DSS.ts_retrieve(paths[0], full_set=True)

        self.assertIsInstance(values, np.ndarray)
        self.assertIsInstance(dates, list)
        self.assertEqual(len(values), 1200)


if __name__ == "__main__":
    unittest.main()
