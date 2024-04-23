import pandas as pd
import pytest

import pandss as pdss
from pandss.timeseries.interval import Interval


def test_ordering():
    i_big = Interval(e="1Day")  # version 7 style
    i_small = Interval(e="1MIN")  # versuon 6 style
    assert i_big >= i_small


def test_to_period_offset_alias():
    yearly = Interval("1Year")
    assert yearly.offset == "Y"
    century = Interval("IR-CENTURY")
    assert century.offset == "100Y"


def test_seconds():
    i1 = Interval(e="10MIN")  # version 7 style
    assert i1.seconds == 10 * 60
    i2 = Interval(e="12Hour")  # version 6 style
    assert i2.seconds == 12 * 60 * 60


def test_slots():
    yearly = Interval(e="1Year")  # version 7 style
    with pytest.raises(AttributeError):
        yearly.foo = None


def test_single_period():
    period = pd.Period(
        value=pd.to_datetime("2023-01-01"),
        freq=Interval("1MON").freq,
    )
    assert period.days_in_month == 31


def test_period_index():
    periods = pd.PeriodIndex(
        data=(
            pd.to_datetime("2023-02-01"),
            pd.to_datetime("2024-02-01"),
        ),
        freq=Interval("1MON").freq,
    )
    for L, R in zip(periods.days_in_month, [28, 29]):
        assert L == R


def test_frame_matches_interval_object(dss_6):
    p = pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/")
    rts = pdss.read_rts(dss_6, p)
    frame = rts.to_frame()
    assert str(rts.interval) == "1MON"
    assert frame.columns.get_level_values("INTERVAL") == str(rts.interval)


def test_create_rts_with_str_interval():
    rts = pdss.RegularTimeseries(
        path="/A/B/C//E/F/",
        values=(1,),
        dates=("2024-01-31",),
        period_type="PER-CUM",
        units="TAF",
        interval="1MON",
    )
    assert isinstance(rts.interval, Interval)
