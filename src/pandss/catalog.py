from dataclasses import dataclass
from pathlib import Path
from typing import Self

from pandas import DataFrame

from .errors import WildcardError
from .paths import DatasetPath, DatasetPathCollection


@dataclass(
    kw_only=True,
    frozen=True,
    slots=True,
    eq=True,
)
class Catalog(DatasetPathCollection):
    """An unordered collection of `pandss.DatasetPath` objects.

    A `Catalog` contains all of the A-F paths present in a DSS file. A `Catalog` isn't
    ususally initialized by the user, but is typically created by a `pandss.DSS` object
    using the `pandss.DSS.read_catalog()` method.

    Parameters
    ----------
    paths : set[DatasetPath]
        The paths present in the DSS Catalog.
    src: pathlib.Path
        The path to the DSS file on disk.
    """

    src: Path

    @classmethod
    def from_strs(cls, paths: list[str], src: Path) -> Self:
        """Create a `Catalog` from an iterable of strings"""
        paths = set(DatasetPath.from_str(p) for p in paths)
        if any(p.has_wildcard for p in paths):
            raise ValueError(f"{cls.__name__} cannot be created with wildcard paths")
        return cls(
            paths=paths,
            src=src,
        )

    @classmethod
    def from_frame(cls, df: DataFrame, src: Path) -> Self:
        """Create a `Catalog` from a `DataFrame`.

        Parameters
        ----------
        df : DataFrame
            The frame containing the paths to collect
        src : Path
            The path of the DSS file

        Returns
        -------
        Catalog
            The created object

        Raises
        ------
        ValueError
            Raised if the `DataFrame` is missing required columns
        WildcardError
            Raised if the paths in the `DataFrame` contain wildcards
        """
        df.columns = df.columns.str.lower()
        missing = [c for c in ("a", "b", "c", "d", "e", "f") if c not in df.columns]
        if missing:
            raise ValueError(
                f"DataFrame is misssing required columns: {missing}\n\t{df.sample(2)}"
            )
        df = df[["a", "b", "c", "d", "e", "f"]]
        paths = set(DatasetPath(*row) for row in df.itertuples(index=False))
        wild = [str(p) for p in paths if p.has_wildcard]
        if wild:
            wild_str = "\n\t".join(wild)
            raise WildcardError(
                f"{cls.__name__} cannot be created with wildcard paths:\n\t{wild_str}"
            )
        return cls(paths=paths, src=src)

    def resolve_wildcard(self, path: DatasetPath) -> DatasetPathCollection:
        return super(Catalog, self).resolve_wildcard(path)

    def find(self, path: DatasetPath) -> DatasetPathCollection:
        return self.resolve_wildcard(path)
