import logging
from dataclasses import dataclass, fields
from re import compile
from typing import Any, Self

from ..errors import DatasetPathParseError
from .wildcard import WILDCARD_PATTERN_LITERAL, WILDCARD_STR


@dataclass(
    frozen=True,
    slots=True,
    order=True,
    eq=True,
)
class DatasetPath:
    """Representation of a single DSS dataset path, made of five parts, A-F."""

    a: str = WILDCARD_STR
    b: str = WILDCARD_STR
    c: str = WILDCARD_STR
    d: str = WILDCARD_STR
    e: str = WILDCARD_STR
    f: str = WILDCARD_STR

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
        if len(args) != len(cls.__annotations__):
            raise DatasetPathParseError(
                "not enough path parts given:\n"
                + f"\t{path=}\n"
                + f"\tparsed to:{args}"
            )
        for bad_wild in ("", *WILDCARD_STR):
            args = tuple(val if val != bad_wild else WILDCARD_STR for val in args)

        return cls(*args)

    def drop_date(self) -> Self:
        """Remove the D part of the path, and return a new DatasetPath object

        Returns
        -------
        DatasetPath
            The new object
        """
        kwargs = {k: v for k, v in self.items() if k != "d"}
        kwargs["d"] = WILDCARD_STR
        return self.__class__(**kwargs)

    def matches(self, __other: Self | str) -> bool:
        """Determine whether or not two DatasetPath objects match against each
        other. Matching is not the same as equality. Paths with wildcards will only
        match each other if they have the same string representation. Matching is
        transative. For example:

            /A/B/C/D/E/F/ matches /A/B/C/D/E/F/, and they are equal
            /A/B/C/.*/E/F/  matches /A/B/C/.*/E/F/, and they are equal
            /A/B/C/.*/E/F/ matches /A/B/C/D/E/F/, but they are not equal
            /A/B/C/.*/E/F/ does not match /.*/B/C/D/E/F/, and they are not equal

        Parameters
        ----------
        __other : Self | str
            The other object to match against.

        Returns
        -------
        bool
            Whether or not the two paths match.
        """
        # If __other is a str, just do equality
        logging.debug(f"matching {self} <-> {__other}")
        if isinstance(__other, str):
            logging.debug("reverting to equality")
            return self == __other
        # Lets do some duck-typing
        try:
            if (not self.has_any_wildcard) and (not __other.has_any_wildcard):
                # If there are no wildcards, just look for equality
                return self == __other
            # For each attr, check for equality, or regex matching
            L_to_R = False
            R_to_L = False
            for f in fields(self):
                L = getattr(self, f.name)
                R = getattr(__other, f.name)
                if L == R:
                    pass
                elif compile(L).findall(R):
                    L_to_R = True
                elif compile(R).findall(L):
                    R_to_L = True
                else:
                    # One of the above should catch if the objects match
                    logging.debug(f"nagative match on part {f.name}, {L}<->{R}")
                    return False
            # Make sure we are only matching in one direction
            if L_to_R and R_to_L:
                logging.debug("nagative match on multi-direction matching")
                return False

        except Exception:
            # fall back to equality
            logging.debug("match gave an error, reverting to equality")
            return self == __other
        # All other check passed
        logging.debug("positive match")
        return True

    def __eq__(self, __other: Any):
        """Determine whether or not two DatasetPath objects equal each other. Equalit is
        not the same as matching. Paths with wildcards will only equal each other if
        they have the same fields exactly. Equality is transative. For example:

            /A/B/C/D/E/F/ matches /A/B/C/D/E/F/, and they are equal
            /A/B/C/.*/E/F/  matches /A/B/C/.*/E/F/, and they are equal
            /A/B/C/.*/E/F/ matches /A/B/C/D/E/F/, but they are not equal
            /A/B/C/.*/E/F/ does not match /.*/B/C/D/E/F/, and they are not equal

        Parameters
        ----------
        __other : Self | str
            The other object to check for equality against.

        Returns
        -------
        bool
            Whether or not the two paths are equal.
        """
        if isinstance(__other, self.__class__):
            # Compare on all fields
            try:
                return all(
                    getattr(self, f.name) == getattr(__other, f.name)
                    for f in fields(self)
                )
            except AttributeError:
                return False
        elif isinstance(__other, str):
            # First clean up, then do str comparison
            return str(self) == str(self.__class__.from_str(__other))
        else:
            # Resort to regular string comparison
            return str(self) == str(__other)

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
        return bool(WILDCARD_PATTERN_LITERAL.findall(s))

    @property
    def has_any_wildcard(self) -> dict[str, bool]:
        """Whether or not the path as a wildcard, including D-part wildcards."""
        return bool(WILDCARD_PATTERN_LITERAL.findall(str(self)))

    @property
    def wildcard_parts(self) -> set[str]:
        parts = set()
        for f, v in self.items():
            if WILDCARD_PATTERN_LITERAL.findall(v):
                parts.add(f)
        return parts
