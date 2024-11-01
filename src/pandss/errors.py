class WildcardError(Exception):
    """Operation on path with wildcard is invalid."""

    ...


class FileVersionError(Exception):
    """Version of DSS file is invalid for this operation."""

    ...


class DatasetNotFound(Exception):
    """Dataset is not present in the DSS file."""

    ...


class DatasetPathParseError(Exception):
    """DatasetPath could not be constructed from the given information."""

    ...


class ClosedDSSError(Exception):
    """Operation attempted to access a closed DSS file."""

    ...


class UnexpectedDSSReturn(Exception):
    """Operation returned an unexpected result from a DSS read operation."""

    ...


class EmptyCollectionError(Exception):
    """When collecting data from a DSS file, no data was returned."""

    ...
