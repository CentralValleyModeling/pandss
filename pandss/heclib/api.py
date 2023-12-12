import logging
from ctypes import CDLL, POINTER, c_char_p, c_double, c_int, c_longlong
from typing import Iterator

DSS_FILE = c_longlong * 250


class DLL_Signature:
    """Simple class to contain the argument and result types for a single
    function in the DLL. The argument types default to empty.
    """

    __slots__ = ["argtypes", "restype"]

    def __init__(self, restype, argtypes: tuple = None):
        self.argtypes = argtypes
        self.restype = restype


class DLL_API:
    """class to pre-define the argument and result types of exposed functions."""

    def __init__(self, version: int):
        self.version = version
        self.hec_dss_open = DLL_Signature(
            argtypes=(
                c_char_p,
                POINTER(POINTER(DSS_FILE)),
            ),
            restype=c_int,
        )
        self.hec_dss_close = DLL_Signature(
            argtypes=(POINTER(DSS_FILE),),
            restype=c_int,
        )
        self.hec_dss_catalog = DLL_Signature(
            argtypes=(
                POINTER(DSS_FILE),
                c_char_p,
                POINTER(c_int),
                c_char_p,
                c_int,
                c_int,
            ),
            restype=c_int,
        )
        self.hec_dss_record_count = DLL_Signature(
            argtypes=(POINTER(DSS_FILE),),
            restype=c_int,
        )
        self.hec_dss_CONSTANT_MAX_PATH_SIZE = DLL_Signature(
            restype=c_int,
        )
        self.hec_dss_tsRetrieveInfo = DLL_Signature(
            argtypes=(
                POINTER(DSS_FILE),
                c_char_p,
                c_char_p,
                c_int,
                c_char_p,
                c_int,
            ),
            restype=c_int,
        )
        self.hec_dss_tsRetrieve = DLL_Signature(
            argtypes=(
                POINTER(DSS_FILE),  # dss
                c_char_p,  # A-F path
                c_char_p,  # start_date
                c_char_p,  # start_time
                c_char_p,  # end_date
                c_char_p,  # end_time
                POINTER(c_int),  # time_array
                POINTER(c_double),  # value_array
                c_int,  # array_size
                POINTER(c_int),  # number_read
                POINTER(c_int),  # quality
                c_int,  # quality_len
                POINTER(c_int),  # base_date
                POINTER(c_int),  # time_resolution
                c_char_p,  # units
                c_int,  # units_len
                c_char_p,  # data_type
                c_int,  # data_type_len
            ),
            restype=c_int,
        )
        self.hec_dss_tsGetSizes = DLL_Signature(
            argtypes=(
                POINTER(DSS_FILE),  # dss
                c_char_p,  # A-F path
                c_char_p,  # start_date
                c_char_p,  # start_time
                c_char_p,  # end_date
                c_char_p,  # end_time
                POINTER(c_int),  # number_values
                POINTER(c_int),  # quality_elements
            ),
            restype=c_int,
        )
        self.hec_dss_tsGetDateTimeRange = DLL_Signature(
            argtypes=(
                POINTER(DSS_FILE),  # dss
                c_char_p,  # A-F path
                c_int,  # full_set
                POINTER(c_int),  # first_date
                POINTER(c_int),  # first_seconds
                POINTER(c_int),  # last_date
                POINTER(c_int),  # last_seconds
            ),
            restype=c_int,
        )
        self.hec_dss_set_value = DLL_Signature(
            argtypes=(
                c_char_p,
                c_int,
            ),
            restype=c_int,
        )
        self.hec_dss_set_string = DLL_Signature(
            argtypes=(
                c_char_p,
                c_char_p,
            ),
            restype=c_int,
        )
        self.hec_dss_convertToVersion7 = DLL_Signature(
            argtypes=(c_char_p, c_char_p), restype=c_int
        )

    def __iter__(self) -> Iterator[tuple[str, DLL_Signature]]:
        for function, signature in vars(self).items():
            if not isinstance(signature, DLL_Signature):
                continue
            yield function, signature

    def add_signatures_to_dll(self, dll: CDLL) -> CDLL:
        for function, signature in self:
            try:
                func: CDLL._FuncPtr = getattr(dll, function)
                if signature.argtypes:
                    func.argtypes = signature.argtypes
                func.restype = signature.restype
                logging.debug(f"api added for {function}")
            except AttributeError:
                logging.warn(f"DLL has no function `{function}`")

        return dll
