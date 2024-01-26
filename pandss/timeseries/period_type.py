class PeriodTypeStandard:
    def __init__(self):
        # values from DSS documentation
        # https://www.hec.usace.army.mil/confluence/dssdocs/dsscprogrammer/time-series-data
        self.valid = ("INST-VAL", "INST-CUM", "PER-AVER", "PER-CUM")

    def __contains__(self, __other: str) -> bool:
        return __other in self.valid

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.valid})"
