from pathlib import Path
from random import choice
from string import ascii_letters

import pytest

import pandss as pdss


@pytest.fixture()
def dss_6():
    pdss.module_engine.set("pyhecdss")
    return Path().resolve() / "tests/assets/existing/v6.dss"


@pytest.fixture()
def dss_7():
    pdss.module_engine.set("pydsstools")
    return Path().resolve() / "tests/assets/existing/v7.dss"


@pytest.fixture()
def dss_large():
    pdss.module_engine.set("pyhecdss")
    return Path().resolve() / "tests/assets/existing/large_v6.dss"


@pytest.fixture(scope="function")
def random_name():
    name = "".join(choice(ascii_letters) for _ in range(10))
    yield name
