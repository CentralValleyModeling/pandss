import pickle
from time import perf_counter
from warnings import catch_warnings

import numpy as np
import pandas as pd
import pytest

import pandss as pdss
from pandss import timeseries
from pandss.timeseries.period_type import PeriodTypeStandard


def test_read_type_6(dss_6):
    catalog = pdss.read_catalog(dss_6)
    p = catalog.paths.pop()
    rts = pdss.read_rts(dss_6, p)
    assert isinstance(rts, pdss.RegularTimeseries)


def test_read_type_7(dss_7):
    catalog = pdss.read_catalog(dss_7)
    p = catalog.paths.pop()
    rts = pdss.read_rts(dss_7, p)
    assert isinstance(rts, pdss.RegularTimeseries)


def test_read_time_6(dss_6):
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    times = list()
    with pdss.DSS(dss_6) as dss:
        for _ in range(10):
            st = perf_counter()
            _ = dss.read_rts(p)
            et = perf_counter()
            times.append(et - st)
    average = sum(times) / len(times)
    assert average <= 0.11


def test_read_time_7(dss_7):
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    times = list()
    with pdss.DSS(dss_7) as dss:
        for _ in range(10):
            st = perf_counter()
            _ = dss.read_rts(p)
            et = perf_counter()
            times.append(et - st)
    average = sum(times) / len(times)
    assert average <= 0.15


def test_data_content_6(dss_6):
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss_6) as dss:
        rts = dss.read_rts(p)
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


def test_data_content_7(dss_7):
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss_7) as dss:
        rts = dss.read_rts(p)
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


def test_interval_6(dss_6):
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    interval = pdss.timeseries.Interval(e="1MON")
    with pdss.DSS(dss_6) as dss:
        rts = dss.read_rts(p)
        assert isinstance(rts.interval, timeseries.Interval)
        assert rts.interval == interval


def test_to_frame(dss_6):
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss_6) as dss:
        rts = dss.read_rts(p)
        df = rts.to_frame()
        assert isinstance(df, pd.DataFrame)
        for L, R in zip(
            df.columns.names,
            ["A", "B", "C", "D", "E", "F", "UNITS", "PERIOD_TYPE", "INTERVAL"],
        ):
            assert L == R
        assert len(rts) == len(df)


def test_multiple_to_frame(dss_6):
    p = pdss.DatasetPath.from_str("/CALSIM/.*/.*/.*/.*/.*/")
    with pdss.DSS(dss_6) as dss:
        p = dss.resolve_wildcard(p)
        frames = [obj.to_frame() for obj in dss.read_multiple_rts(p)]
        df = pd.concat(frames)
        assert isinstance(df, pd.DataFrame)
        for L, R in zip(
            df.columns.names,
            ["A", "B", "C", "D", "E", "F", "UNITS", "PERIOD_TYPE", "INTERVAL"],
        ):
            assert L == R


def test_add_rts(dss_6):
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss_6) as dss:
        rts = dss.read_rts(p)
        double_month = rts + rts
        assert double_month.values[0] == 62


def test_add_with_misaligned_dates(dss_6):
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss_6) as dss:
        rts = dss.read_rts(p)
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


def test_large_dss_to_frame_6(dss_large):
    p = pdss.DatasetPath.from_str("/CALSIM/.*/.*/.*/1MON/.*/")
    st = perf_counter()
    with pdss.DSS(dss_large) as dss:
        p = dss.resolve_wildcard(p)
        assert len(p) == 1_700
        p = pdss.DatasetPathCollection(paths=set(list(p.paths)[:100]))
        df = pd.concat(obj.to_frame() for obj in dss.read_multiple_rts(p))
        assert isinstance(df, pd.DataFrame)
        for L, R in zip(
            df.columns.names,
            ["A", "B", "C", "D", "E", "F", "UNITS", "PERIOD_TYPE", "INTERVAL"],
        ):
            assert L == R
    et = perf_counter()
    tt = et - st
    assert tt <= 20.0


def test_read_single_with_wildcard(dss_6):
    p1 = pdss.DatasetPath(b="MONTH_DAYS")
    rts = pdss.read_rts(dss_6, p1)
    assert isinstance(rts, pdss.RegularTimeseries)
    with pytest.raises(pdss.errors.UnexpectedDSSReturn):
        p2 = pdss.DatasetPath(f="L2020A")
        _ = pdss.read_rts(dss_6, p2)


def test_to_json(dss_6):
    p1 = pdss.DatasetPath(b="MONTH_DAYS")
    rts = pdss.read_rts(dss_6, p1)
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


def test_json_pipeline(dss_6):
    p1 = pdss.DatasetPath(b="MONTH_DAYS")
    rts_1 = pdss.read_rts(dss_6, p1)
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


def test_write_rts_6(dss_6, temporary_dss):
    p_old = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss_6) as dss:
        rts = dss.read_rts(p_old)
    rts.values = rts.values + 1
    p_new = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS_PLUS_ONE/DAY//1MON/L2020A/")
    with pdss.DSS(temporary_dss) as dss_new:
        dss_new.write_rts(p_new, rts)
        catalog = dss_new.read_catalog()
    assert len(catalog) == 1


def test_copy_rts_6(dss_6, temporary_dss):
    p_old = pdss.DatasetPath.from_str(
        "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",
    )
    p_new = pdss.DatasetPath.from_str(
        "/CALSIM/MONTH_DAYS_PLUS_ONE/DAY//1MON/L2020A/",
    )
    with catch_warnings(action="error"):
        pdss.copy_rts(dss_6, temporary_dss, (p_old, p_new))
    assert temporary_dss.exists() is True
    catalog = pdss.read_catalog(temporary_dss)
    assert len(catalog) == 1


def test_copy_multiple_rts_6(dss_6, temporary_dss):
    p_old = (
        "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",
        "/CALSIM/PPT_OROV/PRECIP//1MON/L2020A/",
    )
    p_new = (
        "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",
        "/CALSIM/PPT_OROV/PRECIP//1MON/L2020A/",
    )
    with catch_warnings(action="error"):
        pdss.copy_multiple_rts(dss_6, temporary_dss, tuple(zip(p_old, p_new)))
    assert temporary_dss.exists() is True
    catalog = pdss.read_catalog(temporary_dss)
    assert len(catalog) == 2


def test_pickle_rts_6(dss_6, created_dir):
    pickle_location = created_dir / "month_days.pkl"
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    with pdss.DSS(dss_6) as dss:
        rts = dss.read_rts(p)
    with open(pickle_location, "wb") as OUT:
        pickle.dump(rts, OUT)
    with open(pickle_location, "rb") as IN:
        rts_salty = pickle.load(IN)
    assert rts == rts_salty


def test_update_rts(dss_6):
    p1 = pdss.DatasetPath(b="MONTH_DAYS")
    rts_1 = pdss.read_rts(dss_6, p1)
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
