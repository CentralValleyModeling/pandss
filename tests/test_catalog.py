import unittest
from pathlib import Path
from time import perf_counter

from pandas import DataFrame
import pandss as pdss

DSS_SMALL = Path('./assets/small.dss').resolve()

class TestCatalog(unittest.TestCase):
    def test_read_type(self):
        catalog = pdss.read_catalog(DSS_SMALL)
        self.assertIsInstance(catalog, DataFrame)
    
    def test_read_time(self):
        times = list()
        for _ in range(100): 
            st = perf_counter()
            _ = pdss.read_catalog(DSS_SMALL)
            et = perf_counter()
            times.append(et - st)
        average = sum(times) / len(times)
        self.assertLessEqual(average, 0.01)

if __name__ == '__main__':
    unittest.main()
