from pathlib import Path
from typing import Iterator

from .catalog import Catalog
from .dss import DSS
from .errors import WildcardError
from .paths import DatasetPath, DatasetPathCollection
from .timeseries import RegularTimeseries


def read_catalog(src: str | Path) -> Catalog:
    """Read the DSS catalog, and return a pandss.Catalog object.

    Parameters
    ----------
    src : str | pathlib.Path
        The path to the DSS file to be read.

    Returns
    -------
    Catalog
        The catalog of the DSS file.
    """
    with DSS(src) as dss:
        return dss.read_catalog()


def read_rts(src: str | Path, path: DatasetPath | str) -> RegularTimeseries:
    """Read the DSS file for a single regular timeseries, and return a
    pandss.RegularTimeseries object.

    Parameters
    ----------
    src : str | pathlib.Path
        The path to the DSS file to be read from.
    path : pandss.DatasetPath
        The path within the DSS file that represents the data to be read.

    Returns
    -------
    RegularTimeseries
        The dataset read from the DSS file.
    """
    with DSS(src) as dss:
        return dss.read_rts(path)


def read_multiple_rts(
    src: str | Path,
    path: DatasetPath | DatasetPathCollection,
    drop_date: bool = True,
) -> Iterator[RegularTimeseries]:
    """Read the DSS file for multiple regular timeseries, and return an
    iterator of pandss.RegularTimeseries objects.

    Parameters
    ----------
    src : str | Path
        The path to the DSS file to be read from.
    path : DatasetPath | DatasetPathCollection
        The paths to be found, or a single path with wildcards that resolves to
        multiple paths.
    drop_date : bool, optional
        A flag to ignore the dates in the paths provided, if True, the d part
        of the paths provided will be ignored, by default True

    Yields
    ------
    Iterator[RegularTimeseries]
        The datasets read from the DSS file.
    """
    with DSS(src) as dss:
        yield from dss.read_multiple_rts(path, drop_date)


def copy_rts(
    src: str | Path,
    dst: str | Path,
    paths: tuple[DatasetPath | str, DatasetPath | str],
):
    """Copy one regular timeseries from a source DSS file to a destination DSS.

    Parameters
    ----------
    src : str | Path
        The source DSS file, data will be read from here.
    dst : str | Path
        The destination file, data wil be written here.
    paths : tuple[DatasetPath  |  str, DatasetPath  |  str]
        The dataset to be copied from one file to the other. The first element
        of the tuple is the name in the source file, the second element in the
        tuple is the name in the destination file.

    Raises
    ------
    WildcardError
        Raised when the paths given contain wildcards that resolve to multiple
        DatasetPaths.
    """
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


def copy_multiple_rts(
    src: str | Path,
    dst: str | Path,
    paths: Iterator[tuple[DatasetPath | str, DatasetPath | str]],
):
    """Copy multiple regular timeseries from a source DSS file to a destination
    DSS.

    Parameters
    ----------
    src : str | Path
        The source DSS file, data will be read from here.
    dst : str | Path
        The destination file, data wil be written here.
    paths : Iterator[tuple[DatasetPath | str, DatasetPath | str]]
        The datasets to be copied from one file to the other. Each tuple in the
        iterator is seen as a different dataset to copy. The first element of
        each tuple is the name in the source file, the second element in each
        tuple is the name in the destination file.

    Raises
    ------
    WildcardError
        Raised when any path given contains a wildcard that resolves to
        multiple DatasetPaths.
    """
    with DSS(src) as SRC, DSS(dst) as DST:
        for src_path, dst_path in paths:
            if isinstance(src_path, str):
                src_path = DatasetPath.from_str(src_path)
            if isinstance(dst_path, str):
                dst_path = DatasetPath.from_str(dst_path)
            if src_path.has_wildcard or dst_path.has_wildcard:
                raise WildcardError(
                    f"Cannot write paths with wildcards: {src_path}, {dst_path}"
                )
            DST.write_rts(dst_path, SRC.read_rts(src_path))
