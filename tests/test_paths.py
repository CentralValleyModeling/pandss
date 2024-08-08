import pytest
from pytest import FixtureRequest

import pandss as pdss


def test_partial_construction():
    p = pdss.DatasetPath(b="FOO")
    assert p.b == "FOO"
    assert p.c == ".*"
    assert str(p) == "/.*/FOO/.*/.*/.*/.*/"


@pytest.mark.parametrize("dss", ("dss_6", "dss_7"))
def test_wildcard(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str(r"/CALSIM/.*/.*/.*/.*/.*/")
    assert p.has_wildcard is True

    with pdss.DSS(dss) as dss_obj:
        collection = dss_obj.resolve_wildcard(p)
        collection = collection.collapse_dates()

    assert isinstance(collection, pdss.DatasetPathCollection)
    expected = sorted(
        (pdss.DatasetPath(b="PPT_OROV"), pdss.DatasetPath(b="MONTH_DAYS"))
    )
    collection = sorted(collection)
    for L, R in zip(collection, expected):
        assert L.b == R.b

    assert len(collection) == 3


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_replace_bad_wildcard(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    blank = pdss.DatasetPath.from_str(r"/*/////*/")
    star = pdss.DatasetPath.from_str(r"/.*/.*/.*/.*/.*/.*/")
    with pdss.DSS(dss) as dss:
        blank = dss.resolve_wildcard(blank)
        star = dss.resolve_wildcard(star)
    assert blank == star


@pytest.mark.parametrize("dss", ("dss_6", "dss_7"))
def test_warn_findall_if_wildcard_in_set(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    star = pdss.DatasetPath.from_str(r"/*/*/*/*/*/*/")
    with pdss.DSS(dss) as dss:
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
