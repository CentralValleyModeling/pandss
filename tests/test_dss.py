import pytest
from pytest import FixtureRequest

import pandss as pdss


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_multiple_with_wildcard(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str("/.*/.*/.*/.*/.*/.*/")
    matched_timeseries = 0
    for rts in pdss.read_multiple_rts(dss, p):
        assert isinstance(rts, pdss.RegularTimeseries)
        matched_timeseries += 1
    assert matched_timeseries > 1


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_multiple_with_partial_wildcard(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str("/CALSIM/MO.*DAYS/.*/.*/.*/.*/")
    matched_timeseries = 0
    for rts in pdss.read_multiple_rts(dss, p):
        assert isinstance(rts, pdss.RegularTimeseries)
        matched_timeseries += 1
    assert matched_timeseries == 1


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_multiple_open_close(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    dss_1 = pdss.DSS(dss)
    dss_2 = pdss.DSS(dss)
    with dss_1 as obj_1, dss_2 as obj_2:
        assert isinstance(obj_1, pdss.DSS)
        assert isinstance(obj_2, pdss.DSS)
    assert dss_1.is_open is False
    assert dss_2.is_open is False


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_stacked_wtih(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    dss = pdss.DSS(dss)
    with dss:
        with dss:
            pass
        assert isinstance(dss, pdss.DSS)
        assert dss.is_open is True


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_stacked_with_error_handling(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    dss = pdss.DSS(dss)
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


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_path_as_string(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/"
    with pdss.DSS(dss) as dss:
        rts = dss.read_rts(p)
        assert isinstance(rts, pdss.RegularTimeseries)
