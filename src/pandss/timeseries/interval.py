from functools import total_ordering
from re import compile

from pandas import offsets

# values from DSS documentation
# https://www.hec.usace.army.mil/confluence/dssdocs/dsscprogrammer/time-series-data
INTERVAL_TO_PANDAS_OFFSET = {
    "YEAR": offsets.YearEnd,
    "MON": offsets.MonthEnd,
    "MONTH": offsets.MonthEnd,
    "SEMI-MONTH": offsets.SemiMonthEnd,
    # Not supported in pandas, so raise an error when attempting
    "TRI-MONTH": lambda n: NotImplementedError("TRI-MONTH interval not supported"),
    "WEEK": offsets.Week,
    "DAY": offsets.Day,
    "HOUR": offsets.Hour,
    "MIN": offsets.Minute,
    "MINUTE": offsets.Minute,
    "SECOND": offsets.Second,
    "IR-CENTURY": lambda n: offsets.YearEnd(n * 100),
    "IR-DECADE": lambda n: offsets.YearEnd(n * 10),
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
            raise ValueError(
                f"couldn't parse {e=}, using regex={str(interval_pattern)}"
            )
        n, base = regex_match.groups()
        factory = self._lookup.get(base.upper(), None)
        if factory is None:
            raise ValueError(f"cannot find offset for {e=}")
        if not n:
            n = 1
        self.offset: offsets.DateOffset = factory(int(n))
        self.e = e

    def __eq__(self, __other) -> bool:
        if isinstance(__other, Interval):
            __other = __other.seconds
        return self.seconds == __other

    def __lt__(self, __other) -> bool:
        if isinstance(__other, Interval):
            __other = __other.seconds
        return self.seconds < __other

    def __hash__(self):
        return hash(self.e)

    def __str__(self) -> str:
        return self.e

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.e}>"

    @property
    def seconds(self) -> int:
        try:
            return self.offset.nanos / 1_000_000_000
        except ValueError:
            raise AttributeError(
                "interval is not always the same length, "
                + "cannot determine the number of seconds: "
                + "leap years, 31/30/29/28 day months, etc."
                + "pandas raises an error, see above."
            )

    @property
    def freq(self) -> str:
        return self.offset
