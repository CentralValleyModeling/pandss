from pathlib import Path
from typing import Any, Self

from ..catalog import Catalog
from ..errors import ClosedDSSError
from ..paths import DatasetPath
from ..timeseries import RegularTimeseries


class EngineABC:
    src: Path
    use_units: bool = True
    _catalog: Catalog
    _is_open: bool
    _object: Any
    _create_new: bool

    def __init__(self, src: str | Path, use_units: bool = True):
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

    def read_rts(self, path: DatasetPath | str) -> RegularTimeseries:
        """Reads a single regular timeseries from a DSS file."""
        raise NotImplementedError(
            f"read_rts not implemented on {self.__class__.__name__}"
        )

    def write_rts(self, path: DatasetPath | str, rts: RegularTimeseries):
        """Writes a single regular timeseries to a DSS file."""
        raise NotImplementedError(
            f"write_rts not implemented on {self.__class__.__name__}"
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


class ModuleEngine:
    def __init__(self):
        self.selected = "pyhecdss"

    def set(self, __other: str | EngineABC):
        if not isinstance(__other, str | EngineABC):
            raise ValueError(f"engine type not recognized: {__other}:{type(__other)}")
        self.selected = __other


def get_engine(engine_name: str) -> EngineABC:
    if engine_name.lower() == "pyhecdss":
        from .pyhecdss_engine import PyHecDssEngine

        return PyHecDssEngine

    elif engine_name.lower() == "pydsstools":
        from .pydsstools_engine import PyDssToolsEngine

        return PyDssToolsEngine

    elif engine_name.lower() == "hec-dss-python":
        from .hec_dss_python_engine import HecDssPythonEngine

        return HecDssPythonEngine

    raise ValueError(f"engine_name not recognized: `{engine_name}`")


def must_be_open(method):
    def works_on_open_file(obj, *args, **kwargs):
        if obj._is_open is False:
            raise ClosedDSSError(f"file must be open to call {method}")
        else:
            return method(obj, *args, **kwargs)

    return works_on_open_file
