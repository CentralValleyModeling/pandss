# Tutorials

These tutorials are written to get new users up and running with `pandss`. It might be neccesary for users to understand some DSS concepts to fully understand what they are doing with `pandss`. Where appropriate, USACE HEC-DSS documentation is linked.

## Installation

Conda is the preferred package manager for `pandss` due to certain preferred dependencies. In the future `pandss` may be distributed via PyPI, but not as of now.

### Conda

```powershell
conda install pandss -c dwr-cvm
```

## Basic Usage

The library is mostly used to interact with existing DSS files, but it is possible to create DSS files from scratch.

```python
import pandss as pdss

# Specify the file to be created
file = "new.dss"

# The data to be written to file
data = dict(
    path="/DOCS/MONTH_DAYS/TUTORIALS//1MON/2024/",
    values=(31, 28, 31),
    dates=("1921-01-31", "1921-02-28", "1921-03-31"),
    period_type="PER-CUM",
    units="days",
    interval="1MON",
)

# Create the RegularTimeseries object
rts = pdss.RegularTimeseries.from_json(data)

# Write the data to a file
with pdss.DSS(file) as dss:
    dss.write_rts(rts.path, rts)
```

Usually, you will have a DSS file handy so you will not need to create the RegularTimeseries objects from scratch.

```python
import pandss as pdss

rts = pdss.read_rts("existing.dss", "/DOCS/MONTH_DAYS/TUTORIALS//1MON/2024/")
```

Once you have the data read, you can convert it to a `pandas.DataFrame` and use your typical data analysis tools.

```python
df = rts.to_frame()  # Convert to DataFrame
```
