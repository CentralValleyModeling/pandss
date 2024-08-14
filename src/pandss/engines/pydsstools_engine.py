import logging
from datetime import time, timedelta
from pathlib import Path
from typing import Any, Self

import numpy as np
from pydsstools.heclib.dss import HecDss

from ..catalog import Catalog
from ..errors import DatasetNotFound, WildcardError
from ..paths import DatasetPath
from ..quiet import suppress_stdout_stderr
from ..timeseries import Interval, RegularTimeseries
from . import EngineABC, must_be_open


class PyDssToolsEngine(EngineABC):
    def __init__(self, src: str | Path, use_units: bool = True):
        self.use_units = use_units
        self._catalog = None
        self._is_open = False
        self.src = Path(src).resolve()
        self._object: HecDss.Open = None
        self._create_new = False

    def open(self) -> Self:
        """Opens the underlying DSS file"""
        self._object = HecDss.Open(str(self.src))
        self._is_open = True

    @must_be_open
    def close(self):
        """Closes the underlying DSS file"""
        self._object.close()
        self._is_open = False

    @must_be_open
    def read_catalog(self) -> Catalog:
        """Reads the DSS catalog to a pandss.Catalog object."""
        logging.debug(f"reading catalog, {self.src=}")
        with suppress_stdout_stderr():
            paths: list[str] = self._object.getPathnameList("", sort=1)
        catalog = Catalog.from_strs(
            paths=paths,
            src=self.src,
        )
        logging.debug(f"catalog read, size is {len(catalog)}")
        self._catalog = catalog
        return catalog

    @must_be_open
    def read_rts(self, path: DatasetPath) -> RegularTimeseries:
        """Reads a single regular timeseries from a DSS file."""
        logging.debug(f"reading regular time series, {path}")
        if path.has_wildcard:
            raise WildcardError("path has wildcard, use `read_multiple_rts` method")
        # pydsstools uses a single "*"" char for wildcards in D-parts
        p = str(path)
        if path.d == ".*":
            p = p.replace(".*", "*")
        # read data from file
        with suppress_stdout_stderr():
            try:
                data = self._object.read_ts(p)
            except ValueError:
                raise DatasetNotFound(p)

        return self._convert_to_pandss_rts(data, path)

    def _convert_to_pandss_rts(
        self,
        data: Any,
        path: DatasetPath | str,
    ) -> RegularTimeseries:
        if isinstance(path, str):
            path = DatasetPath.from_str(path)
        attr_map = {
            "values": "values",
            "dates": "pytimes",
            "period_type": "type",
            "units": "units",
            "interval": "interval",
        }
        kwargs = {L: getattr(data, R) for L, R in attr_map.items()}
        # Add the path object to the keyword argument dict
        if isinstance(path, str):
            path = DatasetPath.from_str(path)
        kwargs["path"] = path
        # Replace no-data with nan
        kwargs["values"][data.nodata] = np.nan
        # Adjust the way pydsstools interprets dates in HEC-DSS files.
        interval = kwargs["interval"]
        # Only fix for intervals greater gte 1 day
        if interval >= (60 * 60 * 24):
            fixed_dates = list()
            for date in kwargs["dates"]:
                # Midnight in HEC-DSS belongs to the day prior, which differs
                # from the datetime module. Offset by 1 second to compensate.
                if date.time() == time(0, 0):
                    date = date - timedelta(seconds=1)
                fixed_dates.append(date)
            kwargs["dates"] = fixed_dates
        kwargs["dates"] = np.array(kwargs["dates"], dtype="datetime64")
        # use interval object
        kwargs["interval"] = Interval(path.e)
        return RegularTimeseries(**kwargs)
