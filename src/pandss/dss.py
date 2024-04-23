import logging
from pathlib import Path
from typing import Iterator

from .catalog import Catalog
from .engines import EngineABC, ModuleEngine, get_engine
from .errors import UnexpectedDSSReturn, WildcardError
from .paths import DatasetPath, DatasetPathCollection
from .quiet import silent, suppress_stdout_stderr
from .timeseries import RegularTimeseries

module_engine = ModuleEngine()


class DSS:
    """Class representing an open DSS file. Binds to various other python based
    HEC-DSS file readers through an "engine". The Engine classes wrap the other
    libraries, creating one API that this class uses.

    Parameters
    ----------
    src: pathlib.Path
        The path to the DSS file on disk.
    engine: str | EngineABC, default "pyhecdss"
        The engine object that handles the DSS interactions. Available engines:
            - pyhecdss
            - pydsstools

    See Also
    --------
    DSS.read_catalog: Read the DSS and return a pandss.Catalog object
    DSS.reaf_rts: Read a single regular timeseries from the DSS and return a
        pandss.RegularTimeseries object.
    DSS.read_multiple_rts: Read multiple regular timeseries from the DSS and
        return a iterator of pandss.RegularTimeseries objects.
    DSS.write_rts: Write a pandss.RegularTimeseries object to a DSS file.
    """

    __slots__ = ["src", "engine", "_opened"]

    def __init__(self, src: str | Path, engine: str | EngineABC = None):
        if engine is None:
            engine = module_engine.selected
        self.src: Path = Path(src).resolve()
        if isinstance(engine, str):
            engine = get_engine(engine)
        elif not isinstance(engine, EngineABC):
            raise ValueError(f"engine type not recognized: {type(engine)=}")
        logging.debug(f"using engine {engine}")
        self.engine: EngineABC = engine(self.src)
        self._opened = 0

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.src})"

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
        """
        if self._opened <= 0:
            logging.debug(f"opening dss file {self.src}")
            self.engine.open()
        self._opened += 1
        return self

    @silent
    def __exit__(self, exc_type, exc_inst, traceback):
        """Wraps Engine `close()` and enables the use of this class
        in pythons context manager pattern.
        """
        self._opened += -1
        if self._opened <= 0:
            logging.debug(f"closing dss file {self.src}")
            self.engine.close()
            self._opened = 0

    def read_catalog(self, drop_date: bool = False) -> Catalog:
        logging.debug(f"reading catalog, {self.src=}")
        with suppress_stdout_stderr():
            catalog = self.engine.read_catalog()
        if drop_date:
            catalog = catalog.collapse_dates()
        logging.debug(f"catalog read, size is {len(catalog)}")
        return catalog

    def read_rts(
        self,
        path: DatasetPath | str,
        expect_single: bool = True,
        drop_date: bool = True,
    ) -> RegularTimeseries:
        logging.debug(f"reading regular time series, {path}")
        if isinstance(path, str):
            path = DatasetPath.from_str(path)
        if path.has_wildcard:
            if expect_single:
                rtss = tuple(self.read_multiple_rts(path, drop_date))
                if len(rtss) != 1:
                    raise UnexpectedDSSReturn(
                        f"expected {path} to resolve to single path, "
                        + f"DSS returned {len(rtss)} items."
                    )
                else:
                    return rtss[0]
            else:
                raise WildcardError(
                    f"path has wildcard, use `read_multiple_rts` method, {path=}"
                )
        with suppress_stdout_stderr():
            return self.engine.read_rts(path)

    def read_multiple_rts(
        self,
        paths: DatasetPath | DatasetPathCollection,
        drop_date: bool = True,
    ) -> Iterator[RegularTimeseries]:
        if hasattr(self.engine, "read_multiple_rts"):
            yield from self.engine.read_multiple_rts(paths, drop_date)
        else:  # If the engine doesn't optimize this, we can just iterate one at a time
            # If passed a single path, check for wildcard that might expand it
            if isinstance(paths, DatasetPath):
                if paths.has_wildcard:
                    paths = self.resolve_wildcard(paths)
                else:
                    logging.debug(
                        "`read_multiple_rts` called with only one path,"
                        + " path contains no wildcards to expand"
                    )
                    paths = DatasetPathCollection(paths={paths})
            elif isinstance(paths, DatasetPathCollection):
                # If passed multple paths, expand any of them with wildcards
                if any(p.has_wildcard for p in paths):
                    for p in paths:
                        paths = paths & self.resolve_wildcard(p)
            else:
                raise ValueError(
                    "paths must be given as DatasetPath or DatasetPathCollection"
                    + " so wildcards can be correctly resolved"
                )
            # When expanding wildcards, paths might be specific to a single chunk,
            # use the special method here to re-combine the paths (combine D-parts)
            if drop_date is True:
                paths = paths.collapse_dates()
            # Read each individually
            for p in paths:
                yield self.read_rts(p)

    def write_rts(self, path: DatasetPath | str, rts: RegularTimeseries):
        if isinstance(path, str):
            path = DatasetPath.from_str(path)
        logging.debug(f"writing regular time series, {path}")
        if path.has_wildcard:
            raise WildcardError(f"cannot write to path with non-date wildcard, {path=}")
        with suppress_stdout_stderr():
            return self.engine.write_rts(path, rts)

    def resolve_wildcard(
        self,
        path: DatasetPath | str,
        drop_date: bool = False,
    ) -> DatasetPathCollection:
        if isinstance(path, str):
            path = DatasetPath.from_str(path)
        logging.debug("resolving wildcards")
        if not path.has_wildcard:
            return DatasetPathCollection(paths={path})
        if self.engine.catalog is None:
            self.engine.read_catalog()
        collection = self.engine.catalog.resolve_wildcard(path)
        if drop_date:
            collection = collection.collapse_dates()
        return collection

    @property
    def is_open(self):
        return self.engine.is_open

    @property
    def catalog(self) -> Catalog:
        return self.engine.catalog
