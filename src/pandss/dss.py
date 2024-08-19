import logging
from pathlib import Path
from typing import Iterator, Self

import pandas as pd

from .catalog import Catalog
from .engines import EngineABC, ModuleEngine, get_engine
from .errors import EmptyCollectionError, UnexpectedDSSReturn, WildcardError
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
        pythons context manager pattern. Correspondingly, `DSS.__close__()`
        wraps Engine class `close`.

        ```
        with DSS(path_to_dss_file) as DSS_File:
            # read/write data in DSS file
            cat = DSS_File.read_catalog()
        # Engine.close() automatically called.
        ```

        Returns
        -------
        self
            The open DSS file.
        """
        if self._opened <= 0:
            logging.debug(f"opening dss file {self.src}")
            self.engine.open()
        self._opened += 1
        return self

    @silent
    def __exit__(self, exc_type, exc_inst, traceback):
        self._opened += -1
        if self._opened <= 0:
            logging.debug(f"closing dss file {self.src}")
            self.engine.close()
            self._opened = 0

    @classmethod
    def from_plaintext(cls, src: Path | str) -> Self:
        src = Path(src)
        # make sure dst was specified correctly
        if src.is_file():
            raise ValueError(
                "The source must be specified as a directory, "
                + f"file type {src.suffix} given"
            )
        if not src.exists():
            raise ValueError("src must exist")

        new_file = src.parent / f"{src.stem}.dss"
        if new_file.exists():
            raise ValueError(f"DSS {new_file} already exists")
        new_dss = cls(new_file)
        for f in src.iterdir():
            if f.stem.startswith("rts"):
                df = pd.read_csv(
                    f,
                    header=list(range(0, 9)),
                    index_col=0,
                    parse_dates=True,
                )
                with new_dss:
                    for col in df.columns:
                        path = DatasetPath(
                            a=col[0],
                            b=col[1],
                            c=col[2],
                            d=col[3],
                            e=col[4],
                            f=col[5],
                        )
                        series = df.loc[:, col]
                        idx_s = series.first_valid_index()  # Trim the nan values
                        idx_e = series.last_valid_index()
                        series = series.loc[idx_s:idx_e]
                        rts = RegularTimeseries(
                            path=path,
                            values=series.values,
                            dates=series.index.values,
                            units=col[6],
                            period_type=col[7],
                            interval=col[8],
                        )
                        print(rts.period_type, rts.interval)
                        new_dss.write_rts(rts.path, rts)

        return new_dss

    def to_plaintext(
        self,
        dst: Path | str,
        filter: DatasetPathCollection | DatasetPath | None = None,
    ):
        # make sure dst was specified correctly
        if dst.is_file():
            raise ValueError(
                "The destination must be specified as a empty directory, "
                + f"file type {dst.suffix} given"
            )
        if dst.exists():
            if files := [f for f in dst.iterdir()]:
                raise ValueError(
                    "The destination must be an empty directory, found "
                    + f"{len(files)} files"
                )
        else:
            dst.mkdir(exist_ok=True, parents=False)
        with self:
            # Resolve the different filters
            if isinstance(filter, DatasetPath):
                filter = DatasetPathCollection(paths=set(filter))
            if filter is None:
                filter = self.read_catalog(drop_date=True)

            frames: dict[str, list] = dict()

            for rts in self.read_multiple_rts(filter):
                if rts.interval.e not in frames:
                    frames[rts.interval.e] = list()
                frames[rts.interval.e].append(rts.to_frame())
        if not frames:
            path_list = "\n\t".join(str(p) for p in filter)
            raise EmptyCollectionError(
                f"None of the following paths were found in {self.src}\n\t{path_list}"
            )
        for e, frm in frames.items():
            df = pd.concat(frm, axis=1)
            df.to_csv(dst / f"rts_{e}.csv")

    def read_catalog(self, drop_date: bool = False) -> Catalog:
        """Read the Catalog of the open DSS file.

        The Catalog will contain all the DatasetPath objects present in the DSS
        file.

        Parameters
        ----------
        drop_date : bool, optional
            If True, treat all paths as if they did not have a D part, by default False

        Returns
        -------
        Catalog
            A pandss.Catalog object for the DSS file
        """
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
        """Read a RegularTimeseries from a DSS file.


        Parameters
        ----------
        path : DatasetPath | str
            The A-F path of the data in the DSS, may contain wildcards
        expect_single : bool, optional
            Whether or not to expect a single entry and error on unexpected result, by
            default True
        drop_date : bool, optional
            If True, treat all paths as if they did not have a D part, by default True

        Returns
        -------
        RegularTimeseries
            The RegularTimeseries data stored in the DSS file.

        Raises
        ------
        UnexpectedDSSReturn
            Raised if `expect_single` is True, and multiple paths were matched.
        WildcardError
            Raised if `expect_single` is False, and the path given contains wildcards.
        """
        if isinstance(path, str):
            path = DatasetPath.from_str(path)
        logging.debug(f"reading regular time series, {path}")
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
        paths: DatasetPath | str | DatasetPathCollection,
        drop_date: bool = True,
    ) -> Iterator[RegularTimeseries]:
        """Iteratively read multiple RegularTimeseries.

        Parameters
        ----------
        paths : DatasetPath | str | DatasetPathCollection
            The A-F path of the data in the DSS, may contain wildcards
        drop_date : bool, optional
            If True, treat all paths as if they did not have a D part, by default True

        Yields
        ------
        Iterator[RegularTimeseries]
            An iterator that yields the found RegularTimeseries objects

        Raises
        ------
        ValueError
            Raised if the `paths` argument isn't the correct type.
        """
        if isinstance(paths, str):
            paths = DatasetPath.from_str(paths)
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
                    resolved = set()
                    for p in paths:
                        resolved = resolved | self.resolve_wildcard(p)
                    paths = resolved
            elif hasattr(paths, "__iter__"):
                try:
                    paths = DatasetPathCollection(paths={p for p in paths})
                except Exception:
                    raise ValueError(
                        "paths must be given as DatasetPath or DatasetPathCollection"
                        + " so wildcards can be correctly resolved, "
                        + f"paths given as {type(paths)}"
                    )
            else:
                raise ValueError(
                    "paths must be given as DatasetPath or DatasetPathCollection"
                    + " so wildcards can be correctly resolved, "
                    + f"paths given as {type(paths)}"
                )
            # When expanding wildcards, paths might be specific to a single chunk,
            # use the special method here to re-combine the paths (combine D-parts)
            if drop_date is True:
                paths = paths.collapse_dates()
            # Read each individually
            for p in paths:
                yield self.read_rts(p)

    def write_rts(self, path: DatasetPath | str, rts: RegularTimeseries):
        """Write a RegularTimeseries to a DSS file.

        Parameters
        ----------
        path : DatasetPath | str
            The A-F path to write into the DSS file
        rts : RegularTimeseries
            The RegularTimeseries object containing the data to be written


        Raises
        ------
        WildcardError
            Raised if the `path` argument contains wildcards.
        """
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
        """Search the DSS for DatasetPaths that match the `path` argument.

        Parameters
        ----------
        path : DatasetPath | str
            The path with wildcards to match in the DSS file
        drop_date : bool, optional
            If True, treat paths as if the D part does not exists, by default False

        Returns
        -------
        DatasetPathCollection
            The collection of paths that were matched
        """
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
    def is_open(self) -> bool:
        """Whether or not the DSS is currently open."""
        return self.engine.is_open

    @property
    def catalog(self) -> Catalog:
        """The `Catalog` of the DSS file."""
        return self.engine.catalog
