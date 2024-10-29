from copy import deepcopy
from dataclasses import dataclass, fields
from typing import Literal, Self, get_args

from numpy import array, datetime64, datetime_as_string, intersect1d, ndarray
from numpy.typing import NDArray
from pandas import DataFrame, Index, MultiIndex

from ..paths import DatasetPath
from .interval import Interval


def decode_json_date_array(a: tuple[str]) -> NDArray[datetime64]:
    return array(a, dtype="datetime64")


HEADER_OPTIONS = Literal[
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "UNITS",
    "PERIOD_TYPE",
    "INTERVAL",
]


@dataclass(
    kw_only=True,
    eq=True,
    slots=True,
)
class RegularTimeseries:
    """A regular timeseries within a DSS file.

    Attributes
    -------
    path: DatasetPath
        The A-F path that the data had in the originating DSS file
    values: NDArray
        The timeseries data
    dates: NDArray[datetime64]
        Rendered dates, the alignment of which depends on the interval, and the
        first date in the timeseries. Different Engines align dates differently
    period_type: str
        The DSS period type the data had in the originating DSS file.
    units: str
        The units of the timeseries data
    interval: Interval
        The time interval in seconds between data in the DSS file.
    """

    path: DatasetPath
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
        """The size of the data in the RegularTimeseries.

        Returns
        -------
        int
            The length of `self.values`
        """
        return len(self.values)

    def __eq__(self, __other: object) -> bool:
        """Compare whether or not two `RegularTimeseries` are equal.

        Compares all fields in the dataclass, and fails equality if any are not exactly
        equal.

        Parameters
        ----------
        __other : object
            The other object to compare to.

        Returns
        -------
        bool
            Whether or not the two objects are equal.
        """
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
        """Perform the arithmetic on two `RegularTimeseries` objects.

        The operations are performed accordingly:
        - interval: No change, must be identical left and right
        - period_type: No change, must be identical left and right
        - units: No change, must be identical left and right
        - path: Combined part by part, where identical parts are not changed, and
                differing parts are concatenated
        - dates: Intersected with __other.dates
        - values: The arithmatic is done on the subset of values selected using the same
                intersection used for dates


        Parameters
        ----------
        __other : Self
            The other object to use when doing arithmetic.
        method_name : str
            One of `__add__`, `__sub__`, or other numeric dunders

        Returns
        -------
        dict
            The kwargs to use by `__init__` of the objects class

        Raises
        ------
        ValueError
            Raised if the two objects are not the same type
        ValueError
            Raised if certain attributes do not match as required
        """
        CONCAT_KEY = {"__add__": "+", "__sub__": "-"}
        concat_char = CONCAT_KEY[method_name]
        # Validate action
        if not isinstance(__other, self.__class__):
            raise ValueError(
                f"Cannot perform arithmetic {self.__class__.__name__} "
                + f"with {type(__other)}"
            )
        for attr in ("interval", "period_type", "units"):
            s = getattr(self, attr)
            o = getattr(__other, attr)
            if s != o:
                raise ValueError(f"Cannot add differing {attr}: {s}, {o}")
        # Get kwargs for new instance
        # path
        new_path_kwargs = dict()
        for part in ("a", "b", "c", "d", "e", "f"):
            part_self = getattr(self.path, part)
            part_other = getattr(__other.path, part)
            if part_self == part_other:
                new_path_kwargs[part] = part_self
            else:
                new_path_kwargs[part] = f"{part_self}{concat_char}{part_other}"
        if self.path == __other.path:  # Rare case of adding identical paths
            new_path_kwargs["b"] = f"{self.path.b}{concat_char}{__other.path.b}"
        new_path = DatasetPath(**new_path_kwargs)
        # dates
        new_dates = intersect1d(self.dates, __other.dates)
        # values
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
            units=self.units,
            period_type=self.period_type,
            interval=self.interval,
        )
        return kwargs

    def update(self, **kwargs) -> Self:
        """Update an attribute on the object, creating a new one in the process

        Returns
        -------
        Self
            A RegularTimseries object

        Raises
        ------
        ValueError
            Raised if the length of the values and dates arrays don't match
            after updating
        """
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

    def to_frame(
        self,
        include_in_header: tuple[HEADER_OPTIONS, ...] | HEADER_OPTIONS = None,
    ) -> DataFrame:
        """Create a `pandas.DataFrame` from the `RegularTimeseries`

         Parameters
        ----------
        include_in_header : tuple[str, ...]
            The headers to include in the resulting DataFrame. If this iterable has
            more than one entry, the final DataFrame will have a MultiIndex for its
            `column` attribute.

        Returns
        -------
        DataFrame
            The `DataFrame`, indexed by dates, with column names of: `A`-`F`, `UNITS`,
            `PERIOD_TYPE`, `INTERVAL`
        """
        header_options = get_args(HEADER_OPTIONS)
        if include_in_header is None:
            include_in_header = tuple(v for v in header_options)
        if isinstance(include_in_header, str):
            include_in_header = (include_in_header,)  # Make sure to pack the tuple
        if any(v not in header_options for v in include_in_header):
            raise ValueError(
                f"only {header_options} are accepted, given: {include_in_header}"
            )
        header = dict(self.path.items())
        header["UNITS"] = self.units
        header["PERIOD_TYPE"] = self.period_type
        header["INTERVAL"] = str(self.interval)
        header = {
            k.upper(): (v,) for k, v in header.items() if k.upper() in include_in_header
        }
        if len(header) > 1:
            columns = MultiIndex.from_arrays(
                tuple(header.values()), names=tuple(header.keys())
            )
        else:
            k, v = tuple(header.items())[0]
            columns = Index(data=v, name=k)
        df = DataFrame(
            index=self.dates,
            data=self.values,
            columns=columns,
        )

        return df

    def to_json(self) -> dict:
        """Create a JSON-compliant dictionary with the RegularTimeseries data

        Returns
        -------
        dict
            The JSON-compliant dictionary

        Raises
        ------
        AttributeError
            Raised if unrecognized fields are present in the object, protects against
            converting subclasses naievely.
        """
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
    def from_json(cls, obj: dict) -> Self:
        """Create a RegularTimeseries from a JSON-compliant dictionary

        Extra data in the dictionary is ignored

        Parameters
        ----------
        obj : dict
            A JSON-compliant dictionary

        Returns
        -------
        RegularTimeseries
            The object with data corresponding to the info in the dictionary

        Raises
        ------
        ValueError
            Raised if attributes are missing in the dictionary
        """
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
