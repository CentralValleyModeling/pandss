import pandas as pd


PART_NAMES = {
    'A': 'MODEL',
    'B': 'NAME',
    'C': 'TYPE',
    'D': 'DATE',
    'E': 'INTERVAL',
    'F': 'DEVELOPMENT',
}


def split_path_column(df: pd.DataFrame, semantic: bool = False) -> pd.DataFrame:
    """Split the PATH column in a DataFrame into it's components. 

    Args:
        df (pd.DataFrame): A DataFrame with a HEC-DSS style path column.

    Returns:
        pd.DataFrame: A copy of the original DataFrame with 6 new columns.
    """
    df = df.copy()
    df[['A', 'B', 'C', 'D', 'E', 'F']] = df['PATH']\
        .str.strip('/')\
        .str.split('/', n=6, expand=True)
    if semantic:
        df = df.rename(columns=PART_NAMES)
        
    return df