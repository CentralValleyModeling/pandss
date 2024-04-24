from time import perf_counter

import pyhecdss
import pytest
from pytest import FixtureRequest

import pandss as pdss


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_read_type(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    catalog = pdss.read_catalog(dss)
    assert isinstance(catalog, pdss.Catalog), f"type is {type(catalog)}"


@pytest.mark.parametrize("dss", ("dss_6", "dss_7"))
def test_read_time(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    times = list()
    for _ in range(100):
        st = perf_counter()
        _ = pdss.read_catalog(dss)
        et = perf_counter()
        times.append(et - st)
    average = sum(times) / len(times)
    assert average <= 0.02, f"average time is: {average} for {dss}"


@pytest.mark.parametrize("dss", ("dss_6",))
def test_from_frame(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    with pyhecdss.DSSFile(str(dss)) as dss:
        df_cat = dss.read_catalog()
    cat = pdss.Catalog.from_frame(df_cat, dss)
    assert isinstance(cat, pdss.Catalog)
    assert len(cat) == len(df_cat)
