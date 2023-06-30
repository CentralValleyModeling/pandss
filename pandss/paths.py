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

def make_temp_args(items: tuple, new_loc: Path) -> tuple:
    def inner(items, new_loc):
        for v in items:
            if is_path_like(v):
                logging.info(f'creating temp of {v} in {new_loc}')
                v = create_temp(v, new_loc)
            yield v
    
    return tuple(inner(items, new_loc))
    
def make_temp_kwargs(items: dict, new_loc: Path) -> dict:
    def inner(items, new_loc):
        for k, v in items.items():
            if is_path_like(v):
                logging.info(f'creating temp of {v} in {new_loc}')
                v = create_temp(v, new_loc)
            yield k, v

    return dict(inner(items, new_loc))

def use_temp_paths(func):
    def runner(*args, **kwargs):
        with tempfile.TemporaryDirectory(dir=Path.home()) as temp_dir:
            safe_args = make_temp_args(args, temp_dir)
            safe_kwargs = make_temp_kwargs(kwargs, temp_dir)
            return func(safe_args, safe_kwargs)
        
    return runner
