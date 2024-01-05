import logging
from pathlib import Path

from pydsstools.heclib.dss import HecDss

from .catalog import Catalog
from .paths import DatasetPath
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

    __slots__ = ["src", "_open", "_wrapped"]

    def __init__(self, src: str | Path):
        self.src: Path = Path(src)
        self._open = False
        self._wrapped: HecDss.Open = None

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

    @must_be_open
    def read_catalog(self) -> Catalog:
        logging.info(f"reading catalog, {self.src=}")
        with suppress_stdout_stderr():
            paths: list[str] = self._wrapped.getPathnameList("", sort=1)
        catalog = Catalog.from_strs(paths)
        logging.info(f"catalog read, size is {len(catalog)}")

        return catalog

    @must_be_open
    def read_rts(self, path: DatasetPath) -> RegularTimeseries:
        if not self.open:
            raise ValueError(
                "Called `read_rts()` without file open, try using in a `with` statement."
            )
        logging.info(f"reading regular time series, {path}")
        with suppress_stdout_stderr():
            data: list[str] = self._wrapped.read_ts(str(path))
        data = RegularTimeseries.from_pydsstools(data, path=path)

        return data
