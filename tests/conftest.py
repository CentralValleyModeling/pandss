import logging
from os import remove
from pathlib import Path
from random import choice
from string import ascii_letters
from typing import Generator

import pytest

import pandss as pdss

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture()
def dss_6() -> Path:
    pdss.module_engine.set("pyhecdss")
    return Path().resolve() / "tests/assets/existing/v6.dss"


@pytest.fixture()
def dss_7() -> Path:
    pdss.module_engine.set("pydsstools")
    return Path().resolve() / "tests/assets/existing/v7.dss"


@pytest.fixture()
def dss_large() -> Path:
    pdss.module_engine.set("pyhecdss")
    return Path().resolve() / "tests/assets/existing/large_v6.dss"


@pytest.fixture()
def assets() -> Path:
    return Path().resolve() / "tests/assets"


@pytest.fixture()
def created_dir(assets) -> Path:
    return assets / "created"


@pytest.fixture(scope="function")
def random_name() -> Generator[str, None, None]:
    name = "".join(choice(ascii_letters) for _ in range(10))
    yield f"{name}.dss"


@pytest.fixture(scope="function")
def temporary_dss(created_dir: Path, random_name: str) -> Generator[Path, None, None]:
    file = Path(created_dir / random_name)
    yield file
    remove(file)
    for f in file.parent.iterdir():
        if f.stem == file.stem:
            try:
                remove(f)
            except PermissionError:
                logging.warning(f"couldn't clean up {f}")
