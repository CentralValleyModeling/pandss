from functools import total_ordering
from re import compile
from typing import Callable
from warnings import warn

from pandas import offsets


class AnnualOffset:
    """Used to create offset factories for different multi-year offsets not in
    pandas by default.
    """

    def __init__(self, multiplier: int):
        self.multiplier = multiplier

    def __call__(self, n: int) -> offsets.YearEnd:
        return offsets.YearEnd(n * self.multiplier)


class NotImplementedInterval(NotImplementedError):
    def __init__(self, *args, **kwargs):
        super().__init__("The interval is not supported.")


# values from DSS documentation
# https://www.hec.usace.army.mil/confluence/dssdocs/dsscprogrammer/time-series-data
INTERVAL_TO_PANDAS_OFFSET: dict[str, Callable[[int], offsets.BaseOffset]] = {
    "YEAR": offsets.YearEnd,
    "MON": offsets.MonthEnd,
    "MONTH": offsets.MonthEnd,
    "SEMI-MONTH": offsets.SemiMonthEnd,
    # Not supported in pandas, so raise an error when attempting
    "TRI-MONTH": NotImplementedInterval,
    "WEEK": offsets.Week,
    "DAY": offsets.Day,
    "HOUR": offsets.Hour,
    "MIN": offsets.Minute,
    "MINUTE": offsets.Minute,
    "SECOND": offsets.Second,
    "IR-CENTURY": AnnualOffset(100),
    "IR-DECADE": AnnualOffset(10),
    "IR-YEAR": offsets.YearEnd,
    "IR-MONTH": offsets.MonthEnd,
    "IR-DAY": offsets.Day,
}

interval_pattern = compile(r"(?P<n>\d+)?(?P<key>[a-zA-Z\-]+)")


@total_ordering
class Interval:
    """The interval of a timeseries object.

    See Also
    --------
    Interval.seconds: The number of seconds in the interval.
    Interval.offset: The pandas Period Offset Alias for the interval.
    """

    __slots__ = ("e", "_lookup", "offset")

    def __init__(self, e: str):
        self._lookup = INTERVAL_TO_PANDAS_OFFSET
        regex_match = interval_pattern.match(e)
        if not regex_match:
            self.e = None
            raise ValueError(
                f"couldn't parse {e=}, using regex={str(interval_pattern)}"
            )
        n, base = regex_match.groups()
        factory = self._lookup.get(base.upper(), None)
        if factory is None:
            raise ValueError(f"cannot find offset for {e=}")
        if not n:
            n = 1
        self.offset = factory(int(n))
        self.e = e

    def __eq__(self, __other) -> bool:
        if isinstance(__other, Interval):
            __other = __other.offset
        return self.offset == __other

    def __lt__(self, __other) -> bool:
        if isinstance(__other, Interval):
            __other = __other.seconds
        return self.seconds < __other

    def __hash__(self):
        return hash(self.e)

    def __str__(self) -> str:
        return self.e

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(e={self.e})"

    @property
    def seconds(self) -> int:
        try:
            return self.offset.nanos / 1_000_000_000
        except ValueError:
            warn(
                f"\nThis offset type ({self.offset.name}) has irregular "
                + "durations, so pandas will not calculate the seconds in this"
                + "period. However, pandss defaults to treating all "
                + "non-regular width offsets as if they were non-leap year, "
                + "30 day months.\nThis is consistent with DSS internals as of"
                + " March 2024.\npandss only supports this for year, month, "
                + "and week offsets.",
                category=Warning,
            )
            seconds_in_offset = {
                "Y": 365 * 24 * 60 * 60,
                "M": 30 * 24 * 60 * 60,
                "W": 7 * 24 * 60 * 60,
            }
            key = self.offset.name[0].upper()
            return seconds_in_offset[key]

    @property
    def freq(self) -> str:
        """alias for Interval.offset"""
        return self.offset
