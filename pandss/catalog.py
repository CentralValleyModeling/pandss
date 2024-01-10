from dataclasses import dataclass
from pathlib import Path
from typing import Self

from pandas import DataFrame

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

    @classmethod
    def from_frame(cls, df: DataFrame, src: Path) -> Self:
        df.columns = df.columns.str.lower()
        missing = [c for c in ("a", "b", "c", "d", "e", "f") if c not in df.columns]
        if missing:
            raise ValueError(
                f"DataFrame is misssing required columns: {missing}\n\t{df.sample(2)}"
            )
        df = df[["a", "b", "c", "d", "e", "f"]]
        paths = set(DatasetPath(*row) for row in df.itertuples(index=False))
        if any(p.has_wildcard for p in paths):
            raise ValueError(f"{cls.__name__} cannot be created with wildcard paths")
        return cls(paths=paths, src=src)

    def resolve_wildcard(self, path: DatasetPath) -> DatasetPathCollection:
        return super(Catalog, self).resolve_wildcard(path)

    def find(self, path: DatasetPath) -> DatasetPathCollection:
        """Alias for Catalog.resolve_wildcard"""
        return self.resolve_wildcard(path)
