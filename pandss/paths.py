import logging
from dataclasses import dataclass, field, fields
from re import compile
from typing import Iterator, Self
from warnings import warn

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
        if path.startswith("/"):
            path = path[1:]
        if path.endswith("/"):
            path = path[:-1]
        a, b, c, d, e, f = path.split("/")
        if "" in (a, b, c, e, f):
            warn(
                "wildcards must follow python regex patterns, empty parts (eg //) will not match anything, use '/.*/' instead",
                Warning,
            )
        return cls(a=a, b=b, c=c, d=d, e=e, f=f)

    def __str__(self):
        kwargs = {f.name: getattr(self, f.name) for f in fields(self)}
        s = "/{a}/{b}/{c}/{d}/{e}/{f}/".format(**kwargs)

        return s

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
        return bool(WILDCARD_PATTERN.findall(str(self)))

    def drop_date(self) -> Self:
        kwargs = {k: v for k, v in self.items() if k != "d"}
        kwargs["d"] = ""
        return DatasetPath(**kwargs)


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

    def findall(self, path: DatasetPath) -> Self:
        logging.info(f"finding paths that match {path}")
        regex = compile(str(path))
        logging.debug(f"{regex=}")
        buffer = "\n".join(str(p) for p in self.paths)
        matched = regex.findall(buffer)
        matched = [item.lstrip("/").rstrip("/") for item in matched]
        logging.debug(f"matched {len(matched)} paths")
        return DatasetPathCollection(
            paths=set(DatasetPath(*p.split("/")) for p in matched)
        )

    def drop_date(self) -> Self:
        new_paths = {p.drop_date() for p in self.paths}
        return DatasetPathCollection(paths=new_paths)
