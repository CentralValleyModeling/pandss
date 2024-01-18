from dataclasses import dataclass, fields

from numpy import datetime64
from numpy.typing import NDArray
from pandas import DataFrame, MultiIndex
from pint import Quantity

from .paths import DatasetPath


@dataclass(
    kw_only=True,
    eq=True,
    slots=True,
)
class RegularTimeseries:
    path: DatasetPath
    values: Quantity | NDArray
    dates: NDArray[datetime64]
    period_type: str
    units: str
    interval: int

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(path={str(self.path)}, len={len(self)})"

    def __len__(self) -> int:
        return len(self.values)

    def __eq__(self, __other: object) -> bool:
        if not isinstance(__other, self.__class__):
            return False
        for f in fields(self):
            if not hasattr(__other, f.name):
                return False
            elif hasattr(getattr(self, f.name), "__iter__"):
                for left, right in zip(getattr(self, f.name), getattr(__other, f.name)):
                    if left != right:
                        return False
            elif getattr(self, f.name) != getattr(__other, f.name):
                return False
        return True

    def to_frame(self) -> DataFrame:
        header = dict(self.path.items())
        header["UNITS"] = self.units
        header["PERIOD_TYPE"] = self.period_type
        header["INTERVAL"] = self.interval
        header = {k.upper(): (v,) for k, v in header.items()}
        columns = MultiIndex.from_arrays(
            tuple(header.values()), names=tuple(header.keys())
        )
        df = DataFrame(
            index=self.dates,
            data=self.values,
            columns=columns,
        )

        return df
