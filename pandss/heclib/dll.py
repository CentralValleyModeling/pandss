import logging
from ctypes import CDLL, POINTER, c_char_p, c_int
from pathlib import Path

from .api import DLL_API
from .decorators import silent

DLL_AVAIL = {
    6: None,  # TODO, find applicable DLL
    7: str(Path(__file__).parent / "hecdss.dll"),
}


@silent
def get_file_version(dll: CDLL, dss_path: str) -> int:
    if not Path(dss_path).exists():
        logging.warning("file not found, assuming version 7")
        return 7
    dll.hec_dss_getFileVersion.argtypes = (c_char_p,)
    dll.hec_dss_getFileVersion.restype = c_int
    version = dll.hec_dss_getFileVersion(dss_path.encode())

    return int(version)


@silent
def convert_to_version_7(old_name: str | Path, new_name: str | Path) -> None:
    """Masks `hec_dss_convertToVersion7` DLL function.

    Parameters
    ----------
    new_name : str | Path
        The new DSS file to be created

    Raises
    ------
    FileExistsError
        If new_file already exists
    FileNotFoundError
        If old_file is not found
    """
    if Path(new_name).exists():
        raise FileExistsError(new_name)
    if not Path(old_name).exists():
        raise FileNotFoundError(old_name)
    dll = get_dll_by_version(7)
    old_name = str(old_name).encode("UTF-8")
    new_name = str(new_name).encode("UTF-8")
    result = dll.hec_dss_convertToVersion7(old_name, new_name)
    if result != 0:
        raise RuntimeError(result)


def get_dll_by_version(version: int) -> CDLL:
    dll_path = DLL_AVAIL.get(version, None)
    logging.debug(f"using dll={dll_path}")
    if dll_path is None:
        raise NotImplementedError(f"DSS File Version {version} not supported")
    dll = CDLL(dll_path)
    api = DLL_API(version)
    logging.debug("DLL loaded, applying known API to functions via ctypes")
    dll = api.add_signatures_to_dll(dll)

    return dll


def get_compatible_dll(dss_path: str | Path) -> CDLL:
    dll_default = CDLL(DLL_AVAIL[7])
    version = get_file_version(dll_default, str(dss_path))
    if version == 0:
        raise FileNotFoundError(dss_path)
    logging.debug(f"version determined to be {version}")
    dll = get_dll_by_version(version)

    return dll
