from pathlib import Path

from .catalog import Catalog
from .dss import DSS
from .paths import DatasetPath
from .timeseries import RegularTimeseries


def read_catalog(src: str | Path) -> Catalog:
    with DSS(src) as dss:
        return dss.read_catalog()


def read_rts(src: str | Path, path: DatasetPath) -> RegularTimeseries:
    with DSS(src) as dss:
        return dss.read_rts(path)
