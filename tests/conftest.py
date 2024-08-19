import datetime
import logging
from os import remove
from os.path import getmtime
from pathlib import Path
from typing import Generator

import pytest

import pandss as pdss


def cleanup(d: Path):
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=1)
    if d.is_file():
        remove(d)
    else:
        for f in d.iterdir():
            if f.is_dir():
                cleanup(f)
            elif datetime.datetime.fromtimestamp(getmtime(f)) < cutoff:
                try:
                    remove(f)
                except PermissionError:
                    logging.warning(f"couldn't clean up old file {f}")


@pytest.fixture(scope="session")
def dss_6() -> Path:
    pdss.module_engine.set("pyhecdss")
    return Path().resolve() / "tests/assets/existing/v6.dss"


@pytest.fixture(scope="session")
def dss_7() -> Path:
    pdss.module_engine.set("pydsstools")
    return Path().resolve() / "tests/assets/existing/v7.dss"


@pytest.fixture(scope="session")
def dss_large() -> Path:
    pdss.module_engine.set("pyhecdss")
    return Path().resolve() / "tests/assets/existing/large_v6.dss"


@pytest.fixture(scope="session")
def assets() -> Path:
    return Path().resolve() / "tests/assets"


@pytest.fixture(scope="session")
def created_dir(assets) -> Generator[Path, None, None]:
    d = Path(assets / "created")
    yield d
    cleanup(d)


@pytest.fixture(scope="function")
def random_name() -> Generator[str, None, None]:
    name = datetime.datetime.now().isoformat(timespec="seconds").replace(":", ".")
    yield name


@pytest.fixture(scope="function")
def temporary_dss(created_dir: Path, random_name: str) -> Generator[Path, None, None]:
    file = Path(created_dir / f"{random_name}.dss")
    yield file
    remove(file)
    for f in file.parent.iterdir():
        if f.stem == file.stem:
            try:
                remove(f)
            except PermissionError:
                logging.warning(f"couldn't clean up {f}")
