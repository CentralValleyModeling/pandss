from dataclasses import dataclass, fields

from numpy import datetime64, float64
from numpy.typing import NDArray
from pandas import DataFrame, DatetimeIndex, MultiIndex, PeriodIndex

from .paths import DatasetPath


@dataclass(
    kw_only=True,
    frozen=True,
    eq=True,
    slots=True,
)
class RegularTimeseries:
    path: DatasetPath
    values: NDArray[float64]
    dates: NDArray[datetime64]
    period_type: str
    units: str
    interval: str

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(path={str(self.path)}, len={len(self)})"

    def __len__(self) -> int:
        return len(self.values)

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
