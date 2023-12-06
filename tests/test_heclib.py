import logging
from datetime import datetime

from pandss import HECLIB


if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    dss_file = "C:/Users/zroy/Documents/_Python/pandss/tests/test.dss"
    with HECLIB(dss_file) as DLL:
        paths, record_types = DLL.catalog()
        result = DLL.ts_retrieve(
            path=paths[0], 
            start=datetime(1920, 1, 1, 0, 0),
            end=datetime(1929, 12, 31, 23, 59)
        )
        
