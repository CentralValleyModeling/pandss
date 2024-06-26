import logging
from dataclasses import dataclass, field, fields
from re import IGNORECASE, compile
from typing import Iterable, Iterator, Self
from warnings import warn

from .errors import DatasetPathParseError

WILDCARD_PATTERN = compile(r"\.\*")


def enforce_similar_type(func):
    """Decorator for ensuring that binary operators are acting on objects of
    the same class inheritance.

    Used on many methods in DatasetPathCollection.

    Raises
    ------
    TypeError
        Error raised if the objects are not of the same class.
    """

    def enforce_similar_type_inner(obj, __other):
        if not isinstance(__other, type(obj)):
            raise TypeError(f"cannot {func.__name__} {type(obj)} with {type(__other)}")
        return func(obj, __other)

    return enforce_similar_type_inner


@dataclass(
    frozen=True,
    slots=True,
    eq=True,
    order=True,
)
class DatasetPath:
    """Representation of a single DSS dataset path, made of five parts, A-F."""

    a: str = ".*"
    b: str = ".*"
    c: str = ".*"
    d: str = ".*"
    e: str = ".*"
    f: str = ".*"

    @classmethod
    def from_str(cls, path: str) -> Self:
        """Create a DatasetPath from a string.

        Parameters
        ----------
        path : str
            The string representation of the path

        Returns
        -------
        DatasetPath
            The DatasetPath object

        Raises
        ------
        DatasetPathParseError
            Raised if the string cannot be parsed
        """
        try:
            path = path.strip("/")
            args = path.split("/")
        except Exception as e:
            raise DatasetPathParseError(f"couldn't parse {path} as path") from e
        for bad_wild in ("", "*"):
            args = tuple(val if val != bad_wild else ".*" for val in args)
        if len(args) != len(cls.__annotations__):
            raise DatasetPathParseError(
                "not enough path parts given:\n"
                + f"\t{path=}\n"
                + f"\tparsed to:{args}"
            )

        return cls(*args)

    def drop_date(self) -> Self:
        """Remove the D part of the path, and return a new DatasetPath object

        Returns
        -------
        DatasetPath
            The new object
        """
        kwargs = {k: v for k, v in self.items() if k != "d"}
        kwargs["d"] = ".*"
        return self.__class__(**kwargs)

    def __str__(self):
        return f"/{self.a}/{self.b}/{self.c}/{self.d}/{self.e}/{self.f}/"

    def __dict__(self) -> dict[str, str]:
        return dict(self.items())

    def __iter__(self):
        for f in fields(self):
            yield getattr(self, f.name)

    def items(self):
        for f in fields(self):
            yield f.name, getattr(self, f.name)

    @property
    def has_wildcard(self) -> bool:
        """Whether or not the path as a wildcard, ignoring D-part wildcards."""
        s = f"/{self.a}/{self.b}/{self.c}//{self.e}/{self.f}/"
        return bool(WILDCARD_PATTERN.findall(s))

    @property
    def has_any_wildcard(self) -> dict[str, bool]:
        """Whether or not the path as a wildcard, including D-part wildcards."""
        return bool(WILDCARD_PATTERN.findall(str(self)))


@dataclass(
    kw_only=True,
    frozen=True,
    slots=True,
    eq=True,
)
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
                + " seen types: {bad_types}"
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

    @enforce_similar_type
    def __add__(self, __other: Self) -> Self:
        """Alias for self.__and__"""
        return self.__and__(__other)

    @enforce_similar_type
    def __sub__(self, __other: Self) -> Self:
        """Set-style __sub__ of the collections"""
        new = self.paths.__sub__(__other.paths)
        return DatasetPathCollection(paths=new)

    @enforce_similar_type
    def __and__(self, __other: Self) -> Self:
        new = self.paths.__and__(__other.paths)
        return DatasetPathCollection(paths=new)

    @enforce_similar_type
    def __or__(self, __other: Self) -> Self:
        new = self.paths.__or__(__other.paths)
        return DatasetPathCollection(paths=new)

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
