from importlib.metadata import PackageNotFoundError, version

from . import errors, quiet
from .catalog import Catalog
from .dss import DSS, module_engine
from .paths import DatasetPath, DatasetPathCollection
from .timeseries import RegularTimeseries
from .utils import (
    copy_multiple_rts,
    copy_rts,
    read_catalog,
    read_multiple_rts,
    read_rts,
)

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # pandss not installed, likely developer mode
    __version__ = None


__all__ = [
    "DSS",
    "DatasetPath",
    "Catalog",
    "DatasetPathCollection",
    "RegularTimeseries",
]
