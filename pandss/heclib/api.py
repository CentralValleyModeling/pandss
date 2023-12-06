import ctypes as ct
import logging
from pathlib import Path
from typing import Iterator


DLL_AVAIL = {
    6: None,
    7: str(Path(__file__).parent / "heclib-7-IR-4-win-x86_64/release64/hecdss.dll")
}

class DLL_Signature:
    """Simple class to contain the argument and result types for a single 
    function in the DLL. The argument types default to empty.
    """
    __slots__ = ["argtypes", "restype"]
    def __init__(self, restype, argtypes: tuple = None):
        self.argtypes = argtypes
        self.restype = restype

class DLL_API:
    """class to pre-define the argument and result types of exposed functions.
    """
    def __init__(self, version: int):
        self.version = version
        self.hec_dss_open = DLL_Signature(
            argtypes=(ct.c_char_p, ct.POINTER(ct.c_void_p), ), 
            restype=ct.c_int,
        )
        self.hec_dss_close = DLL_Signature(
            argtypes=(ct.c_void_p,), 
            restype=ct.c_int,
        )
        self.hec_dss_catalog = DLL_Signature(
            argtypes=(
                ct.c_void_p,
                ct.c_char_p,
                ct.POINTER(ct.c_int),
                ct.c_char_p,
                ct.POINTER(ct.c_int),
                ct.POINTER(ct.c_int),
            ),
            restype=ct.c_int,
        )
        self.hec_dss_record_count = DLL_Signature(
            argtypes=(ct.c_void_p,),
            restype=ct.c_int
        )
        self.hec_dss_CONSTANT_MAX_PATH_SIZE = DLL_Signature(
            restype=ct.c_int
        )
        self.hec_dss_tsRetrieve = DLL_Signature(
            argtypes=(
                ct.c_void_p,  # dss
                ct.c_void_p,  # A-F path
                ct.c_void_p,  # start_date
                ct.c_void_p,  # start_time
                ct.c_void_p,  # end_date
                ct.c_void_p,  # end_time
                ct.POINTER(ct.c_int),     # time_array
                ct.POINTER(ct.c_double),  # value_array
                ct.c_int,                 # array_size
                ct.POINTER(ct.c_int),     # number_read
                ct.POINTER(ct.c_int),  # quality
                ct.c_int,              # quality_len
                ct.POINTER(ct.c_int),  # base_date
                ct.POINTER(ct.c_int),  # time_resolution
                ct.c_char_p,  # units
                ct.c_int,     # units_len
                ct.c_char_p,  # data_type
                ct.c_int,     # data_type_len
            ),
            restype=ct.c_int
        )
        self.hec_dss_tsGetSizes = DLL_Signature(
            argtypes=(
                ct.c_void_p,  # dss
                ct.c_void_p,  # A-F path
                ct.c_void_p,  # start_date
                ct.c_void_p,  # start_time
                ct.c_void_p,  # end_date
                ct.c_void_p,  # end_time
                ct.c_int,     # number_values
                ct.c_int,     # quality_elements
            ),
            restype=ct.c_int
        )

    def __iter__(self) -> Iterator[tuple[str, DLL_Signature]]:
        for function, signature in vars(self).items():
            if not isinstance(signature, DLL_Signature):
                continue
            yield function, signature
   
def get_file_version(dll: ct.CDLL, dss_path: str) -> int:
    dll.hec_dss_getFileVersion.argtypes = (ct.c_char_p,)
    dll.hec_dss_getFileVersion.restype = ct.c_int
    version = dll.hec_dss_getFileVersion(dss_path.encode())

    return int(version)


def get_dll(dss_path: str | Path) -> ct.CDLL:
    dll_default = ct.CDLL(DLL_AVAIL[7])
    version = get_file_version(dll_default, str(dss_path))
    if version == 0:
        raise FileNotFoundError(dss_path)
    logging.info(f"version determined to be {version}")
    
    dll_path = DLL_AVAIL.get(version, None)
    logging.info(f"using dll={dll_path}")
    if dll_path is None:
        raise NotImplementedError(f"DSS File Version {version} not supported")
    dll = ct.CDLL(dll_path)
    api = DLL_API(version)
    logging.info("DLL loaded, applying known API to functions via ctypes")

    for function, signature in api:
        func: ct.CDLL._FuncPtr = getattr(dll, function)
        if signature.argtypes:
            func.argtypes = signature.argtypes
        func.restype = signature.restype
        logging.info(f"api added for {function}")

    return dll