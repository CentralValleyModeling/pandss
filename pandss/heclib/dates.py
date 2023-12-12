import logging
from ctypes import c_int
from datetime import datetime, time, timedelta

import numpy as np

JULIAN_ANCHOR = datetime(1899, 12, 31, 0, 0)
JULIAN_ANCHOR_NP = np.datetime64(JULIAN_ANCHOR)


def datetime_encode(dt: datetime) -> tuple[bytes, bytes]:
    """Convert from Python datetime object to HEC-DSS formatted bytestring.

    HEC-DSS follows the convention of 00:00:01 to 24:00:00 for one day
    Python follows the convention of 00:00:00 to 23:59:59 for one day

    This function handles the convention conversion.
    """
    logging.debug(f"parsing datetime {dt}")
    if dt.time() == time(0, 0, 0, 0):
        dt = dt - timedelta(days=1)
        fmt = "%d%b%Y,24:00"
    else:
        fmt = "%d%b%Y,%H:%M"

    d, t = dt.strftime(fmt).split(",")

    logging.debug(f"datetime parsed to {d}, {t}")

    return d.encode("UTF-8"), t.encode("UTF-8")


def julian_to_date(
    julian: c_int,
    seconds: c_int = None,
    resolution: int = 86400,
) -> datetime:
    step_func_key = {
        # resolution is given as how many seconds in 1 Unit
        86400: lambda x: timedelta(days=x),
        3600: lambda x: timedelta(hours=x),
        60: lambda x: timedelta(minutes=x),
    }
    step = step_func_key[resolution]
    date = JULIAN_ANCHOR + step(julian.value)
    if seconds is not None:
        date = date + timedelta(seconds=seconds.value)
    logging.debug(f"converted {julian}, {seconds} -> {date}")

    return date


def julian_array_to_date(
    julian: np.ndarray,
    seconds: np.ndarray = None,
    resolution: int = 86400,
) -> np.ndarray:
    step_func_key = {
        # resolution is given as how many seconds in 1 Unit
        86400: lambda x: x.astype("timedelta64[D]"),
        3600: lambda x: x.astype("timedelta64[h]"),
        60: lambda x: x.astype("timedelta64[m]"),
    }
    step = step_func_key[resolution]
    date = JULIAN_ANCHOR_NP + step(julian)
    if seconds is not None:
        date = date + np.timedelta64(seconds, "s")
    else:
        seconds = [None]
    logging.debug(f"converted array, item 0 {julian[0]}, {seconds[0]} -> {date[0]}")

    return date


def get_datetime_range_pyobj(
    start_date_julian: c_int,
    start_seconds: c_int,
    end_date_julian: c_int,
    end_seconds: c_int,
) -> tuple[datetime, datetime]:
    start = julian_to_date(start_date_julian, start_seconds)
    end = julian_to_date(end_date_julian, end_seconds)

    return start, end
