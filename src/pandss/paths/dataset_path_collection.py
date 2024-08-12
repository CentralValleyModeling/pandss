import logging
from dataclasses import dataclass, field, fields
from re import IGNORECASE, compile
from typing import Any, Iterable, Iterator, Self
from warnings import warn

from .dataset_path import DatasetPath


@dataclass(kw_only=True, frozen=True, slots=True, order=True)
class DatasetPathCollection:
    """Representation of multiple pandss.DatasetPath objects. Acts similarly to
    and ordered set of DatasetPath objects.
    """

    paths: set[DatasetPath] = field(default_factory=set)

    def __post_init__(self):
        if not isinstance(self.paths, set):
            raise ValueError("paths must be given as a set of pdss.DatasetPath")
        bad_types = list()
        for obj in self.paths:
            if not isinstance(obj, DatasetPath):
                bad_types.append(obj)
        if bad_types:
            bad_types = set([type(obj) for obj in bad_types])
            raise ValueError(
                f"paths must be given as `{DatasetPath.__name__}` objects,"
                + f" {len(bad_types)} bad items given,"
                + f" seen types: {bad_types}"
            )

    def __iter__(self) -> Iterator[DatasetPath]:
        yield from sorted(list(self.paths))

    def __len__(self) -> int:
        """The size of the collection

        Returns
        -------
        int
            The number of paths in the collection
        """
        return len(self.paths)

    def __eq__(self, __other: Any) -> bool:
        if isinstance(__other, self.__class__):
            return self.paths == __other.paths
        return self.paths == set(__other)

    def __add__(self, __other: Any) -> Self:
        return self.__or__(__other)

    def __sub__(self, __other: Any) -> Self:
        new = self.paths.__sub__(set(__other))
        return DatasetPathCollection(paths=new)

    def __and__(self, __other: Any) -> Self:
        new = self.paths.__and__(set(__other))
        return DatasetPathCollection(paths=new)

    def __or__(self, __other: Any) -> Self:
        new = self.paths.__or__(set(__other))
        return DatasetPathCollection(paths=new)

    def __req__(self, __other: Any) -> bool:
        return self.__eq__(__other)

    def __radd__(self, __other: Any) -> Self:
        return self.__add__(__other)

    def __rsub__(self, __other: Any) -> Self:
        return self.__sub__(__other)

    def __rand__(self, __other: Any) -> Self:
        return self.__and__(__other)

    def __ror__(self, __other: Any) -> Self:
        return self.__or__(__other)

    def intersection(self, __other: Self) -> Self:
        """Set style & operation"""
        return self.paths & __other

    def union(self, __other: Self) -> Self:
        """Set style & operation"""
        return self.paths & __other

    def difference(self, __other: Self) -> Self:
        """Set style - operation"""
        return self.paths - __other

    @classmethod
    def from_strs(cls, paths: Iterable[str]) -> Self:
        """Create a DatasetPathCollection from an iterable of strings"""
        return cls(paths=set(DatasetPath.from_str(p) for p in paths))

    def resolve_wildcard(self, path: DatasetPath) -> Self:
        logging.debug(f"finding paths that match {path}")
        if any(p.has_any_wildcard for p in self.paths):
            warn(
                "some paths in the searched collection contain wildcards,"
                + " matching might not return expected results.",
                Warning,
            )
        regex = compile(str(path), flags=IGNORECASE)
        logging.debug(f"{regex=}")
        buffer = "\n".join(str(p) for p in self.paths)
        matched = regex.findall(buffer)
        matched = [item.lstrip("/").rstrip("/") for item in matched]
        logging.debug(f"matched {len(matched)} paths")
        return DatasetPathCollection(
            paths=set(DatasetPath(*p.split("/")) for p in matched)
        )

    def collapse_dates(self) -> Self:
        logging.debug("collapsing dates")
        # get the kwargs needed to re-build the class
        kwargs = {f.name: getattr(self, f.name) for f in fields(self)}
        # set construction removes duplicates automatically, so drop the dates
        # in each of the paths in the current object
        kwargs["paths"] = {p.drop_date() for p in self.paths}
        return self.__class__(**kwargs)  # Maintain subclasses by calling __class__
