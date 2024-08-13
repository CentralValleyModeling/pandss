from itertools import product

import pytest
from pytest import FixtureRequest

import pandss as pdss


def test_partial_construction():
    p = pdss.DatasetPath(b="FOO")
    assert p.b == "FOO"
    assert p.c == ".*"
    assert str(p) == "/.*/FOO/.*/.*/.*/.*/"


def test_strange_eq():
    paths = {pdss.DatasetPath(b="A"), pdss.DatasetPath(b="B")}
    dsp = pdss.DatasetPathCollection(paths=paths)
    assert dsp == dsp
    assert dsp == paths
    assert paths == dsp
    assert dsp == [p for p in paths]
    assert [p for p in paths] == dsp
    assert dsp != paths.pop()


def test_set_operations():
    dsp_1 = pdss.DatasetPathCollection(
        paths={
            pdss.DatasetPath(b="A"),
            pdss.DatasetPath(b="B"),
        }
    )

    dsp_2 = pdss.DatasetPathCollection(
        paths={
            pdss.DatasetPath(b="B"),
            pdss.DatasetPath(b="C"),
        }
    )
    add = dsp_1 + dsp_2
    sub = dsp_1 - dsp_2
    _and = dsp_1 & dsp_2
    _or = dsp_1 | dsp_2
    assert len(add) == 3
    assert len(add) == len(_or)
    assert len(sub) == 1
    assert sub.paths.pop() == pdss.DatasetPath(b="A")
    assert len(_and) == 1
    assert _and.paths.pop() == pdss.DatasetPath(b="B")


def test_swapped_operands():
    dsp_collection = pdss.DatasetPathCollection(
        paths={
            pdss.DatasetPath(b="A"),
            pdss.DatasetPath(b="B"),
        }
    )

    set_collection = {
        pdss.DatasetPath(b="B"),
        pdss.DatasetPath(b="C"),
    }
    add_1 = dsp_collection + set_collection
    sub_1 = dsp_collection - set_collection
    _and_1 = dsp_collection & set_collection
    _or_1 = dsp_collection | set_collection

    add_2 = set_collection + dsp_collection
    sub_2 = set_collection - dsp_collection
    _and_2 = set_collection & dsp_collection
    _or_2 = set_collection | dsp_collection

    assert add_1 == add_2
    assert sub_1 == sub_2
    assert _and_1 == _and_2
    assert _or_1 == _or_2


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


@pytest.mark.parametrize("dss", ("dss_6", "dss_7"))
def test_wildcard_on_read_multiple(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    p = pdss.DatasetPath.from_str(r"/.*/TESTING/.*/.*/.*/.*/")
    assert p.has_wildcard is True

    i = None
    for i, rts in enumerate(pdss.read_multiple_rts(dss, p)):
        assert isinstance(rts, pdss.RegularTimeseries)
    assert i == 0

    dsp = pdss.DatasetPathCollection(paths={p})
    i = None
    for i, rts in enumerate(pdss.read_multiple_rts(dss, dsp)):
        assert isinstance(rts, pdss.RegularTimeseries)
    assert i == 0


@pytest.mark.parametrize("dss", ("dss_6", "dss_7", "dss_large"))
def test_replace_bad_wildcard(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    blank = pdss.DatasetPath.from_str(r"/*/////*/")
    star = pdss.DatasetPath.from_str(r"/.*/.*/.*/.*/.*/.*/")
    assert blank == star
    with pdss.DSS(dss) as dss_obj:
        blank = dss_obj.resolve_wildcard(blank)
        star = dss_obj.resolve_wildcard(star)
    assert blank == star


@pytest.mark.parametrize("dss", ("dss_6", "dss_7"))
def test_warn_findall_if_wildcard_in_set(dss, request: FixtureRequest):
    dss = request.getfixturevalue(dss)
    star = pdss.DatasetPath.from_str(r"/*/*/*/*/*/*/")
    with pdss.DSS(dss) as dss:
        catalog = dss.read_catalog()
        _ = catalog.resolve_wildcard(star)
        catalog = catalog.collapse_dates()
        with pytest.raises(pdss.errors.WildcardError):
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


def test_matching_and_equality():
    abc = pdss.DatasetPath(a="A", b="B", c="C")
    ab_ = pdss.DatasetPath(a="A", b="B")
    a_c = pdss.DatasetPath(a="A", c="C")
    _bc = pdss.DatasetPath(b="B", c="C")

    wildcards = [ab_, a_c, _bc]
    for w in wildcards:
        assert abc != w
        assert w != abc
        assert abc.matches(w)
        assert w.matches(abc)

    for L, R in product(wildcards, wildcards):
        if L is R:
            continue
        assert L != R
        assert R != L
        assert not L.matches(R)
        assert not R.matches(L)

    for pattern in wildcards:
        assert pattern == pattern
        assert pattern.matches(pattern)

    assert abc == abc
    assert abc.matches(abc)

    L = pdss.DatasetPath(a="Foo.*")
    R = pdss.DatasetPath(a=".*Bar")
    C = pdss.DatasetPath(a="FooBar", b="Anything")
    for side in (L, R):
        assert C.matches(side)
        assert side.matches(C)
        assert C != side
        assert side != C
    assert L != R
    assert not L.matches(R)
    assert R != L
    assert not R.matches(L)
