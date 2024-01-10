import logging
from dataclasses import dataclass, field, fields
from re import IGNORECASE, compile
from typing import Iterator, Self
from warnings import warn

from .errors import DatasetPathParseError

WILDCARD_PATTERN = compile(r"\.\*")


def enforce_similar_type(method):
    def enforce_similar_type_inner(obj, __other):
        if not isinstance(__other, type(obj)):
            raise ValueError(
                f"cannot {method.__name__} {type(obj)} with {type(__other)}"
            )
        return method(obj, __other)

    return enforce_similar_type_inner


@dataclass(
    frozen=True,
    slots=True,
)
class DatasetPath:
    a: str
    b: str
    c: str
    d: str
    e: str
    f: str

    @classmethod
    def from_str(cls, path: str) -> Self:
        try:
            _, *args, _ = path.split("/")
        except Exception as e:
            raise DatasetPathParseError(f"couldn't parse {path} as path") from e
        for bad_wild in ("", "*"):
            args = tuple(val if val != bad_wild else ".*" for val in args)

        return cls(*args)

    def drop_date(self) -> Self:
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
        """Bool, does not check D-Part"""
        s = f"/{self.a}/{self.b}/{self.c}//{self.e}/{self.f}/"
        return bool(WILDCARD_PATTERN.findall(s))

    @property
    def has_any_wildcard(self) -> dict[str, bool]:
        """Bool, includes D-part"""
        return bool(WILDCARD_PATTERN.findall(str(self)))


@dataclass(
    kw_only=True,
    frozen=True,
    slots=True,
    eq=True,
)
class DatasetPathCollection:
    paths: set[DatasetPath] = field(default_factory=set)

    def __post_init__(self):
        if not isinstance(self.paths, set):
            raise ValueError("paths must be given as a set of pdss.DatasetPath")
        bad_types = list()
        for obj in self.paths:
            if not isinstance(obj, DatasetPath):
                bad_types.append(obj)
        if bad_types:
            n = len(bad_types)
            bad_types = set([type(obj) for obj in bad_types])
            raise ValueError(
                f"paths must be given as `{DatasetPath.__name__}` objects, {n} bad items given, seen types: {bad_types}"
            )

    def __iter__(self) -> Iterator[DatasetPath]:
        yield from self.paths

    def __len__(self) -> int:
        return len(self.paths)

    @enforce_similar_type
    def __add__(self, __other: Self) -> Self:
        return self.__and__(__other)

    @enforce_similar_type
    def __sub__(self, __other: Self) -> Self:
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
        return self.paths & __other

    def union(self, __other: Self) -> Self:
        return self.paths & __other

    def difference(self, __other: Self) -> Self:
        return self.paths - __other

    @classmethod
    def from_strs(cls, paths: list[str]) -> Self:
        return cls(paths=set(DatasetPath.from_str(p) for p in paths))

    def resolve_wildcard(self, path: DatasetPath) -> Self:
        logging.info(f"finding paths that match {path}")
        if any(p.has_any_wildcard for p in self.paths):
            warn(
                f"paths in {self.__class__.__name__} have wildcards, these may not match pattern provided!",
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
        logging.info("collapsing dates")
        # get the kwargs needed to re-build the class
        kwargs = {f.name: getattr(self, f.name) for f in fields(self)}
        # set construction removes duplicates automatically, so drop the dates
        # in each of the paths in the current object
        kwargs["paths"] = {p.drop_date() for p in self.paths}
        return self.__class__(**kwargs)  # Maintain subclasses by calling __class__
