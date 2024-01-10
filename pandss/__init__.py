"""pandss - Interact with HEC DSS files in a pandas to CSV like API.

Zachary Roy, DWR
June 2023
"""
from . import errors, keywords
from .catalog import Catalog
from .dss import DSS
from .paths import DatasetPath, DatasetPathCollection
from .timeseries import RegularTimeseries
from .utils import (copy_multiple_rts, copy_rts, read_catalog,
                    read_multiple_rts, read_rts)

__all__ = [
    "DSS",
    "DatasetPath",
    "Catalog",
    "DatasetPathCollection",
    "RegularTimeseries",
]
