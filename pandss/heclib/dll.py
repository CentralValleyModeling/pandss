import ctypes as ct
import logging
from pathlib import Path
from datetime import datetime

import numpy as np

from .api import get_dll


def datetime_encode(d: datetime):
    date = d.strftime("%d%b%Y").encode()
    time = d.strftime("%H%S").encode()

    return date, time

class HECLIB:
    """Wrapper class exposing DLL functions in the USACE heclib.dll to python.
    """
    __slots__ = ['_open', "file_path", "file_table", "dll"]
    def __init__(self, dss: str | Path):
        self._open = False
        self.file_path = dss
        self.file_table = ct.c_void_p()
        self.dll = get_dll(self.file_path)

    def __enter__(self):
        logging.info(f"opening dss file {self.file_path}")
        fp = str(self.file_path).encode()
        try:
            success = self.dll.hec_dss_open(fp, ct.byref(self.file_table))
        except Exception as e:
            logging.error("exception caught before DLL function returned")
            raise e
        if success != 0:
            raise ValueError("") # TODO create error handling
        self._open = True
        return self

    def __exit__(self, *args, **kwargs):
        logging.info(f"closing dss file {self.file_path}")
        success = self.dll.hec_dss_close(self.file_table)
        if success != 0:
            raise ValueError("") # TODO create error handling
        self._open = False
    
    @staticmethod
    def must_be_open(method):
        def inner(obj, *args, **kwargs):
            if obj._open is False:
                raise IOError(f"file must be open to call {method}")
            else:
                return method(obj, *args, **kwargs)
        return inner
    
    @must_be_open
    def catalog(self, path_filter: str = ""):
        logging.info(f"getting catalog from dss {self.file_path}")
        path_filter = path_filter.encode("ascii")
        # Determine sizes of arrays
        count = self.dll.hec_dss_record_count(self.file_table)
        buffer_size = self.dll.hec_dss_CONSTANT_MAX_PATH_SIZE()
        # Allocate
        buffer = ct.create_string_buffer(count * buffer_size)
        record_types = (ct.c_int32 * count)()
        # Collect catalog
        record_count = self.dll.hec_dss_catalog(
            self.file_table,
            buffer,
            record_types,
            path_filter,
            count,
            buffer_size
        )
        # Convert to numpy types
        paths = np.char.chararray(
            shape=(record_count), 
            itemsize=buffer_size, 
            buffer=buffer,
        )
        paths = np.char.decode(paths, encoding='utf-8')
        record_types = np.int32(record_types[:count])

        return paths, record_types

    @must_be_open
    def ts_retrieve(self, path: str, start: datetime, end: datetime):
        # encode arguments
        path = path.encode()
        start_date, start_time = datetime_encode(start)
        end_date, end_time = datetime_encode(end)
        #
        time_len = ct.c_int()
        quality_len = ct.c_int()
        success = self.dll.hec_dss_tsGetSizes(
            self.file_table,
            path,
            start_date, start_time,
            end_date, end_time,
            ct.byref(time_len),
            ct.byref(quality_len)
        )

        return success



