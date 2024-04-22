from copy import deepcopy
from dataclasses import dataclass, fields
from typing import Self

from numpy import array, datetime64, datetime_as_string, intersect1d, ndarray
from numpy.typing import NDArray
from pandas import DataFrame, MultiIndex

from ..paths import DatasetPath
from .interval import Interval


def decode_json_date_array(a: tuple[str]) -> NDArray[datetime64]:
    return array(a, dtype="datetime64")


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

    path: DatasetPath | str
    values: NDArray
    dates: NDArray[datetime64]
    period_type: str
    units: str
    interval: Interval

    def __post_init__(self):
        if not isinstance(self.path, DatasetPath):
            self.path = DatasetPath.from_str(self.path)
        if not isinstance(self.dates, ndarray):
            self.dates = array(self.dates, dtype=datetime64)
        if not isinstance(self.values, ndarray):
            self.values = array(self.values)
        if not isinstance(self.interval, Interval):
            self.interval = Interval(self.interval)

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
        kwargs = self._do_arithmetic(__other, "__add__")

        return RegularTimeseries(**kwargs)

    def _do_arithmetic(self, __other: Self, method_name: str) -> dict:
        # Validate action
        if not isinstance(__other, self.__class__):
            raise ValueError(
                f"Cannot perform arithmetic {self.__class__.__name__} "
                + f"with {type(__other)}"
            )
        for attr in ("interval", "period_type"):
            s = getattr(self, attr)
            o = getattr(__other, attr)
            if s != o:
                raise ValueError(f"Cannot add differing {attr}: {s}, {o}")
        # Get kwargs for new instance
        # units
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
        # dates
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

    def update(self, **kwargs) -> Self:
        values = kwargs.get("values", None)
        dates = kwargs.get("dates", None)
        if values or dates:
            if values is None:
                values = self.values
            if dates is None:
                dates = self.dates
            if len(values) != len(dates):
                raise ValueError(
                    "new values/dates must match length:\n"
                    + f"\t{len(values)=}\n"
                    + f"\t{len(dates)=}"
                )

        new_obj_kwargs = {f.name: deepcopy(getattr(self, f.name)) for f in fields(self)}
        new_obj_kwargs.update(**kwargs)

        return self.__class__(**new_obj_kwargs)

    def to_frame(self) -> DataFrame:
        header = dict(self.path.items())
        header["UNITS"] = self.units
        header["PERIOD_TYPE"] = self.period_type
        header["INTERVAL"] = str(self.interval)
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

    def to_json(self) -> dict:
        json_obj = dict()
        str_encode = ("path", "period_type", "units", "interval")
        tuple_encode = {"values": float, "dates": datetime_as_string}
        for f in fields(self):
            if f.name in str_encode:
                json_obj[f.name] = str(getattr(self, f.name))
            elif f.name in tuple_encode:
                encoder = tuple_encode[f.name]
                json_obj[f.name] = tuple(encoder(i) for i in getattr(self, f.name))
            else:
                raise AttributeError(
                    f"unrecognized field `{f}`, cannot encode {self.__class__} to JSON."
                )
        return json_obj

    @classmethod
    def from_json(cls, obj: dict):
        missing = list()
        for f in fields(cls):
            if f.name not in obj:
                missing.append(f.name)
        if missing:
            raise ValueError(f"missing the following attributes in JSON obj: {missing}")
        decoders = {
            "path": DatasetPath.from_str,
            "values": array,
            "dates": decode_json_date_array,
        }
        kwargs = dict()
        for f in fields(cls):
            decoder = decoders.get(f.name, str)
            kwargs[f.name] = decoder(obj.get(f.name))
        return cls(**kwargs)
