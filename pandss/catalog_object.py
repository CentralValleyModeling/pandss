from typing import Self

from pandas import DataFrame, Series

from .catalog import read_catalog
from .timeseries import read_dss
from .paths import PathLike

class Catalog(DataFrame):
    """Thin wrapper on a pandas DataFrame that keeps relevant metadata."""
    _metadata = ["source"]
    source: PathLike = None

    def __init__(self, *args, **kwargs) -> None:
        source = kwargs.pop('source', None)
        super().__init__(*args, **kwargs)
        missing_columns = [
            c for c in ['A', 'B', 'C', 'D', 'E']
            if c not in self.columns
        ]
        extra_columns = [
            c for c in self.columns 
            if c not in ['T', 'A', 'B', 'C', 'D', 'E']
        ]
        if missing_columns:
            raise ValueError(missing_columns) 
        if extra_columns:
            raise ValueError(extra_columns)   
        self.source = source

    @classmethod
    def from_dss(cls, source: PathLike) -> Self:
        return Catalog(read_catalog(source), source=source)

    @property
    def _constructor(self):
        return Catalog

    @property
    def _constructor_sliced(self):
        return Series
    
    def get_data(self, add_context: bool = True):
        return read_dss(self.source, self, add_context)