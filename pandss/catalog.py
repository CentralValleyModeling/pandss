from typing import Union
import logging

from pandas import DataFrame
import pyhecdss

from .paths import PathLike


ALL_CATALOG_COLUMNS = ['T', 'A', 'B', 'C', 'F', 'E', 'D']

def read_catalog(
        dss: PathLike,
        query_expr: Union[str, None] = None,
    ) -> DataFrame:
    """Read the catalog from one or many DSS files. Optionally filter the 
    catalog using pandas.DataFrame.query using the query_expr.

    Parameters
    ----------
    dss : Union[PathLike, Iterable[PathLike]]
        The path or paths to the DSS file(s).
    query_expr : Union[str, None], optional
        A query expression to be passed to pandas.DataFrame.query, by default None
    make_temp : bool, optional
        If true, the DSS file will be copied to a temp file in a local location, by default False

    Returnss
    -------
    pd.DataFrame
        A list of, or single pandas.DataFrame catalogs.
    """ 
    logging.info(f"reading catalog from {dss}")
    with pyhecdss.DSSFile(str(dss)) as DSS:
        catalog = DSS.read_catalog()

    logging.info(f'query_expr is {query_expr}')
    if query_expr is not None:
        catalog = catalog.query(query_expr)
    
    logging.info(f'catalog size is {len(catalog)}')
    return catalog

def common_catalog(
        left: Union[PathLike, DataFrame], 
        right: Union[PathLike, DataFrame]
    ) -> DataFrame:
    if isinstance(left, PathLike):
        left = read_catalog(left)
    if isinstance(right, PathLike):
        right = read_catalog(right)
    left = left.set_index(ALL_CATALOG_COLUMNS)
    right = right.set_index(ALL_CATALOG_COLUMNS)

    index_common = left.index.intersection(right.index)

    return left.loc[index_common].reset_index()
