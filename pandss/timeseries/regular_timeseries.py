from dataclasses import dataclass, fields
from warnings import catch_warnings

from numpy import datetime64
from numpy.typing import NDArray
from pandas import DataFrame, MultiIndex
from pint import Quantity
from pint.errors import UnitStrippedWarning

from ..paths import DatasetPath
from .interval import Interval


@dataclass(
    kw_only=True,
    eq=True,
    slots=True,
)
class RegularTimeseries:
    """A regular timeseries within a DSS file.

    See Also
    --------
    RegularTimeseries.to_frame: Render this object to a pandas.DataFrame.
    """

    path: DatasetPath
    values: Quantity | NDArray
    dates: NDArray[datetime64]
    period_type: str
    units: str
    interval: Interval

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
        header["INTERVAL"] = str(self.interval)
        header = {k.upper(): (v,) for k, v in header.items()}
        columns = MultiIndex.from_arrays(
            tuple(header.values()), names=tuple(header.keys())
        )
        with catch_warnings(action="ignore", category=UnitStrippedWarning):
            df = DataFrame(
                index=self.dates,
                data=self.values,
                columns=columns,
            )

        return df
