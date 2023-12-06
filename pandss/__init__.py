import os
import sys
from contextlib import contextmanager


@contextmanager
def null_io():
    """Create a TextIOWrapper object pointing to os.devnull"""
    try:
        with open(os.devnull, "w") as null:
            yield null
    finally:
        pass


@contextmanager
def silent_std_out():
    """Small context manager to ignore stdout, even from FORTRAN subroutines.

    Does not re-map stderr or stdin. Re-maps the system level stdout found
    using `sys.__stdout__`. The following will produce no outputs to appear on
    the screen:

    >>> with silent_std_out():
    ...    print("Hello World")
    ...    call_noisy_subroutine()
    ...
    """
    # Clear pending, we want to see these
    sys.__stdout__.flush()
    STD_OUT_FD = 1
    PLACEHOLDER_FD = 11
    with null_io() as null:
        try:
            os.dup2(sys.__stdout__.fileno(), PLACEHOLDER_FD)
            os.dup2(null.fileno(), STD_OUT_FD)
            yield None
        finally:
            # Clear pending, we do not want to see these
            null.flush()
            os.dup2(PLACEHOLDER_FD, STD_OUT_FD)
            os.close(PLACEHOLDER_FD)


from . import catalog, reshape, timeseries
from .catalog import common_catalog, iter_common_catalog, read_catalog
from .catalog_object import Catalog
from .reshape import split_path
from .timeseries import read_dss, write_dss
from .heclib import HECLIB

__all__ = ["timeseries", "reshape"]
