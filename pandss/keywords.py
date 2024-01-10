from enum import Enum, StrEnum


class Duration(StrEnum):
    YEAR = "1YEAR"
    MONTH = "1MONTH"
    SEMI_MONTH = "SEMI-MONTH"
    TRI_MONTH = "TRI-MONTH"
    WEEK = "1WEEK"
    DAY = "1DAY"
    HOUR = "1HOUR"
    MINUTE = "1MINUTE"
    SECOND = "1SECOND"
    # Hour groups
    HOUR_12 = "12HOUR"
    HOUR_8 = "8HOUR"
    HOUR_6 = "6HOUR"
    HOUR_4 = "4HOUR"
    HOUR_3 = "3HOUR"
    HOUR_2 = "2HOUR"
    # Minute groups
    MINUTE_30 = "30MINUTE"
    MINUTE_20 = "20MINUTE"
    MINUTE_15 = "15MINUTE"
    MINUTE_10 = "10MINUTE"
    MINUTE_6 = "6MINUTE"
    MINUTE_5 = "5MINUTE"
    MINUTE_4 = "4MINUTE"
    MINUTE_3 = "3MINUTE"
    MINUTE_2 = "2MINUTE"
    # Second groups
    SECOND_30 = "30SECOND"
    SECOND_20 = "20SECOND"
    SECOND_15 = "15SECOND"
    SECOND_10 = "10SECOND"
    SECOND_6 = "6SECOND"
    SECOND_5 = "5SECOND"
    SECOND_4 = "4SECOND"
    SECOND_3 = "3SECOND"
    SECOND_2 = "2SECOND"


class PeriodTypes(StrEnum):
    INSTANT = "INST-VAL"  # Example: Stages
    CUMULATIVE = "INST-CUM"  # Example Precipitation Mass urve
    PERIOD_AVERAGE = "PER-AVER"  # Example: Monthly Flow
    PERIOD_CUMULATIVE = "PER-CUM"  # Example: Incremental Precipitation


class Missing(Enum):
    VALUE = -901.0
    RECORD = -902.0
