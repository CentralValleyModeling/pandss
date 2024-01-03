from dataclasses import dataclass
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
        parts = ("a", "b", "c", "d", "e", "f")
        kwargs = {attr: getattr(self, attr) for attr in parts}
        return "/{a}/{b}/{c}/{d}/{e}/{f}/".format(**kwargs)
