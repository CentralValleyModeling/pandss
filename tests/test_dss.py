import pytest

import pandss as pdss


def test_multiple_with_wildcard_6(dss_6):
    p = pdss.DatasetPath.from_str("/.*/.*/.*/.*/.*/.*/")
    matched_timeseries = 0
    for rts in pdss.read_multiple_rts(dss_6, p):
        assert isinstance(rts, pdss.RegularTimeseries)
        matched_timeseries += 1
    assert matched_timeseries == 2


def test_multiple_with_wildcard_7(dss_7):
    p = pdss.DatasetPath.from_str("/.*/.*/.*/.*/.*/.*/")
    matched_timeseries = 0
    for rts in pdss.read_multiple_rts(dss_7, p):
        assert isinstance(rts, pdss.RegularTimeseries)
        matched_timeseries += 1
    assert matched_timeseries == 2


def test_multiple_with_partial_wildcard_6(dss_6):
    p = pdss.DatasetPath.from_str("/CALSIM/MO.*DAYS/.*/.*/.*/.*/")
    matched_timeseries = 0
    for rts in pdss.read_multiple_rts(dss_6, p):
        assert isinstance(rts, pdss.RegularTimeseries)
        matched_timeseries += 1
    assert matched_timeseries == 1


def test_multiple_with_partial_wildcard_7(dss_7):
    p = pdss.DatasetPath.from_str("/CALSIM/MO.*DAYS/.*/.*/.*/.*/")
    matched_timeseries = 0
    for rts in pdss.read_multiple_rts(dss_7, p):
        assert isinstance(rts, pdss.RegularTimeseries)
        matched_timeseries += 1
    assert matched_timeseries == 1


def test_pyhecdss_engine_6(dss_6):
    with pdss.DSS(dss_6, engine="pyhecdss") as dss:
        catalog = dss.read_catalog()
        assert isinstance(catalog, pdss.Catalog)
        assert len(catalog) == 2
        for rts in dss.read_multiple_rts(catalog):
            assert isinstance(rts, pdss.RegularTimeseries)


def test_pyhecdss_engine_7(dss_7):
    with pytest.raises(pdss.errors.FileVersionError):
        with pdss.DSS(dss_7, engine="pyhecdss") as dss:
            pass


def test_pydsstools_engine_6(dss_6):
    with pdss.DSS(dss_6, engine="pydsstools") as dss:
        catalog = dss.read_catalog(drop_date=True)
        assert isinstance(catalog, pdss.Catalog)
        assert len(catalog) == 2
        for rts in dss.read_multiple_rts(catalog):
            assert isinstance(rts, pdss.RegularTimeseries)


def test_pydsstools_engine_7(dss_7):
    with pdss.DSS(dss_7, engine="pydsstools") as dss:
        catalog = dss.read_catalog(drop_date=True)
        assert isinstance(catalog, pdss.Catalog)
        assert len(catalog) == 2
        for rts in dss.read_multiple_rts(catalog):
            assert isinstance(rts, pdss.RegularTimeseries)


def test_multiple_open_close(dss_6):
    dss_1 = pdss.DSS(dss_6)
    dss_2 = pdss.DSS(dss_6)
    with dss_1 as obj_1, dss_2 as obj_2:
        assert isinstance(obj_1, pdss.DSS)
        assert isinstance(obj_2, pdss.DSS)
    assert dss_1.is_open is False
    assert dss_2.is_open is False


def test_stacked_wtih(dss_6):
    dss = pdss.DSS(dss_6)
    with dss:
        with dss:
            pass
        assert isinstance(dss, pdss.DSS)
        assert dss.is_open is True


def test_stacked_with_error_handling(dss_6):
    dss = pdss.DSS(dss_6)
    with pytest.raises(ZeroDivisionError):
        with dss:
            try:
                with dss:
                    assert dss._opened == 2
                    _ = 1 / 0
            finally:
                assert dss._opened == 1
                assert dss.is_open is True
    assert dss.is_open is False


def test_path_as_string(dss_6):
    p = "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/"
    with pdss.DSS(dss_6) as dss:
        rts = dss.read_rts(p)
        assert isinstance(rts, pdss.RegularTimeseries)
