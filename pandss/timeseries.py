from dataclasses import dataclass, fields
from datetime import datetime, time, timedelta
from typing import Any, Self

import numpy as np
from pandas import DataFrame, MultiIndex

from .paths import DatasetPath


@dataclass(
    kw_only=True,
    frozen=True,
    eq=True,
    slots=True,
)
class RegularTimeseries:
    path: DatasetPath
    values: np.ndarray
    dates: list[datetime]
    period_type: str
    units: str
    interval: str

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(path={str(self.path)}, len={len(self)})"

    def __len__(self) -> int:
        return len(self.values)

    @staticmethod
    def from_pydsstools(obj: Any, path: str | DatasetPath) -> Self:
        attr_map = {
            "values": "values",
            "dates": "pytimes",
            "period_type": "type",
            "units": "units",
            "interval": "interval",
        }
        kwargs = {L: getattr(obj, R) for L, R in attr_map.items()}
        # Add the path object to the keyword argument dict
        if isinstance(path, str):
            path = DatasetPath.from_str(path)
        kwargs["path"] = path
        # Adjust the way pydsstools interprets dates in HEC-DSS files.
        dates = kwargs["dates"]
        interval = kwargs["interval"]
        # Only fix for intervals greater gte 1 day
        if interval >= (60 * 60 * 24):
            fixed_dates = list()
            for date in dates:
                # Midnight in HEC-DSS belongs to the day prior, which differs
                # from the datetime module. Offset by 1 second to compensate.
                if date.time() == time(0, 0):
                    date = date - timedelta(seconds=1)
                fixed_dates.append(date)
            kwargs["dates"] = fixed_dates

        return RegularTimeseries(**kwargs)

    def to_frame(self) -> DataFrame:
        header = dict(self.path.items())
        header["UNITS"] = self.units
        header["PERIOD_TYPE"] = self.period_type
        header["INTERVAL"] = self.interval
        header = {k.upper(): (v,) for k, v in header.items()}
        columns = MultiIndex.from_arrays(
            tuple(header.values()), names=tuple(header.keys())
        )
        df = DataFrame(index=self.dates, data=self.values, columns=columns)

        return df
