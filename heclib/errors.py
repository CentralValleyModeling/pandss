import logging
from ctypes import c_int
from typing import Callable


class HECDSS_ErrorHandler:
    def __init__(self):
        self.severity = {
            -1: ("UNKNOWN", RuntimeError),
            0: ("STATUS_OKAY", print),
            1: ("INFORMATION", logging.info),
            2: ("WARNING", logging.warn),
            3: ("INVALID_ARGUMENT", ValueError),
            4: ("WARNING_NO_WRITE_ACCESS", IOError),
            5: ("WARNING_NO_FILE_ACCESS", IOError),
            6: ("WRITE_ERROR", RuntimeError),
            7: ("READ_ERROR", RuntimeError),
            8: ("CORRUPT_FILE", RuntimeError),
            9: ("MEMORY_ERROR", MemoryError),
        }
        self.error_type = {
            0: "do_nothing",
            1: "user_error",
            2: "data_error",
            3: "process_error",
        }

    def __call__(self, code: c_int) -> tuple[str, Callable]:
        code = int(code)
        msg, action = self.severity.get(code, self.severity[-1])
        return msg, action

    def resolve(self, code: c_int) -> None:
        msg, action = self(code)
        if isinstance(action, Exception):
            raise action(msg)
        else:
            action(msg)


class NoDataError(Exception):
    ...
