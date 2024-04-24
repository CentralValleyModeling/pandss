import pickle
from pathlib import Path
from time import perf_counter
from warnings import catch_warnings

import numpy as np
import pandas as pd
import pytest
from pytest import FixtureRequest

import pandss as pdss
from pandss import timeseries
from pandss.timeseries.period_type import PeriodTypeStandard


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_read_type(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    catalog = pdss.read_catalog(dss)
    p = catalog.paths.pop()
    rts = pdss.read_rts(dss, p)
    assert isinstance(rts, pdss.RegularTimeseries)


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_read_time(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    times = list()
    with pdss.DSS(dss) as dss_obj:
        for _ in range(10):
            st = perf_counter()
            _ = dss_obj.read_rts(p)
            et = perf_counter()
            times.append(et - st)
    average = sum(times) / len(times)
    assert average <= 0.11


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_data_content(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss) as dss_obj:
        rts = dss_obj.read_rts(p)
        assert len(rts) == len(rts.values)
        assert len(rts.values) == len(rts.dates)
        assert rts.path == p
        assert hasattr(rts.values, "__array_ufunc__") is True
        assert hasattr(rts.values, "__array_function__") is True
        value = rts.values[0]
        assert isinstance(value, np.float64)
        assert isinstance(rts.dates, np.ndarray)
        assert rts.period_type in PeriodTypeStandard()
        assert rts.dates[0] == np.datetime64("1921-10-31T23:59:59")
        assert value == 31.0


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_interval(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    interval = pdss.timeseries.Interval(e="1MON")
    with pdss.DSS(dss) as dss_obj:
        rts = dss_obj.read_rts(p)
        assert isinstance(rts.interval, timeseries.Interval)
        assert rts.interval == interval


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_to_frame(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss) as dss_obj:
        rts = dss_obj.read_rts(p)
        df = rts.to_frame()
        assert isinstance(df, pd.DataFrame)
        for L, R in zip(
            df.columns.names,
            ["A", "B", "C", "D", "E", "F", "UNITS", "PERIOD_TYPE", "INTERVAL"],
        ):
            assert L == R
        assert len(rts) == len(df)


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_multiple_to_frame(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str("/CALSIM/.*/.*/.*/.*/.*/")
    with pdss.DSS(dss) as dss_obj:
        p = dss_obj.resolve_wildcard(p)
        frames = [obj.to_frame() for obj in dss_obj.read_multiple_rts(p)]
        df = pd.concat(frames)
        assert isinstance(df, pd.DataFrame)
        for L, R in zip(
            df.columns.names,
            ["A", "B", "C", "D", "E", "F", "UNITS", "PERIOD_TYPE", "INTERVAL"],
        ):
            assert L == R


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_add_rts(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss) as dss_obj:
        rts = dss_obj.read_rts(p)
        double_month = rts + rts
        assert double_month.values[0] == 62


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_add_with_misaligned_dates(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss) as dss_obj:
        rts = dss_obj.read_rts(p)
        dates = pd.to_datetime(rts.dates)
        # offset by four years to avoid leap year weirdness in this test
        dates = dates + pd.DateOffset(years=4)
        rts_2 = pdss.RegularTimeseries(
            path=pdss.DatasetPath.from_str(
                "/CALSIM/MONTH_DAYS_OFFSET/DAY//1MON/L2020A/"
            ),
            values=rts.values,
            dates=dates.values,
            units=rts.units,
            period_type=rts.period_type,
            interval=rts.interval,
        )
        rts_add_LR = rts + rts_2
        assert rts_add_LR.values[0] == 62
        assert len(rts_add_LR.values) == len(rts_add_LR.dates)
        assert len(rts_add_LR) == 1200 - 48
        rts_add_RL = rts_2 + rts  # Swap places
        assert rts_add_RL.values[0] == 62
        assert len(rts_add_RL.values) == len(rts_add_RL.dates)
        assert len(rts_add_RL) == 1200 - 48


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_read_single_with_wildcard(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p1 = pdss.DatasetPath(b="MONTH_DAYS")
    rts = pdss.read_rts(dss, p1)
    assert isinstance(rts, pdss.RegularTimeseries)
    with pytest.raises(pdss.errors.UnexpectedDSSReturn):
        p2 = pdss.DatasetPath(f="L2020A")
        _ = pdss.read_rts(dss, p2)


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_to_json(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p1 = pdss.DatasetPath(b="MONTH_DAYS")
    rts = pdss.read_rts(dss, p1)
    j = rts.to_json()
    assert j["path"] == str(rts.path)


def test_from_json():
    obj = dict(
        path="/.*/MONTH_DAYS/.*//.*/.*/",
        values=(31, 28, 31),
        dates=("1921-01-31", "1921-02-28", "1921-03-31"),
        period_type="PER-CUM",
        units="days",
        interval="1MON",
    )
    rts = pdss.RegularTimeseries.from_json(obj)
    assert rts.units == obj["units"]


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_json_pipeline(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p1 = pdss.DatasetPath(b="MONTH_DAYS")
    rts_1 = pdss.read_rts(dss, p1)
    rts_2 = pdss.RegularTimeseries.from_json(rts_1.to_json())
    assert rts_1 == rts_2
    assert id(rts_1) != id(rts_2)


def test_fix_types():
    obj = dict(
        path="/.*/MONTH_DAYS/.*//.*/.*/",
        values=(31, 28, 31),
        dates=("1921-01-31", "1921-02-28", "1921-03-31"),
        period_type="PER-CUM",
        units="days",
        interval="1MON",
    )
    rts = pdss.RegularTimeseries(**obj)
    assert isinstance(rts.values, np.ndarray)


def test_accept_path_as_str():
    obj = dict(
        path="/.*/MONTH_DAYS/.*//.*/.*/",
        values=(31, 28, 31),
        dates=("1921-01-31", "1921-02-28", "1921-03-31"),
        period_type="PER-CUM",
        units="days",
        interval="1MON",
    )
    rts = pdss.RegularTimeseries(**obj)
    assert isinstance(rts.path, pdss.DatasetPath)
    assert rts.path.b == "MONTH_DAYS"


@pytest.mark.parametrize("dss", ("dss_6", "dss_7"))
def test_write_rts(dss, temporary_dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p_old = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss) as dss_obj:
        rts = dss_obj.read_rts(p_old)
    rts.values = rts.values + 1
    p_new = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS_PLUS_ONE/DAY//1MON/L2020A/")
    with pdss.DSS(temporary_dss) as dss_new:
        dss_new.write_rts(p_new, rts)
        catalog = dss_new.read_catalog()
    assert len(catalog) == 1


@pytest.mark.parametrize("dss", ("dss_6", "dss_7"))
def test_copy_rts(dss, temporary_dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p_old = pdss.DatasetPath.from_str(
        "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",
    )
    p_new = pdss.DatasetPath.from_str(
        "/CALSIM/MONTH_DAYS_PLUS_ONE/DAY//1MON/L2020A/",
    )
    with catch_warnings(action="error"):
        pdss.copy_rts(dss, temporary_dss, (p_old, p_new))
    assert temporary_dss.exists() is True
    catalog = pdss.read_catalog(temporary_dss)
    assert len(catalog) == 1


@pytest.mark.parametrize("dss", ("dss_6", "dss_7"))
def test_copy_multiple_rts_6(dss, temporary_dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p_old = (
        "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",
        "/CALSIM/PPT_OROV/PRECIP//1MON/L2020A/",
    )
    p_new = (
        "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",
        "/CALSIM/PPT_OROV/PRECIP//1MON/L2020A/",
    )
    with catch_warnings(action="error"):
        pdss.copy_multiple_rts(dss, temporary_dss, tuple(zip(p_old, p_new)))
    assert temporary_dss.exists() is True
    catalog = pdss.read_catalog(temporary_dss)
    assert len(catalog) == 2


@pytest.mark.parametrize("dss", ("dss_6", "dss_7"))
def test_pickle_rts(dss, created_dir, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    pickle_location = created_dir / "month_days.pkl"
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss) as dss_obj:
        rts = dss_obj.read_rts(p)
    with open(pickle_location, "wb") as OUT:
        pickle.dump(rts, OUT)
    with open(pickle_location, "rb") as IN:
        rts_salty = pickle.load(IN)
    assert rts == rts_salty


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_update_rts(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p1 = pdss.DatasetPath(b="MONTH_DAYS")
    rts_1 = pdss.read_rts(dss, p1)
    rts_2 = rts_1.update(units="MOON-DAY")
    # Basic attr tests
    assert rts_1.path == rts_2.path
    assert id(rts_1) != id(rts_2)
    assert rts_1 != rts_2
    assert rts_1.units == "DAYS"
    assert rts_2.units == "MOON-DAY"
    # Test bad update of values without update of dates
    with pytest.raises(ValueError):
        rts_1.update(values=[0])
    # Test update of values with same len dates
    rts_3 = rts_2.update(values=[31], dates=["2000-01-31"])
    assert rts_3.path == rts_2.path
    # Test changing values
    rts_1.values[0] = -1000
    assert rts_1.values[0] != rts_2.values[0]
