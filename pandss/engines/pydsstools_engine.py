from pathlib import Path
from typing import Self
import logging

from pydsstools.heclib.dss import HecDss

from . import EngineABC
from ..catalog import Catalog
from ..paths import DatasetPath
from ..timeseries import RegularTimeseries
from ..quiet import suppress_stdout_stderr


class PyDssToolsEngine(EngineABC):
    def __init__(self, src: str | Path):
        self._catalog = None
        self._is_open = False
        self.src = Path(src).resolve()
        self._object: HecDss.Open = None

    def open(self) -> Self:
        """Opens the underlying DSS file"""
        self._object = HecDss.Open(str(self.src))
        self._is_open = True

    def close(self):
        """Closes the underlying DSS file"""
        self._object.close()
        self._is_open = False

    def read_catalog(self) -> Catalog:
        """Reads the DSS catalog to a pandss.Catalog object."""
        logging.info(f"reading catalog, {self.src=}")
        with suppress_stdout_stderr():
            paths: list[str] = self._object.getPathnameList("", sort=1)
        catalog = Catalog.from_strs(
            paths=paths,
            src=self.src,
        )
        logging.info(f"catalog read, size is {len(catalog)}")
        self._catalog = catalog
        return catalog

    def read_rts(self, path: DatasetPath) -> RegularTimeseries:
        """Reads a single regular timeseries from a DSS file."""
        logging.info(f"reading regular time series, {path}")
        if path.has_wildcard:
            raise ValueError("path has wildcard, use `read_multiple_rts` method")

        with suppress_stdout_stderr():
            data: list[str] = self._object.read_ts(str(path))
        return RegularTimeseries.from_pydsstools(data, path=path)
