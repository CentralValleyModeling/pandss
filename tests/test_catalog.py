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

class TestCommonCatalog(unittest.TestCase):
    def test_ignore_all_raises(self):
        with self.assertRaises(ValueError):
            pdss.common_catalog(
                left=DSS_SMALL, 
                right=DSS_SMALL, 
                ignore_parts=pdss.catalog.COMPARE_ON)
    
    def test_with_duplicate(self):
        cat_1 = DataFrame(
            [['T', 'A1', 'B', 'C', 'D', 'E'],
            ['T', 'A2', 'B', 'C', 'D', 'E'],
            ['T', 'A2', 'B', 'C', 'D', 'E']],
            columns=['T', 'A', 'B', 'C', 'D', 'E']
        )
        cat_2 = DataFrame(
            [['T', 'A1', 'B', 'C', 'D', 'E'],
            ['T', 'A2', 'B', 'C', 'D', 'E'],
            ['T', 'A2', 'B', 'C', 'D', 'E'],
            ['T', 'A3', 'B', 'C', 'D', 'E']],
            columns=['T', 'A', 'B', 'C', 'D', 'E']
        )
        with self.assertWarns(Warning):
            L, R =pdss.common_catalog(
                cat_1, 
                cat_2, 
                ignore_parts=['B', 'C', 'D', 'E'])
        self.assertEqual(len(L), len(R))
            
if __name__ == '__main__':
    unittest.main()
