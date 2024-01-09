from pathlib import Path
from typing import Iterator

from .catalog import Catalog
from .dss import DSS
from .paths import DatasetPath, DatasetPathCollection
from .timeseries import RegularTimeseries


def read_catalog(src: str | Path) -> Catalog:
    with DSS(src) as dss:
        return dss.read_catalog()


def read_rts(src: str | Path, path: DatasetPath) -> RegularTimeseries:
    with DSS(src) as dss:
        return dss.read_rts(path)


def read_multiple_rts(
    src: str | Path,
    path: DatasetPath | DatasetPathCollection,
    drop_date: bool = True,
) -> Iterator[RegularTimeseries]:
    with DSS(src) as dss:
        yield from dss.read_multiple_rts(path, drop_date)
