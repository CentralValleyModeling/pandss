# DSS interactions like Pandas
Interact with data in DSS files like you're used to. A `pandas` like API for reading and writing data to DSS files. 

## Supports:

- DSS version 6, 7
- Reading catalogs
- Reading regular timeseries

In development:

- Writing regular timeseries
- Irregular timeseries

## Examples
### Read Catalog

Read the file using the module-level utility function:
```
import pandss as pdss

# Read the catalog and close the HEC-DSS file immediately
file = "example.dss"
catalog = pdss.read_catalog(file)
```

Read the cata log using the DSS context manager:
```
import pandss as pdss

file = "example.dss"
with pdss.DSS(file) as dss:
    # Read the catalog, but the HEC-DSS file remains open
    catalog = dss.read_catalog()
```
### Read Regular Timeseries

Read data, knowing the full name ahead of time:

```
import pandss as pdss

file = "example.dss"
# You do not need to specify the D-part
path = pdss.DatasetPath.from_str("/A/B/C//E/F/")
regular_time_series = pdss.read_rts(file, path)
```

Read data, with wildcards:

```
import pandss as pdss

file = "example.dss"
# Use regular expressions that conform to the python re module to match paths
path = pdss.DatasetPath.from_str("/A/.*/C//E/F/")
for regular_time_series in pdss.read_multiple_rts(file, path):
    ...
```

Read all data from a DSS file:

```
import pandss as pdss

file = "example.dss"
with pdss.DSS(file) as dss:
    catalog = dss.read_catalog()
    for regular_time_series in dss.read_multiple_rts(catalog):
        ...
```

Copy data between DSS files:

```
old_dss = "old.dss"
old_paths = (
    "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",
    "/CALSIM/PPT_OROV/PRECIP//1MON/L2020A/",
)
new_dss = "new.dss"
new_paths = (
    "/CALSIM/MONTH_DAYS/DAY//1MON/L2020A/",  # Same name ok
    "/CALSIM/PPT_OROV_NEW/PRECIP//1MON/L2020A/",  # Changed name ok too
)
pdss.copy_multiple_rts(
    old_dss, 
    new_dss, 
    zip(p_old, p_new),
)
```

## Objects and their attributes
### `pdss.RegularTimeseries`

This object contains the information stored in a single Regular Timeseries in a DSS file. The values and dates are stored in `numpy.array` objects, and the other attributes are saved on the object. Some attributes are not supported by all engines. 

```
class RegularTimeseries:
    path: DatasetPath
    values: NDArray[float64]
    dates: NDArray[datetime64]
    period_type: str
    units: str
    interval: int

    # methods
    def to_frame() -> pandas.DataFrame:
        ...
```

### `pdss.Catalog`

This object represents the collection of all paths in a DSS file. It is a subclass of `pdss.DatasetPathCollection` which has the additional attribute of `src`. It is searchable via the `findall` method.

```
class Catalog:
    src: Path
    paths: set(DatasetPath)

    # methods
    @classmethod
    def from_strs() -> Catalog:
        ...
    @classmethod
    def from_frame() -> Catalog:
        ...
    def findall() -> DatasetPathCollection:
        ...
```

### `pdss.DatasetPath`

This object represents the path to a single dataset in a DSS file. It is made up of A-F parts. Each of the parts may contain regular expressions that could be used to search a collection containing many `DatasetPath` objects for matching patterns. Two attributes on this object determine if the object uses wildcards:

- `has_wildcard`: `True` if any part (other than the D part) uses wildcards, `False` otherwise.
- `has_any_wildcard`: `True` if any part uses wildcards, `False` otherwise.

```
class DatasetPath:
    a: str
    b: str
    c: str
    d: str
    e: str
    f: str

    # properties
    @property
    def has_wildcard() -> bool:
        ...
    @property
    def has_any_wildcard() -> bool:
        ... 
    
    # methods
    def drop_date() -> DatasetPath:
        ...
```