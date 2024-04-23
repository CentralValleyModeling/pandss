import pytest

import pandss as pdss


def test_partial_construction():
    p = pdss.DatasetPath(b="FOO")
    assert p.b == "FOO"
    assert p.c == ".*"
    assert str(p) == "/.*/FOO/.*/.*/.*/.*/"


def test_wildcard_6(dss_6):
    p = pdss.DatasetPath.from_str(r"/CALSIM/.*/.*/.*/.*/.*/")
    assert p.has_wildcard is True

    with pdss.DSS(dss_6) as dss:
        collection = dss.resolve_wildcard(p)
        collection = collection.collapse_dates()

    assert isinstance(collection, pdss.DatasetPathCollection)
    assert collection.paths == {
        pdss.DatasetPath.from_str("/CALSIM/PPT_OROV/PRECIP//1MON/L2020A/"),
        pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY/*/1MON/L2020A/"),
    }

    assert len(collection) == 2


def test_wildcard_7(dss_7):
    p = pdss.DatasetPath.from_str(r"/CALSIM/.*/.*/.*/.*/.*/")
    assert p.has_wildcard is True
    with pdss.DSS(dss_7) as dss:
        collection = dss.resolve_wildcard(p)
        collection = collection.collapse_dates()
    assert isinstance(collection, pdss.DatasetPathCollection)
    assert collection.paths == {
        pdss.DatasetPath.from_str("/CALSIM/PPT_OROV/PRECIP//1Month/L2020A/"),
        pdss.DatasetPath.from_str("/CALSIM/MONTH_DAYS/DAY/*/1Month/L2020A/"),
    }

    assert len(collection) == 2


def test_replace_bad_wildcard(dss_6):
    blank = pdss.DatasetPath.from_str(r"/*/////*/")
    star = pdss.DatasetPath.from_str(r"/.*/.*/.*/.*/.*/.*/")
    with pdss.DSS(dss_6) as dss:
        blank = dss.resolve_wildcard(blank)
        star = dss.resolve_wildcard(star)
    assert blank == star


def test_warn_findall_if_wildcard_in_set(dss_6):
    star = pdss.DatasetPath.from_str(r"/*/*/*/*/*/*/")
    with pdss.DSS(dss_6) as dss:
        catalog = dss.read_catalog()
        catalog = catalog.collapse_dates()
        with pytest.warns(Warning):
            catalog.resolve_wildcard(star)


def test_path_ordering():
    a = pdss.DatasetPath.from_str(r"/A/A/A/A/A/A/")
    z = pdss.DatasetPath.from_str(r"/Z/Z/Z/Z/Z/Z/")
    assert z > a
    ab = pdss.DatasetPath.from_str(r"/A/A/A/A/A/B/")
    ba = pdss.DatasetPath.from_str(r"/B/A/A/A/A/A/")
    assert ba > ab
    sorted_paths = sorted([ba, ab, z, a])
    for L, R in zip(sorted_paths, [a, ab, ba, z]):
        assert L == R
    collection = pdss.DatasetPathCollection(paths=set((z, a, ab, ba)))
    list_collection = list(collection)
    for L, R in zip(list_collection, [a, ab, ba, z]):
        assert L == R


def test_bad_str():
    with pytest.raises(pdss.errors.DatasetPathParseError):
        pdss.DatasetPath.from_str("/A/")


def test_optional_formatting():
    strs = (
        "A/B/C/D/E/F",
        "/A/B/C/D/E/F",
        "/A/B/C/D/E/F/",
        "A/B/C//E/F",
        "/A/B/C//E/F",
        "/A/B/C//E/F/",
    )
    for s in strs:
        p = pdss.DatasetPath.from_str(s)
        assert isinstance(p, pdss.DatasetPath)
        assert p.a == "A"
        assert p.f == "F"
