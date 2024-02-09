from dataclasses import dataclass, fields
from typing import Self
from warnings import catch_warnings

from numpy import datetime64, intersect1d
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

    def __add__(self, __other: Self) -> Self:
        kwargs = self._do_arithmatic(__other, "__add__")

        return RegularTimeseries(**kwargs)

    def _do_arithmatic(self, __other: Self, method_name: str) -> dict:
        # Validate action
        if not isinstance(__other, self.__class__):
            raise ValueError(
                f"Cannot perform arithmatic {self.__class__.__name__} "
                + f"with {type(__other)}"
            )
        if __other.units != self.units:
            raise ValueError(
                f"Cannot perform arithmatic between {self.__class__.__name__} with"
                + f"differing units: {self.units}, {__other.units}"
            )
        for attr in ("interval", "period_type"):
            s = getattr(self, attr)
            o = getattr(__other, attr)
            if s != o:
                raise ValueError(f"Cannot add differing {attr}: {s}, {o}")
        # Get kwargs for new instance
        # units
        if isinstance(self.values, Quantity):
            new_units = self.values.units
        else:
            new_units = self.units
        # path
        new_path_kwargs = dict()
        for part in ("a", "b", "c", "d", "e", "f"):
            part_self = getattr(self.path, part)
            part_other = getattr(__other.path, part)
            if part_self == part_other:
                new_path_kwargs[part] = part_self
            else:
                new_path_kwargs[part] = f"{part_self}+{part_other}"
        if self.path == __other.path:  # Rare case of adding identical paths
            new_path_kwargs["b"] = f"{self.path.b}+{__other.path.b}"
        new_path = DatasetPath(**new_path_kwargs)

        new_dates = intersect1d(self.dates, __other.dates)
        mask_left = [date in new_dates for date in self.dates]
        values_left = self.values[mask_left]
        mask_right = [date in new_dates for date in __other.dates]
        values_right = __other.values[mask_right]
        method = getattr(values_left, method_name)
        new_values = method(values_right)

        kwargs = dict(
            path=new_path,
            values=new_values,
            dates=new_dates,
            units=new_units,
            period_type=self.period_type,
            interval=self.interval,
        )
        return kwargs

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
