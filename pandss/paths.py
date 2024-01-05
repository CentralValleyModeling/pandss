from dataclasses import dataclass, fields
from typing import Self


@dataclass(kw_only=True, frozen=True, slots=True, eq=True)
class DatasetPath:
    a: str
    b: str
    c: str
    d: str
    e: str
    f: str

    @staticmethod
    def from_str(path: str) -> Self:
        a, b, c, d, e, f = path.strip("/").split("/")
        return DatasetPath(a=a, b=b, c=c, d=d, e=e, f=f)

    def __str__(self):
        kwargs = {f.name: getattr(self, f.name) for f in fields(self)}
        return "/{a}/{b}/{c}/{d}/{e}/{f}/".format(**kwargs)

    def items(self):
        for f in fields(self):
            yield f.name, getattr(self, f.name)
    
    def __iter__(self):
        for f in fields(self):
            yield getattr(self, f.name)