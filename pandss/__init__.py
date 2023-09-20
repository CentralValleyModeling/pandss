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
    with null_io() as null:
        try:
            os.dup2(null.fileno(), sys.__stdout__.fileno())
            yield None
        finally:
            # Clear pending, we do not want to see these
            null.flush()
            os.dup2(sys.__stdout__.fileno(), null.fileno())


with silent_std_out():
    from . import catalog, reshape, timeseries
    from .catalog import common_catalog, iter_common_catalog, read_catalog
    from .reshape import split_path
    from .timeseries import read_dss, write_dss

__all__ = ["timeseries", "reshape"]
