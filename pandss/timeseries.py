from dataclasses import dataclass
from typing import Any, Self

from .paths import DatasetPath


@dataclass(
    kw_only=True,
    frozen=True,
    eq=True,
    slots=True,
)
class RegularTimeseries:
    path: DatasetPath
    values: list[float]
    dates: list[str]
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
        if isinstance(path, str):
            path = DatasetPath.from_str(path)
        kwargs["path"] = path
        return RegularTimeseries(**kwargs)
