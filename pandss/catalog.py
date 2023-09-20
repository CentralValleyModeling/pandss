import logging
from pathlib import Path
from typing import Iterator, Optional, Union
from warnings import warn

import pyhecdss
from pandas import DataFrame
from pandas.errors import OutOfBoundsDatetime

from .paths import PathLike

COMPARE_ON = ["A", "B", "C", "E", "D"]
ALL_CATALOG_COLUMNS = ["T", *COMPARE_ON]


def read_catalog(
    dss: PathLike,
) -> DataFrame:
    """Read the catalog from a DSS file.

    Parameters
    ----------
    dss : Union[PathLike, Iterable[PathLike]]
        The path or paths to the DSS file(s).

    Returns
    -------
    pd.DataFrame
        A list of, or single pandas.DataFrame catalogs.
    """
    logging.info(f"reading catalog from {dss}")
    with pyhecdss.DSSFile(str(dss)) as DSS:
        catalog = DSS.read_catalog()

    logging.info(f"catalog size is {len(catalog)}")
    return catalog


def common_catalog(
    left: Union[PathLike, DataFrame],
    right: Union[PathLike, DataFrame],
    ignore_parts: Optional[list] = None,
) -> tuple[DataFrame, DataFrame]:
    """Extract the common catalog from two DSS files. Allows for comparisons
    on custom collections of columns. Only can compare two catalogs.

    Parameters
    ----------
    left : Union[PathLike, DataFrame]
        The left DSS file, or catalog DataFrame
    right : Union[PathLike, DataFrame]
        The right DSS file, or catalog DataFrame
    ignore_parts : Optional[list], optional
        Parts of the path to ignore when considering equality, by default None

    Returns
    -------
    tuple[DataFrame, DataFrame]
        The two intersecting catalogs, for the left and right
    """
    # Allow for paths instead
    if isinstance(left, (Path, str)):
        logging.info(f"reading path: {left=}")
        left = read_catalog(left)
    if isinstance(right, (Path, str)):
        logging.info(f"reading path: {right=}")
        right = read_catalog(right)
    compare_on = COMPARE_ON
    if ignore_parts is not None:
        compare_on = [c for c in compare_on if c not in ignore_parts]
    if not compare_on:  # All items removed.
        raise ValueError(
            f"Cannot ignore all parts of the catalog. invalid arg: {ignore_parts=}"
        )

    logging.info(f"{compare_on=}")
    # Track the order of the columns passed
    left_col_order = left.columns
    right_col_order = right.columns
    logging.info(f"left columns seen: {left_col_order}")
    logging.info(f"left catalog length: {len(left)}")
    logging.info(f"right columns seen: {right_col_order}")
    logging.info(f"right catalog length: {len(right)}")

    left = left.set_index(compare_on)
    right = right.set_index(compare_on)
    if any(left.groupby(left.index).size() > 1):
        warn(f"common index ({compare_on}) does not create unique values on left.")
    if any(right.groupby(right.index).size() > 1):
        warn(f"common index ({compare_on}) does not create unique values on right.")
    index_common = left.index.intersection(right.index)
    logging.info(f"length of common index {len(index_common)}")
    left = left.loc[index_common].reset_index()
    right = right.loc[index_common].reset_index()

    return left[left_col_order], right[right_col_order]


def iter_common_catalog(
    left: Union[PathLike, DataFrame],
    right: Union[PathLike, DataFrame],
    groupby: str = "B",
    ignore_parts: Optional[list] = None,
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
    ignore_parts : Optional[list], optional
        Parts of the path to ignore when considering equality, by default None

    Yields
    ------
    Iterator[tuple[str, DataFrame, DataFrame]]
        An iterator that yields a tuple of the groupby index, and each section
    """
    cat_base, cat_alt = common_catalog(left, right, ignore_parts=ignore_parts)
    g_L = cat_base.groupby(groupby)
    g_R = cat_alt.groupby(groupby)
    for (c, df_L), (_, df_R) in zip(g_L, g_R):
        yield c, df_L, df_R
