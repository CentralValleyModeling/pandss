import logging
from pathlib import Path
from typing import Iterator

from pydsstools.heclib.dss import HecDss

from .catalog import Catalog
from .paths import DatasetPath, DatasetPathCollection
from .quiet import silent, suppress_stdout_stderr
from .timeseries import RegularTimeseries


def must_be_open(method):
    def works_on_open_file(obj, *args, **kwargs):
        if obj.open is False:
            raise IOError(f"file must be open to call {method}")
        else:
            return method(obj, *args, **kwargs)

    return works_on_open_file


class DSS:
    """Wrapper class exposing functionality in pydsstools"""

    __slots__ = ["src", "_open", "_wrapped", "_catalog"]

    def __init__(self, src: str | Path):
        self.src: Path = Path(src).resolve()
        self._open = False
        self._wrapped: HecDss.Open = None
        self._catalog = None

    @property
    def open(self):
        return self._open

    @silent
    def __enter__(self):
        """Wraps pydsstools class `Open` and enables the use of this class
        in pythons context manager pattern.

        with DSS(path_to_dss_file) as DSS_File:
            # read/write data in DSS file
            ...
        # HecDss.Open.close() automatically called.


        Returns
        -------
        self
            Returns a DSS object.

        Raises
        ------
        RuntimeError
            Generic error for error opening DSS file
        """
        if not self.src.exists():
            raise FileNotFoundError(self.src)
        logging.info(f"opening dss file {self.src}")
        self._wrapped = HecDss.Open(str(self.src))
        self._open = True
        return self

    @silent
    def __exit__(self, exc_type, exc_inst, traceback):
        """Wraps pydsstools `HecDss.Open.close()` and enables the use of this class
        in pythons context manager pattern.
        """
        logging.info(f"closing dss file {self.src}")
        self._wrapped.close()
        self._open = False
        self._wrapped = None
        self._catalog = None

    @must_be_open
    def read_catalog(self) -> Catalog:
        logging.info(f"reading catalog, {self.src=}")
        with suppress_stdout_stderr():
            paths: list[str] = self._wrapped.getPathnameList("", sort=1)
        catalog = Catalog.from_strs(
            paths=paths,
            src=self.src,
        )
        logging.info(f"catalog read, size is {len(catalog)}")
        self._catalog = catalog
        return catalog

    @must_be_open
    def read_rts(self, path: DatasetPath) -> RegularTimeseries:
        logging.info(f"reading regular time series, {path}")
        if path.has_wildcard:
            raise ValueError("path has wildcard, use `read_multiple_rts` method")

        with suppress_stdout_stderr():
            data: list[str] = self._wrapped.read_ts(str(path))
        return RegularTimeseries.from_pydsstools(data, path=path)

    @must_be_open
    def read_multiple_rts(
        self,
        paths: DatasetPath | DatasetPathCollection,
        drop_date: bool = True,
    ) -> Iterator[RegularTimeseries]:
        if isinstance(paths, DatasetPath):
            if paths.has_wildcard:
                paths = self.resolve_wildcard(paths)
            else:
                logging.debug(
                    "`read_multiple_rts` called with only one path with no wildcards"
                )
                paths = DatasetPathCollection(paths={paths})

        if any(p.has_wildcard for p in paths):
            for p in paths:
                paths = paths & self.resolve_wildcard(p)
        if drop_date is True:
            paths = paths.drop_date()
        for p in paths:
            yield self.read_rts(p)

    @must_be_open
    def resolve_wildcard(self, path: DatasetPath) -> DatasetPathCollection:
        logging.info("resolving wildcards")
        if not path.has_wildcard:
            return DatasetPathCollection(paths={path})
        if self._catalog is None:
            self.read_catalog()

        return self._catalog.findall(path)
