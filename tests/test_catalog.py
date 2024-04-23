from time import perf_counter

import pyhecdss

import pandss as pdss


def test_read_type_6(dss_6):
    catalog = pdss.read_catalog(dss_6)
    assert isinstance(catalog, pdss.Catalog)


def test_read_type_7(dss_7):
    catalog = pdss.read_catalog(dss_7)
    assert isinstance(catalog, pdss.Catalog)


def test_read_time_6(dss_6):
    times = list()
    for _ in range(100):
        st = perf_counter()
        _ = pdss.read_catalog(dss_6)
        et = perf_counter()
        times.append(et - st)
    average = sum(times) / len(times)
    assert average <= 0.02


def test_read_time_7(dss_7):
    times = list()
    for _ in range(100):
        st = perf_counter()
        _ = pdss.read_catalog(dss_7)
        et = perf_counter()
        times.append(et - st)
    average = sum(times) / len(times)
    assert average <= 0.02


def test_from_frame_6(dss_6):
    with pyhecdss.DSSFile(str(dss_6)) as dss:
        df_cat = dss.read_catalog()
    cat = pdss.Catalog.from_frame(df_cat, dss_6)
    assert isinstance(cat, pdss.Catalog)
    assert len(cat) == len(df_cat)
