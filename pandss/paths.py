from typing import Union, TypeVar
from pathlib import Path
import tempfile
import shutil
import logging


PathLike = TypeVar('PathLike', bound=Union[Path, str])

def is_path_like(p) -> bool:
    return isinstance(p, (Path, str))

def create_temp(p: PathLike, new_loc: Path) -> Path:
    temp_f = tempfile.mktemp(dir=new_loc, suffix=p.suffix)
    shutil.copy(p, temp_f)

    return temp_f
