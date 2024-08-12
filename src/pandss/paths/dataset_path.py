from dataclasses import dataclass, fields
from typing import Self

from ..errors import DatasetPathParseError
from .wildcard import WILDCARD_PATTERN


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
