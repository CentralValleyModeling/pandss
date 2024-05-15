# How To

## How do I read data from a DSS file?

```python
import pandss as pdss

file = "path/to/file.dss"
with pdss.DSS(file) as dss:
    # Read the catalog of the DSS file
    catalog = dss.read_catalog()
    
    # For this example, we are just grabbing the first path from the catalog
    path = catalog.paths.pop()

    # Get the data corresponding to that path from the DSS
    rts = dss.read_rts(path)
```

## How do I read a lot of data from a DSS file?

```python
import pandss as pdss

file = "path/to/file.dss"
# Use regular expressions that conform to the python re module to match paths
path = pdss.DatasetPath(b=".*", c="C")
for rts in pdss.read_multiple_rts(file, path):
    # Do something with the rts
    print(rts.values[0:10])
```

## How do I combine many datasets to a single DataFrame?

```python
import pandss as pdss
import pandas as pd

file = "path/to/file.dss"
path = pdss.DatasetPath(b=".*", c="C")

# Create the generator, this will keep the DSS file open between reads
generator = (
    rts.to_frame() 
    for rts in pdss.read_multiple_rts(file, path)
)
# Use the generator in pandas concat
df = pd.concat(generator, axis=1)
```

## How do I write data to a DSS file?

```python
import pandss as pdss

# Using a RegularTimeseries object that was created somehow...
rts = pdss.RegularTimeseries(...)

# Open a DSS file, which can be new or existing
file = "path/to/file.dss"
with pdss.DSS(file) as dss:
    # Write the data in the rts to the DSS file
    # This will overwrite data at the datasetpath if it existed already
    rts = dss.write_rts(rts.path, rts)
```

## How can I copy data between two DSS files?

```python
import pandss as pdss

# Specify the dss files to copy from/to
old_dss = "old.dss"
new_dss = "new.dss"

# Specify the names that will be read and written. 
old_paths = (
    "/DOCS/MONTH_DAYS/DAY//1MON/2024/",
    "/DOCS/LOCATION/PRECIP//1MON/2024/",
)
new_paths = (
    "/DOCS/MONTH_DAYS/DAY//1MON/2024/",  # Same name ok
    "/DOCS/LOCATION_NEW/PRECIP//1MON/2024/",  # Changed name ok too
)

# Copy data
pdss.copy_multiple_rts(
    old_dss, 
    new_dss, 
    zip(p_old, p_new),
)
```

## How can I analyze the data in a DSS file?

```python
import pandss as pdss

file = "path/to/file.dss"
path = "/DOCS/LOCATION/PRECIP//1MON/2024/"
with pdss.DSS(file) as dss:
    # Get the data corresponding to that path from the DSS
    rts = dss.read_rts(path)

# Convert the data to a pandas DataFrame and use your regular tools
df = rts.to_frame()
```
