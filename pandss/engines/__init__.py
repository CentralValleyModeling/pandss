from pathlib import Path
from typing import Self, Any

from ..catalog import Catalog
from ..paths import DatasetPath, DatasetPathCollection
from ..timeseries import RegularTimeseries


class EngineABC:
    src: Path
    _catalog: Catalog = None
    _is_open: bool = False
    _object: Any = None

    def __init__(self, src: str | Path):
        raise NotImplementedError(
            f"cannot initialize abstract base class {self.__class__.__name__}"
        )

    def open(self) -> Self:
        """Opens the underlying DSS file"""
        raise NotImplementedError(f"open not implemented on {self.__class__.__name__}")

    def close(self):
        """Closes the underlying DSS file"""
        raise NotImplementedError(f"close not implemented on {self.__class__.__name__}")

    def read_catalog(self) -> Catalog:
        """Reads the DSS catalog to a pandss.Catalog object."""
        raise NotImplementedError(
            f"read_catalog not implemented on {self.__class__.__name__}"
        )

    def read_rts(self, path: DatasetPath) -> RegularTimeseries:
        """Reads a single regular timeseries from a DSS file."""
        raise NotImplementedError(
            f"read_rts not implemented on {self.__class__.__name__}"
        )

    @property
    def catalog(self) -> Catalog:
        """Property to access the catalog of the DSS file"""
        if self._catalog is None:
            self.read_catalog()
        return self._catalog

    @property
    def is_open(self):
        return self._is_open


def get_engine(engine_name: str) -> EngineABC:
    if engine_name.lower() == "pyhecdss":
        from .pyhecdss_engine import PyHecDssEngine
        return PyHecDssEngine
    elif engine_name.lower() == "pydsstools":
        from .pydsstools_engine import PyDssToolsEngine
        return PyDssToolsEngine
    raise ValueError(f"engine_name not recognized: `{engine_name}`")
    
