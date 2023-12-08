import ctypes as ct
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

from .. import silent_std_out
from .api import get_dll


def datetime_encode(d: datetime):
    date = d.strftime("%d%b%Y").encode("utf-8")
    time = d.strftime("%H%S").encode("utf-8")

    return date, time


class HECLIB:
    """Wrapper class exposing DLL functions in the USACE heclib.dll to python."""

    __slots__ = ["_open", "file_path", "file_table", "dll"]

    def __init__(self, dss: str | Path):
        self._open = False
        self.file_path = dss
        self.file_table = ct.c_void_p()
        with silent_std_out():
            self.dll = get_dll(self.file_path)

    @staticmethod
    def must_be_open(method):
        def works_on_open_file(obj, *args, **kwargs):
            if obj._open is False:
                raise IOError(f"file must be open to call {method}")
            else:
                return method(obj, *args, **kwargs)

        return works_on_open_file

    @staticmethod
    def silent(method):
        def silent_method(obj, *args, **kwargs):
            with silent_std_out():
                return method(obj, *args, **kwargs)

        return silent_method

    @silent
    def __enter__(self):
        logging.info(f"opening dss file {self.file_path}")
        fp = str(self.file_path).encode()
        try:
            success = self.dll.hec_dss_open(fp, ct.byref(self.file_table))
        except Exception as e:
            logging.error("exception caught before DLL function returned")
            raise e
        if success != 0:
            raise RuntimeError("")  # TODO create error handling
        self._open = True

        return self

    @silent
    def __exit__(self, *args, **kwargs):
        logging.info(f"closing dss file {self.file_path}")
        success = self.dll.hec_dss_close(self.file_table)
        if success != 0:
            raise RuntimeError("")  # TODO create error handling
        self._open = False

    @silent
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
            self.file_table, buffer, record_types, path_filter, count, buffer_size
        )
        # Convert to numpy types
        paths = np.char.chararray(
            shape=(record_count),
            itemsize=buffer_size,
            buffer=buffer,
        )
        paths = np.char.decode(paths, encoding="utf-8")
        record_types = np.int32(record_types[:count])

        return paths, record_types

    def get_datetime_range(self, path: str):
        # encode arguments
        path = path.encode("utf-8")
        # read date span
        start_julian = ct.c_int()
        start_seconds = ct.c_int()
        end_julian = ct.c_int()
        end_seconds = ct.c_int()
        success = self.dll.hec_dss_tsGetDateTimeRange(
            self.file_table,
            path,
            ct.c_int(1),
            ct.byref(start_julian),
            ct.byref(start_seconds),
            ct.byref(end_julian),
            ct.byref(end_seconds),
        )
        if success != 0:
            raise RuntimeError("")  # TODO create error handling

        return start_julian, start_seconds, end_julian, end_seconds

    def julian_to_ymd(
        self,
        julian: ct.c_int,
    ) -> tuple[ct.c_int, ct.c_int, ct.c_int]:
        y = ct.c_int()
        m = ct.c_int()
        d = ct.c_int()
        self.dll.hec_dss_julianToYearMonthDay(
            julian, ct.byref(y), ct.byref(m), ct.byref(d)
        )
        logging.info(f"converted julian {julian} -> {y.value}-{m.value}-{d.value}")
        return y, m, d

    def get_ts_sizes(
        self,
        path: str,
        start_julian: ct.c_int,
        start_seconds: ct.c_int,
        end_julian: ct.c_int,
        end_seconds: ct.c_int,
    ):
        # encode arguments
        path = path.encode("utf-8")
        # Init
        time_len = ct.c_int()
        quality_len = ct.c_int()
        success = self.dll.hec_dss_tsGetSizes(
            self.file_table,
            path,
            start_julian,
            start_seconds,
            end_julian,
            end_seconds,
            ct.byref(time_len),
            ct.byref(quality_len),
        )
        if success != 0:
            raise RuntimeError("")  # TODO create error handling
        logging.info(f"{time_len.value=}")
        logging.info(f"{quality_len.value=}")

        return time_len, quality_len

    # @silent
    @must_be_open
    def ts_retrieve(self, path: str):
        # read date span
        sj, ss, ej, es = self.get_datetime_range(path)
        # encode arguments
        path = path.encode("utf-8")
        # Init
        time_len = ct.c_int()
        quality_len = ct.c_int()
        success = self.dll.hec_dss_tsGetSizes(
            self.file_table,
            path,
            sj,
            ss,
            ej,
            es,
            ct.byref(time_len),
            ct.byref(quality_len),
        )
        if success != 0:
            raise RuntimeError("")  # TODO create error handling
        logging.info(f"{time_len.value=}")
        logging.info(f"{quality_len.value=}")
        shape = time_len.value, quality_len.value
        # Places to store data
        times = (ct.c_int32 * shape[0])()
        values = (ct.c_double * shape[0])()
        quality = (ct.c_int * (shape[0] * shape[1]))()
        buffer_size = 20  # magic number from hec-dss-python library by USACE
        units = ct.create_string_buffer(buffer_size)
        data_type = ct.create_string_buffer(buffer_size)
        buffer_size = ct.c_int(buffer_size)
        # Metadata
        values_read = ct.c_int(0)
        base_date = ct.c_int()
        time_resolution = ct.c_int()

        success = self.dll.hec_dss_tsRetrieve(
            self.file_table,
            path,
            start_date,
            start_time,
            end_date,
            end_time,
            times,
            values,
            time_len.value,
            ct.byref(values_read),
            quality,
            quality_len.value,
            ct.byref(base_date),
            ct.byref(time_resolution),
            units,
            buffer_size.value,
            data_type,
            buffer_size.value,
        )
        if success != 0:
            raise RuntimeError("")  # TODO create error handling

        return success
