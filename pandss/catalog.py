from pathlib import Path
from typing import Union, Optional, Iterator
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
        right: Union[PathLike, DataFrame],
        compare_on: Optional[list] = None
    ) -> tuple[DataFrame, DataFrame]:
    """Extract the common catalog from two DSS files. Allows for comparisons 
    on custom collections of columns. Only can compare two catalogs.

    Parameters
    ----------
    left : Union[PathLike, DataFrame]
        The left DSS file, or catalog DataFrame
    right : Union[PathLike, DataFrame]
        The right DSS file, or catalog DataFrame
    compare_on : Optional[list], optional
        The list of A-F, T to compare on, by default None

    Returns
    -------
    tuple[DataFrame, DataFrame]
        The two intersecting catalogs, for the left and right
    """
    # Allow for paths instead
    if isinstance(left, (Path, str)):
        left = read_catalog(left)
    if isinstance(right, (Path, str)):
        right = read_catalog(right)
    if compare_on is None:
        compare_on = ALL_CATALOG_COLUMNS
    # Track the order of the columns passed
    left_og_order = left.columns
    right_og_order = right.columns

    left = left.set_index(compare_on)
    right = right.set_index(compare_on)
    index_common = left.index.intersection(right.index)
    left = left.loc[index_common].reset_index()
    right = right.loc[index_common].reset_index()

    return left[left_og_order], right[right_og_order] 

def iter_common_catalog(
        left: Union[PathLike, DataFrame], 
        right: Union[PathLike, DataFrame], 
        groupby: str,
        compare_on: Optional[list] = None, 
    ) -> Iterator[tuple[str, DataFrame, DataFrame]]:
    """Iterate over two catalogs, only returning sections of the catalog that 
    are common between two DSS files. The sections are grouped by the argument
    groupby.

    Parameters
    ----------
    left : Union[PathLike, DataFrame]
        The left DSS file, or DataFrame catalog.
    right : Union[PathLike, DataFrame]
        The right DSS file, or DataFrame catalog.
    groupby : str
        The argument passed to pandas.DataFrame.groupby for each catalog    
    compare_on : Optional[list], optional
        Passed to pandss.catalog.common_catalog, by default None

    Yields
    ------
    Iterator[tuple[str, DataFrame, DataFrame]]
        An iterator that yields a tuple of the groupby index, and each section
    """
    cat_base, cat_alt = common_catalog(left, right, compare_on=compare_on)
    g_L = cat_base.groupby(groupby)
    g_R = cat_alt.groupby(groupby)
    for (c, df_L), (_, df_R) in zip(g_L, g_R):
        yield c, df_L, df_R
