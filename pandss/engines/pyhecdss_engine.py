import logging
from pathlib import Path
from typing import Self

import numpy as np
import pandas as pd
import pyhecdss

from ..catalog import Catalog
from ..errors import FileVersionError
from ..paths import WILDCARD_PATTERN, DatasetPath
from ..quiet import suppress_stdout_stderr
from ..timeseries import RegularTimeseries
from . import EngineABC, must_be_open


class PyHecDssEngine(EngineABC):
    def __init__(self, src: str | Path):
        self._catalog = None
        self._is_open = False
        self.src = Path(src).resolve()
        _, file_version = pyhecdss.get_version(str(self.src))
        if file_version not in [6, -1]:
            raise FileVersionError(
                f"pyhecdss con only interact with version 6 DSS-Files, {file_version=}"
            )
        self._object: pyhecdss.DSSFile = None
        self._create_new = True

    def open(self) -> Self:
        """Opens the underlying DSS file"""
        self._object = pyhecdss.DSSFile(
            str(self.src),
            create_new=self._create_new,
        )
        self._is_open = True

    @must_be_open
    def close(self):
        """Closes the underlying DSS file"""
        self._object.close()
        self._is_open = False

    @must_be_open
    def read_catalog(self) -> Catalog:
        """Reads the DSS catalog to a pandss.Catalog object."""
        logging.info(f"reading catalog, {self.src=}")
        with suppress_stdout_stderr():
            df = self._object.read_catalog()
        catalog = Catalog.from_frame(
            df=df,
            src=self.src,
        )
        logging.info(f"catalog read, size is {len(catalog)}")
        self._catalog = catalog
        return catalog

    @must_be_open
    def read_rts(self, path: DatasetPath) -> RegularTimeseries:
        """Reads a single regular timeseries from a DSS file."""
        logging.info(f"reading regular time series, {path}")
        if path.has_wildcard:
            raise ValueError("path has wildcard, use `read_multiple_rts` method")
        # If the date is a wildcard, pyhecdss needs to request each and combine
        if path.d == ".*":
            with suppress_stdout_stderr():
                data = [
                    self._object.read_rts(str(p)) for p in self.catalog.resolve_wildcard(path)
                ]
                df = pd.concat(d.data for d in data)
                data = pyhecdss.DSSData(df, data[0].units, data[0].period_type)
        # Otherwise just read the single timeseries
        else:
            with suppress_stdout_stderr():
                data = self._object.read_rts(str(path))
        # magic number that is returned by the library in some cases
        mask = data.data.values == -3.4028234663852886e38
        data.data.loc[mask] = np.nan
        data.data.dropna(inplace=True)

        return self._convert_to_pandss_rts(data, path)

    def write_rts(self, path: DatasetPath, rts: RegularTimeseries):
        periods = pd.DatetimeIndex(rts.dates).to_period()
        df = pd.DataFrame(
            data=rts.values,
            index=periods,
        )
        p = f"/{path.a}/{path.b}/{path.c}//{path.e}/{path.f}/"
        self._object.write_rts(p, df, rts.units, rts.period_type)

    @staticmethod
    def _convert_to_pandss_rts(
        data: pyhecdss.DSSData, path: DatasetPath
    ) -> RegularTimeseries:
        # Convert to RegularTimeseries
        attr_map = {
            "period_type": "period_type",
            "units": "units",
        }
        kwargs = {L: getattr(data, R) for L, R in attr_map.items()}
        # Add values and dates
        kwargs["values"] = data.data.values
        # Sometimes indexes are PeriodIndexes, other times they are DatetimeIndex
        dates = data.data.index
        if isinstance(dates, pd.PeriodIndex):
            dates = dates.end_time
        if not isinstance(dates, pd.DatetimeIndex):
            raise ValueError(f"unknown datetype in pyhecdss object: {type(dates)}")
        kwargs["dates"] = dates.values.astype("datetime64[s]")
        kwargs["interval"] = None
        # Add the path object to the keyword argument dict
        if isinstance(path, str):
            path = DatasetPath.from_str(path)
        kwargs["path"] = path

        return RegularTimeseries(**kwargs)
