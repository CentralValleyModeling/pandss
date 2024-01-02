from .. import suppress_stdout_stderr


def must_be_open(method):
    def works_on_open_file(obj, *args, **kwargs):
        if obj.open is False:
            raise IOError(f"file must be open to call {method}")
        else:
            return method(obj, *args, **kwargs)

    return works_on_open_file


def silent(method):
    def silent_method(*args, **kwargs):
        with suppress_stdout_stderr():
            return method(*args, **kwargs)

    return silent_method
