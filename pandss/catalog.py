from dataclasses import dataclass
from pathlib import Path
from typing import Self

from .paths import DatasetPath, DatasetPathCollection


@dataclass(
    kw_only=True,
    frozen=True,
    slots=True,
    eq=True,
)
class Catalog(DatasetPathCollection):
    src: Path

    @classmethod
    def from_strs(cls, paths: list[str], src: Path) -> Self:
        paths = set(DatasetPath.from_str(p) for p in paths)
        if any(p.has_wildcard for p in paths):
            raise ValueError(f"{cls.__name__} cannot be created with wildcard paths")
        return cls(
            paths=paths,
            src=src,
        )

    def findall(self, path: DatasetPath) -> DatasetPathCollection:
        return super(Catalog, self).findall(path)
