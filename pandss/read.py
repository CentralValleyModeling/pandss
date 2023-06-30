from pathlib import Path
from typing import Union, Iterable
import logging

import pandas as pd
import pyhecdss

from .paths import PathLike, use_temp_paths

CONTEXT_ATTR = (
    'PATH',
    'UNITS',
    'PERIOD_TYPE'
)

@use_temp_paths
def read_catalog(
        dss: PathLike,
        query_expr: Union[str, None] = None,
    ) -> pd.DataFrame:
    """Read the catalog from one or many DSS files. Optionally filter the 
    catalog using pandas.DataFrame.query using the query_expr.

    Parameters
    ----------
    dss : Union[PathLike, Iterable[PathLike]]
        The path or paths to the DSS file(s).
    query_expr : Union[str, None], optional
        A query expression to be passed to pandas.DataFrame.query, by default None

    Returns
    -------
    pd.DataFrame
        A list of, or single pandas.DataFrame catalogs.
    """
    logging.info(f"reading catalog from {dss}")
    with pyhecdss.DSSFile(str(p)) as P:
        catalog = P.read_catalog()
        
    logging.info(f'query_expr is {query_expr}')
    if query_expr is not None:
        catalog = catalog.query(query_expr)
    
    logging.info('catalogs successfully read')
    return catalog

@use_temp_paths
def read_dss(
        dss: PathLike, 
        paths: Union[Iterable[str], pd.DataFrame], 
        add_context: Union[bool, Iterable[str]] = False
    ) -> pd.DataFrame:
    """Create a DataFrame ledger from a set of Timeseries in a DSS file. 

    The timeseries will be concatenated vertically. Columns for the DSS path, 
    the timeseries units, and the indexing period type can be added with the 
    optional `add_context

    Parameters
    ----------
    dss : Union[Path, str]
        The filepath of the DSS file.
    paths : Union[Iterable[str], pd.DataFrame]
        A list of DSS A-F paths to be read, or a catalog DataFrame.
    add_context : Union[bool, Iterable[str]]
        An iterable like ['PATH', 'UNITS', 'PERIOD_TYPE'], or a subset of these, by default False

    Returns
    -------
    pd.DataFrame
        A long-list DataFrame of the timeseries
    """
    logging.info(f'reading timeseries from {dss}')
    if add_context is True:  # Add all
        add_context = CONTEXT_ATTR
    elif add_context is False:  # Add none
        add_context = tuple()
    else:  # Make sure they are all recognizable
        add_context = [i.upper() for i in add_context]
        assert all([i for i in add_context in CONTEXT_ATTR])     
    logging.info(f'{add_context=}')
    with pyhecdss.DSSFile(str(dss)) as DSS:
        if isinstance(paths, pd.DataFrame):  # Resolve the catalog to pathnames
            paths = DSS.get_pathnames(paths)
        logging.info(f'reading {len(paths)} paths')
        frames = list()
        for p in paths:
            ts = DSS.read_rts(p)
            df_individual = ts.data  # type: pd.DataFrame
            df_individual = df_individual.rename(columns={p: 'VALUE'})
            if 'PATH' in add_context:
                df_individual['PATH'] = p
            if 'UNITS' in add_context:
                df_individual['UNITS'] = ts.units
            if 'PERIOD_TYPE' in add_context:
                df_individual['PERIOD_TYPE'] = ts.period_type

            frames.append(df_individual)
    logging.info('concatenating data')
    df = pd.concat(frames, axis=0)
    df.index.name = 'PERIOD'
    logging.info(f'{len(df)} records read')

    return df
