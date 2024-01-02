# DSS interactions like Pandas
Interact with data in DSS files like you're used to. A `pandas` like API for reading and writing data to DSS files. 

Supports:
- DSS version 6
- Reading catalogs
- Reading regular timeseries
- Writing regular timeseries

In development:
- DSS version 7
- Irregular timeseries

## Conceptual Structure

```mermaid
classDiagram
direction LR
    class DSS {
        <<Context Manager>>
        int version
        str source
        read_catalog() ~Catalog~
        read_rts(path~Path~) ~RegularTimeseries~
        __enter__()
        __exit__()
    }
    class pandss {
        <<module>>
        read_catalog(~str~ source)
        read_rts(~str~source, ~Path~path)
    }

    class Catalog {
        itn size
        list~Path~ paths
        __iter__()
    }

    class Path {
        list~str~ parts
        to_string()
    }

    class RegularTimeseries {
        Path path
        str period_type
        str units
        datetime start
        datetime stop
        str frequency
        __iter__()
    }


    DSS -- Catalog
    DSS -- RegularTimeseries
    
    pandss .. DSS

    Catalog --o Path
    Path --* RegularTimeseries


```