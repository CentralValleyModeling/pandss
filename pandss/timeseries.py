from typing import Union, Iterable
import logging
from pathlib import Path

import pandas as pd
import pyhecdss

from .paths import PathLike
from .catalog import read_catalog

CONTEXT_ATTR = (
    'PATH',
    'UNITS',
    'PERIOD_TYPE'
)

E_PARTS = (
    '1YEAR',
    '1MONTH', 'SEMI-MONTH', 'TRI-MONTH',
    '1WEEK',
    '1DAY',
    '12HOUR', '8HOUR', '6HOUR', '4HOUR', '3HOUR', '2HOUR', '1HOUR',
    '30MINUTE', '20MINUTE', '15MINUTE', '10MINUTE', '6MINUTE', '5MINUTE', '4MINUTE', '3MINUTE', '2MINUTE', '1MINUTE',
    '30SECOND', '20SECOND', '15SECOND', '10SECOND', '6SECOND', '5SECOND', '4SECOND', '3SECOND', '2SECOND', '1SECOND',
)

PERIOD_TYPES = (
    'INST-VAL',
    'INST-CUM',
    'PER-AVER',
    'PER-CUM',
)

def read_dss(
        dss: PathLike, 
        paths: Union[Iterable[str], pd.DataFrame], 
        add_context: Union[bool, Iterable[str]] = True,
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
        An iterable like ['PATH', 'UNITS', 'PERIOD_TYPE'], or a subset of these, by default True

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
    if len(frames) == 0:
        raise ValueError("No timeseries found, check paths requested.")
    elif len(frames) > 1:
        logging.info('concatenating data')
        df = pd.concat(frames, axis=0)
    else:
        df = frames[0]
    df.index.name = 'PERIOD'
    logging.info(f'{len(df)} records read')

    return df

def write_dss(dst: PathLike, df: pd.DataFrame):
    """Create a DSS file from a pandas DataFrame. Creates a regular timeseries
    dataset in the output dataset.

    Parameters
    ----------
    dst : PathLike
        The location of the DSS file to be created.
    data : pd.DataFrame
        The dataframe to convert to the DSS file. Must contain columns for 
        A-F parts, UNITS, PERIOD_TYPE, PERIOD, and VALUES.

    """
    # Validate the dataframe
    df.columns = [c.upper() for c in df.columns]
    missing = list()
    if 'PERIOD' not in df.columns:
        if df.index.name.upper() != 'PERIOD':
            missing.append('PERIOD')
    else:
        df = df.set_index('PERIOD')
    # Ensure paths are usable
    if 'PATH' not in df.columns:
        missing.extend([c for c in ['A', 'B', 'C', 'E', 'F'] if c not in df.columns]) 
    # Ensure simple required columns are gven
    for req in ['UNITS', 'PERIOD-TYPE', 'VALUE']:
        if req not in df.columns:
            missing.append(req)
    # Raise
    if missing:
        raise ValueError(f"Missing the following columns:\n{missing}\ngiven: {df.columns}")
    # Validate E parts
    if 'E' in df.columns:
        bad_e = [e for e in df['E'].unique() if e not in E_PARTS]
        if bad_e:
            raise ValueError(f"E-part not recognized:\ngiven: {bad_e}\naccepted: {E_PARTS}")
    # Now that we know none of the columns are missing, make a PATH column
    if 'PATH' not in df.columns:
        df['PATH'] = '/' \
            + df[['A', 'B', 'C']].agg('-'.join, axis=1) \
            + '//' \
            + df[['E', 'F']].agg('-'.join, axis=1) \
            + '/'
    # Validate PERIOD-TYPE
    bad_pt = [pt for pt in df['PERIOD-TYPE'].unique() if pt not in PERIOD_TYPES]
    if bad_pt:
        raise ValueError(f"Period type not recognized:\ngiven: {bad_pt}\naccepted: {PERIOD_TYPES}")
    
    # Validate the destination location
    dst = Path(dst).resolve()
    if dst.exists():
        raise ValueError(f"dst already exists!\n{dst}")

    # Do the dang thing
    with pyhecdss.DSSFile(str(dst), create_new=True) as DST:
        for path, ts in df.groupby('PATH'):
            ts = ts.copy()
            units = ts['UNITS'].unique()
            period_type = ts['PERIOD-TYPE'].unique()
            if len(units) != 1:
                raise ValueError(f"Path {path} contains non-unique units: {units}")
            if len(period_type) != 1:
                raise ValueError(f"Path {path} contains non-unique period-type: {period_type}")
            data = ts['VALUE']
            # Validate frequency on index
            if data.index.freq is None:
                freq = pd.infer_freq(ts.index)
                if freq is None:
                    raise ValueError(f"Cannot determine frequency from index for {path=}")
                data.index.freq = pd.tseries.frequencies.to_offset(freq)
            DST.write_rts(
                pathname=path, 
                df=data, 
                cunits=units[0], 
                ctype=period_type[0])


@pd.api.extensions.register_dataframe_accessor('dss')
class PandssAccessor:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    def write(self, dst: PathLike):
        write_dss(dst, self._df)

    def read(self, src: PathLike):
        return read_dss(src, self._df)
