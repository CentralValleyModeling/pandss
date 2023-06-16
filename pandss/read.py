from pathlib import Path
from typing import Union, Iterable

import pandas as pd
import pyhecdss


CONTEXT_ATTR = (
    'PATH',
    'UNITS',
    'PERIOD_TYPE'
)


def read_dss(
        dss: Union[Path, str], 
        paths: Union[Iterable[str], pd.DataFrame], 
        add_context: Union[bool, Iterable[str]]
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
        An iterable like ['PATH', 'UNITS', 'PERIOD_TYPE'], or a subset of these.

    Returns
    -------
    pd.DataFrame
        A long-list DataFrame of the timeseries
    """    
    if add_context is True:  # Add all
        add_context = CONTEXT_ATTR
    elif add_context is False:  # Add none
        add_context = tuple()
    else:  # Make sure they are all recognizable
        add_context = [i.upper() for i in add_context]
        assert all([i for i in add_context in CONTEXT_ATTR])     

    with pyhecdss.DSSFile(str(dss)) as DSS:
        if isinstance(paths, pd.DataFrame):  # Resolve the catalog to pathnames
            paths = DSS.get_pathnames(paths)

        frames = list()
        for p in paths:
            ts = DSS.read_rts(p)
            df_individual = ts.data  # type: pd.DataFrame
            df_individual = df_individual.rename(columns={p: 'VALUE'})
            df_individual['PATH'] = p
            df_individual['UNITS'] = ts.units
            df_individual['PERIOD_TYPE'] = ts.period_type

            frames.append(df_individual)
        df = pd.concat(frames, axis=0)
        df.index.name = 'PERIOD'

        return df