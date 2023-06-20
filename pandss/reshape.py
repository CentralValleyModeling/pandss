from typing import Union, Iterable

import pandas as pd


PART_NAMES = {
    'A': 'MODEL',
    'B': 'NAME',
    'C': 'TYPE',
    'D': 'DATE',
    'E': 'INTERVAL',
    'F': 'DEVELOPMENT',
}


def split_path(
        df: pd.DataFrame, 
        semantic: Union[bool, Iterable] = False
    ) -> pd.DataFrame:
    """Split the PATH column in a DataFrame into it's components. 

    Parameters
    ----------
    df : pandas.DataFrame
        A pandas DataFrame with a HEC-DSS style path column.
    semantic : Union[bool, Iterable], optional
        Change the A-F column labels, True gives CalSim3 interpretation, by default False

    Returns
    -------
    pandas.DataFrame
        A copy of the original pandas DataFrame with 6 new columns.
    """    
    df = df.copy()
    df[['A', 'B', 'C', 'D', 'E', 'F']] = df['PATH']\
        .str.strip('/')\
        .str.split('/', n=6, expand=True)
    if semantic:
        if semantic is True:  
            semantic = PART_NAMES  # Default to CalSim3 meaning
        df = df.rename(columns=semantic)
        
    return df
