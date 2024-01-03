from dataclasses import dataclass, field
from typing import Self

from .paths import DatasetPath


@dataclass(kw_only=True, slots=True)
class Catalog:
    paths: list[DatasetPath] = field(default_factory=list)

    def __post_init__(self):
        bad_type = [obj for obj in self.paths if not isinstance(obj, DatasetPath)]
        if bad_type:
            n = len(bad_type)
            bad_types = set([type(obj) for obj in bad_type])
            raise ValueError(
                f"paths must be given as `{DatasetPath.__name__}` objects, {n} bad items given, seen types: {bad_types}"
            )

    def __len__(self):
        return len(self.paths)

    def append(self):
        raise NotImplementedError()

    @staticmethod
    def from_strs(paths: list[str]) -> Self:
        return Catalog(paths=[DatasetPath.from_str(p) for p in paths])
