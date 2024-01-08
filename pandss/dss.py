import logging
from pathlib import Path
from typing import Iterator

from .catalog import Catalog
from .paths import DatasetPath, DatasetPathCollection
from .quiet import silent, suppress_stdout_stderr
from .timeseries import RegularTimeseries
from .engines import get_engine, EngineABC


def must_be_open(method):
    def works_on_open_file(obj, *args, **kwargs):
        if obj.is_open is False:
            raise IOError(f"file must be open to call {method}")
        else:
            return method(obj, *args, **kwargs)

    return works_on_open_file


class DSS:
    """Class representing an open DSS file. Binds to various other python based
    HEC-DSS file readers through an "engine". The Engine classes wrap the other
    libraries, creating one API that this class uses.
    """

    __slots__ = ["src", "engine"]

    def __init__(self, src: str | Path, engine: str | EngineABC = "pydsstools"):
        self.src: Path = Path(src).resolve()
        if isinstance(engine, str):
            engine = get_engine(engine)
        elif not isinstance(engine, EngineABC):
            raise ValueError(f"engine type not recognized: {type(engine)=}")
        logging.info(f"using engine {engine}")
        self.engine = engine(self.src)

    @silent
    def __enter__(self):
        """Wraps Engine class `open` and enables the use of engine classes in
        pythons context manager pattern.

        with DSS(path_to_dss_file) as DSS_File:
            # read/write data in DSS file
            ...
        # Engine.close() automatically called.


        Returns
        -------
        self
            Returns a DSS object.

        Raises
        ------
        RuntimeError
            Generic error for error opening DSS file
        """
        if not self.src.exists():
            raise FileNotFoundError(self.src)
        logging.info(f"opening dss file {self.src}")
        self.engine.open()
        return self

    @silent
    def __exit__(self, exc_type, exc_inst, traceback):
        """Wraps Engine `close()` and enables the use of this class
        in pythons context manager pattern.
        """
        logging.info(f"closing dss file {self.src}")
        self.engine.close()

    @must_be_open
    def read_catalog(self) -> Catalog:
        logging.info(f"reading catalog, {self.src=}")
        with suppress_stdout_stderr():
            catalog = self.engine.read_catalog()
        logging.info(f"catalog read, size is {len(catalog)}")
        return catalog

    @must_be_open
    def read_rts(self, path: DatasetPath) -> RegularTimeseries:
        logging.info(f"reading regular time series, {path}")
        if path.has_wildcard:
            raise ValueError("path has wildcard, use `read_multiple_rts` method")
        with suppress_stdout_stderr():
            return self.engine.read_rts(path)

    @must_be_open
    def read_multiple_rts(
        self,
        paths: DatasetPath | DatasetPathCollection,
        drop_date: bool = True,
    ) -> Iterator[RegularTimeseries]:
        if hasattr(self.engine, "read_multiple_rts") and callable(
            self.engine.read_multiple_rts
        ):
            yield from self.engine.read_multiple_rts(paths, drop_date)
        else:  # If the engine doesn't optimize this, we can just iterate one at a time
            # If passed a single path, check for wildcard that might expand it
            if isinstance(paths, DatasetPath):
                if paths.has_wildcard:
                    paths = self.resolve_wildcard(paths)
                else:
                    logging.debug(
                        "`read_multiple_rts` called with only one path with no wildcards"
                    )
                    paths = DatasetPathCollection(paths={paths})
            else:
                # If passed multple paths, expand any of them with wildcards
                if any(p.has_wildcard for p in paths):
                    for p in paths:
                        paths = paths & self.resolve_wildcard(p)
            # When expanding wildcards, paths might be specific to a single chunk,
            # use the special method here to re-combine the paths (combine D-parts)
            if drop_date is True:
                paths = paths.drop_date()
            # Read each individually
            for p in paths:
                yield self.read_rts(p)

    @must_be_open
    def resolve_wildcard(self, path: DatasetPath) -> DatasetPathCollection:
        logging.info("resolving wildcards")
        if not path.has_wildcard:
            return DatasetPathCollection(paths={path})
        if self.engine.catalog is None:
            self.engine.read_catalog()
        return self.engine.catalog.findall(path)

    @property
    def is_open(self):
        return self.engine.is_open

    @property
    def catalog(self) -> Catalog:
        return self.engine.catalog
