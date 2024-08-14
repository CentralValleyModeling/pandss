# Library Design

This library is designed to act as a consistent API to other DSS interaction libraries. Currently, many other libraries have overlapping but non-comprehensive support of DSS-interactions. For example the following libraries :

| Library        | DSS Versions | Timestamp Types Used for `PER-AVG` |
| -------------- | ------------ | ---------------------------------- |
| pyhecdss       | 6 Only       | `pandas.Periods`                   |
| pydsstools     | 6 and 7      | `datetime.datetime`                |
| hec-dss-python | 7 Only       | Inconsistent                       |

`pandss` utilizes "Engines" to do the heavy lifting of the DSS interactions. Currently, engines are written to engage with the following libraries:

- [pyhecdss](https://github.com/CADWRDeltaModeling/pyhecdss)
- [pydsstools](https://github.com/gyanz/pydsstools)

Engines are currently under development for the following:

- [dss7_ctypes_bindings](https://github.com/CentralValleyModeling/dss7_ctypes_bindings)

Other compatable libraries that are not currently supported include:

- [hec-dss-python](https://github.com/HydrologicEngineeringCenter/hec-dss-python)

## pandss Engine

An Engine must implement the methods defined on `pandss.engines.EngineABC`:

```python
class EngineABC:
    src: Path
    use_units: bool = True
    _catalog: Catalog
    _is_open: bool
    _object: Any
    _create_new: bool

    def __init__(self, src: str | Path, use_units: bool = True): ...

    def open(self) -> Self: ...

    def close(self): ...

    def read_catalog(self) -> Catalog: ...

    def read_rts(self, path: DatasetPath | str) -> RegularTimeseries: ...

    def write_rts(self, path: DatasetPath | str, rts: RegularTimeseries): ...

    @property
    def catalog(self) -> Catalog: ...

    @property
    def is_open(self) -> bool: ...
```
