import logging
from datetime import time, timedelta
from pathlib import Path
from typing import Any, Self

import numpy as np
from hecdss import HecDss
from hecdss import Catalog as hec_Catalog

from ..catalog import Catalog
from ..errors import DatasetNotFound, WildcardError
from ..paths import DatasetPath
from ..quiet import suppress_stdout_stderr
from ..timeseries import Interval, RegularTimeseries
from . import EngineABC, must_be_open


class HecDssPythonEngine(EngineABC):
    def __init__(self, src: str | Path, use_units: bool = True):
        self.use_units = use_units
        self._catalog = None
        self._is_open = False
        self.src = Path(src).resolve()
        self._object: HecDss = None
        self._create_new = False

    def open(self) -> Self:
        """Opens the underlying DSS file"""
        self._object = HecDss(str(self.src))
        self._is_open = True

    @must_be_open
    def close(self):
        """Closes the underlying DSS file"""
        self._object.close()
        self._object = None
        self._is_open = False

    @must_be_open
    def read_catalog(self) -> Catalog:
