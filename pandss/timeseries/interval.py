import json
from functools import total_ordering
from pathlib import Path


class EPartStandard:
    def __init__(self):
        # values from DSS documentation
        # https://www.hec.usace.army.mil/confluence/dssdocs/dsscprogrammer/time-series-data
        here = Path(__file__).parent
        with open(here / "interval_to_seconds.json", "r") as J:
            self.e_to_sec: dict[str, int | None] = json.load(J)
        with open(here / "interval_to_period_offset.json", "r") as J:
            self.e_to_period_offset: dict[str, int | None] = json.load(J)

    @property
    def valid_e(self) -> set:
        return set(self.e_to_sec) | set(self.e_to_period_offset)

    def __contains__(self, __other) -> bool:
        return __other in self.e_to_sec

    def get_seconds(self, e: str) -> int:
        if e not in self.e_to_sec:
            raise ValueError(f"{e=} not recognized, must be one of {self.valid_e}")
        return self.e_to_sec[e]

    def get_period_offset(self, e: str) -> str:
        if e not in self.e_to_period_offset:
            raise ValueError(f"{e=} not recognized, must be one of {self.valid_e}")
        return self.e_to_period_offset[e]


@total_ordering
class Interval:
    """The interval of a timeseries object.

    See Also
    --------
    Interval.seconds: The number of seconds in the interval.
    Interval.offset: The pandas Period Offset Alias for the interval.
    """

    __slots__ = ("e", "_lookup")

    def __init__(self, e: str):
        self._lookup = EPartStandard()
        if e not in self._lookup:  # make sure the e is parsable
            raise ValueError(
                f"{e=} not recognized, must be one of {self._lookup.valid_e}"
            )
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

    @property
    def seconds(self) -> int:
        return self._lookup.get_seconds(self.e)

    @property
    def offset(self) -> str:
        return self._lookup.get_period_offset(self.e)
