from pathlib import Path
from typing import Iterator

from .catalog import Catalog
from .dss import DSS
from .errors import WildcardError
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


def copy_rts(
    src: str | Path,
    dst: str | Path,
    paths: tuple[DatasetPath | str, DatasetPath | str],
):
    src_path, dst_path = paths
    if isinstance(src_path, str):
        src_path = DatasetPath.from_str(src_path)
    if isinstance(dst_path, str):
        dst_path = DatasetPath.from_str(dst_path)
    if src_path.has_wildcard or dst_path.has_wildcard:
        raise WildcardError(
            f"Cannot write paths with wildcards: {src_path}, {dst_path}"
        )

    with DSS(src) as SRC, DSS(dst) as DST:
        DST.write_rts(dst_path, SRC.read_rts(src_path))
