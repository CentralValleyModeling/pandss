import ctypes as ct
import logging
from datetime import datetime
from pathlib import Path

import numpy as np

from .. import suppress_stdout_stderr
from .api import get_dll
from .dates import datetime_encode, get_datetime_range_pyobj, julian_to_date
from .decorators import must_be_open, silent
from .errors import HECDSS_ErrorHandler


class DSS_Handle:
    """Wrapper class exposing DLL functions in the USACE heclib.dll to python."""

    __slots__ = ["open", "file_path", "file_table", "dll", "handler"]

    def __init__(self, dss: str | Path):
        self.open = False
        self.file_path = dss
        self.file_table = ct.pointer((ct.c_longlong * 250)())
        with suppress_stdout_stderr():
            self.dll = get_dll(self.file_path)
        self.handler = HECDSS_ErrorHandler()

    @silent
    def __enter__(self):
        """Wraps DLL function `hec_dss_open` and enables the use of this class
        in pythons context manager pattern.

        with DSS_Handle(path_to_dss_file) as DSS:
            # read/write data in DSS file
            ...
        # hec_dss_close automatically called.


        Returns
        -------
        self
            Returns a DSS_Handle object.

        Raises
        ------
        RuntimeError
            Generic error for error opening DSS file
        """
        logging.info(f"opening dss file {self.file_path}")
        fp = str(self.file_path).encode()
        success = self.dll.hec_dss_open(fp, ct.byref(self.file_table))
        if success != 0:
            self.handler.resolve(success)
        self.open = True

        return self

    @silent
    @must_be_open
    def __exit__(self, exc_type, exc_inst, traceback):
        """Wraps DLL function `hec_dss_close` and enables the use of this class
        in pythons context manager pattern.
        """
        logging.info(f"closing dss file {self.file_path}")
        success = self.dll.hec_dss_close(self.file_table)
        if success != 0:
            self.handler.resolve(success)
        self.open = False

    @silent
    @must_be_open
    def catalog(self, path_filter: str = "") -> tuple[np.ndarray, np.ndarray]:
        """Wraps `hec_dss_catalog` and other DSS functions needed for reading
        the DSS catalog.

        with DSS_Handle(path) as DSS:
            catalog, record_types = DSS.catalog()

        Parameters
        ----------
        path_filter : str, optional
            A str that represents a pathname with wild characters represented
            by a star (*) to match any string in the pathname part. Wild
            characters can be at the beginning or end of a part, not inside of
            a string. As an example, "/*/*/*Flow/*/*/*/" will match all
            pathnames that have "Flow" anywhere in the C part, such as "Flow",
            "Inflow", "Outflow-Reg", etc. A part such as "Flow*Reg" is not
            legal. A null (//) will only match a null, where only a star (*)
            will match all., by default ""

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            char array of catalog paths, and an array of matching record types
        """
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
            buffer_size,
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

    @silent
    @must_be_open
    def ts_info(self, path: str) -> tuple[str, str]:
        """Wraps `hec_dss_tsRetrieveInfo` and returns the units, period_type of
        a timeseries.

        Parameters
        ----------
        path : str
            A-F path of a DSS timeseries

        Returns
        -------
        tuple[str, str]
            Values for `untis` and `period_type` of the timeseries

        Raises
        ------
        RuntimeError
            Generic error for error reading info from the DSS file
        """
        logging.info(f"getting units and period_type for {path}")
        path_bytes = path.encode("UTF-8")
        buffer_size = ct.c_int(10)
        units = ct.create_string_buffer(buffer_size.value)
        period_type = ct.create_string_buffer(buffer_size.value)
        success = self.dll.hec_dss_tsRetrieveInfo(
            self.file_table,
            path_bytes,
            units,
            buffer_size,
            period_type,
            buffer_size,
        )
        if success != 0:
            self.handler.resolve(success)

        return units.value.decode(), period_type.value.decode()

    @silent
    @must_be_open
    def _get_datetime_range(
        self,
        path: bytes,
        full_set: bool = True,
    ) -> tuple[ct.c_int, ct.c_int, ct.c_int, ct.c_int]:
        """Wraps hec_dss_tsGetDateTimeRange and returns the julian, seconds
        start and end dates of the timeseries.

        Parameters
        ----------
        path : str
            A-F path to the timeseries
        full_set : bool, optional
            Corresponds to the boolFullSet flag, by default True

        Returns
        -------
        tuple[ct.c_int, ct.c_int, ct.c_int, ct.c_int]
            The start date in julian format, the start time in seconds, the end
            date in julian format, the end time in seconds

        Raises
        ------
        RuntimeError
            Generic error for error reading info from the DSS file
        """
        # read date span
        start_julian = ct.c_int()
        start_seconds = ct.c_int()
        end_julian = ct.c_int()
        end_seconds = ct.c_int()
        if full_set is True:
            full_set = ct.c_int(1)
        else:
            full_set = ct.c_int(0)
        success = self.dll.hec_dss_tsGetDateTimeRange(
            self.file_table,
            path,
            full_set,
            ct.byref(start_julian),
            ct.byref(start_seconds),
            ct.byref(end_julian),
            ct.byref(end_seconds),
        )
        if success != 0:
            self.handler.resolve(success)
        logging.debug(
            "{}: start JD-{} T-{}, end JD-{} T-{}".format(
                path,
                start_julian.value,
                start_seconds.value,
                end_julian.value,
                end_seconds.value,
            )
        )
        return start_julian, start_seconds, end_julian, end_seconds

    @silent
    @must_be_open
    def _get_ts_sizes(
        self,
        path: bytes,
        start_date: ct.c_char_p,
        start_time: ct.c_char_p,
        end_date: ct.c_char_p,
        end_time: ct.c_char_p,
    ) -> tuple[ct.c_int, ct.c_int]:
        """Wraps hec_dss_tsGetSizes and returns the array length and quality
        table width for the given path and date range.

        Parameters
        ----------
        path : bytes
            A-F path to the timeseries
        start_date : ct.c_char_p
            Inclusive start date in DDMMMYYYY format
        start_time : ct.c_char_p
            Inclusive start time in HHMM format
        end_date : ct.c_char_p
            Inclusive end date in DDMMYYY format
        end_time : ct.c_char_p
            Inclusive end date in HHMM format

        Returns
        -------
        tuple[ct.c_int, ct.c_int]
            The length and width of arrays needed to store the data in this timeseries
            and associated quality data

        Raises
        ------
        RuntimeError
            Generic error for error reading info from the DSS file
        """
        logging.debug("getting timeseries size")
        # Init
        time_len = ct.c_int()
        quality_len = ct.c_int()
        # Call
        success = self.dll.hec_dss_tsGetSizes(
            self.file_table,
            path,
            start_date,
            start_time,
            end_date,
            end_time,
            ct.byref(time_len),
            ct.byref(quality_len),
        )
        if success != 0:
            self.handler.resolve(success)
        logging.debug(f"number of times: {time_len.value}")
        logging.debug(f"number of quality: {quality_len.value}")

        return time_len, quality_len

    @silent
    @must_be_open
    def ts_retrieve(
        self,
        path: str,
        full_set: bool = True,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Wraps `hec_dss_tsRetrieve` and associated functions to read timeseries data
        from a DSS file.

        Parameters
        ----------
        path :
            A-F path to the timeseries
        full_set : bool, optional
            Corresponds to the boolFullSet flag, by default True, by default True

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            The values and and times read for the timeseries

        Raises
        ------
        RuntimeError
            Generic error for error reading info from the DSS file
        """
        path_bytes = path.encode("UTF-8")
        # Determine date range
        date_range_julian = self._get_datetime_range(path_bytes, full_set)
        start, end = get_datetime_range_pyobj(*date_range_julian)
        start_date, start_time = datetime_encode(start)
        end_date, end_time = datetime_encode(end)
        time_len, quality_len = self._get_ts_sizes(
            path_bytes,
            start_date,
            start_time,
            end_date,
            end_time,
        )
        logging.info(
            f"size to read: {time_len.value} (quality table width = {quality_len.value})"
        )
        buffer_size = 20  # magic number from hec-dss-python library by USACE
        logging.info(f"retrieving data for {path}")
        units = ct.create_string_buffer(buffer_size)
        period_type = ct.create_string_buffer(buffer_size)
        # Places to store data
        array_size = int(time_len.value)
        quality_size = array_size * quality_len.value
        times = (ct.c_int * array_size)()
        values = (ct.c_double * array_size)()
        quality = (ct.c_int * quality_size)()

        buffer_size = ct.c_int(buffer_size)
        # Metadata
        values_read = ct.c_int(0)
        base_date = ct.c_int(0)
        time_resolution = ct.c_int(0)

        logging.debug("retrieving data")
        success = self.dll.hec_dss_tsRetrieve(
            self.file_table,
            path_bytes,
            start_date,
            start_time,
            end_date,
            end_time,
            times,
            values,
            time_len,
            ct.byref(values_read),
            quality,
            quality_len,
            ct.byref(base_date),
            ct.byref(time_resolution),
            units,
            buffer_size,
            period_type,
            buffer_size,
        )
        if success != 0:
            self.handler.resolve(success)

        values = np.int32(values[: values_read.value])
        times = times[: values_read.value]
        times = [
            julian_to_date(ct.c_int(t), resolution=time_resolution.value) for t in times
        ]

        return values, times

    @silent
    @must_be_open
    def ts_store_regular(
        self,
        path: str,
        date_range: tuple[datetime, datetime],
        values: np.ndarray,
        quality: np.ndarray,
        units: str,
        period_type: str,
        save_as_float: bool = True,
    ) -> None:
        """Wraps `hec_dss_tsStoreRegular`.

        Parameters
        ----------
        path : str
            A-F path for the timeseries provided.
        date_range : tuple[datetime, datetime]
            The inclusive datetime range for the timeseries
        values : np.ndarray
            The array of values to be saved
        quality : np.ndarray
            The table of quality data to be saved
        units : str
            The units for the timeseries
        period_type : str
            The period_type for the timeseries
        save_as_float : bool, optional
            Corresponds to the saveAsFloat flag, by default True

        Returns
        -------
        None

        Raises
        ------
        RuntimeError
            Generic error for error reading info from the DSS file
        """
        path_bytes = path.encode("UTF-8")
        start_date, start_time = datetime_encode(date_range[0])
        end_date, end_time = datetime_encode(date_range[1])

        v_size = len(values)
        values = (ct.c_double * v_size)(*values)
        q_size = len(quality)
        quality = (ct.c_int * q_size)(*quality)

        save_as_float = ct.c_bool(save_as_float)

        success = self.dll.hec_dss_tsStoreRegular(
            self.file_table,
            path_bytes,
            start_date,
            start_time,
            end_date,
            end_time,
            ct.byref(values),
            v_size,
            ct.byref(quality),
            q_size,
            save_as_float,
            units.encode("UTF-8"),
            period_type.encode("UTF-8"),
        )

        if success != 0:
            self.handler.resolve(success)
