
from datalog.main import Engine, Rule


def test_equality():
    L = Engine()
    + L.person(L.bob)

    query = list(L.query(L.person(L.bob)))
    assert(query == [True])


def test_simple_matching():
    L = Engine()
    + L.person(L.bob)
    + L.person(L.charlie)

    query = list(L.query(L.person(L.X)))

    assert(query == [{"X": L.bob}, {"X": L.charlie}] or query == [{"X": L.charlie}, {"X": L.bob}])


def test_simple_rule():
    L = Engine()
    + L.person(L.bob)

    L.add_rule(Rule(L.thing(L.X), [L.person(L.X)], engine=L))

    query = list(L.query(L.thing(L.X)))

    assert(query == [{"X": L.bob}])


def test_dsl_rule():
    L = Engine()

    + L.parent(L.david, L.alex)
    + L.parent(L.alex, L.tony)

    + L.grandparent(L.X, L.Y) <= L.parent(L.X, L.Z) & L.parent(L.Z, L.Y)

    query = list(L.query(L.grandparent(L.X, L.Y)))

    assert(query == [{'X': L.david, 'Y': L.tony}])


# From https://en.wikipedia.org/wiki/Datalog#Example
def test_ancestor():
    L = Engine()

    + L.parent(L.bill, L.mary)
    + L.parent(L.mary, L.john)

    + L.ancestor(L.X, L.Y) <= L.parent(L.X, L.Y)
    + L.ancestor(L.X, L.Y) <= L.parent(L.X, L.Z) & L.ancestor(L.Z, L.Y)

    query = list(L.query(L.ancestor(L.bill, L.X)))

    assert({"X": L.mary} in query)
    assert ({"X": L.john} in query)


def test_greatgrandparent_rule():
    L = Engine()

    + L.grandparent(L.X, L.Y) <= L.parent(L.X, L.Z) & L.parent(L.Z, L.Y)
    + L.greatgrandparent(L.X, L.Y) <= L.grandparent(L.X, L.Z) & L.parent(L.Z, L.Y)

    + L.parent(L.david, L.alex)
    + L.parent(L.alex, L.tony)
    + L.parent(L.tony, L.mary)

    query = list(L.query(L.greatgrandparent(L.X, L.Y)))

    assert(query == [{'X': L.david, 'Y': L.mary}])


# based on https://stackoverflow.com/questions/47043937/what-is-the-difference-between-naive-and-semi-naive-evaluation/49655358#49655358
def test_reachable():
    L = Engine()

    + L.link(L.a, L.b)
    + L.link(L.b, L.c)
    + L.link(L.c, L.c)
    + L.link(L.c, L.d)
    + L.link(L.d, L.e)

    + L.reachable(L.X, L.Y) <= L.link(L.X, L.Y)
    + L.reachable(L.X, L.Y) <= L.link(L.X, L.Z) & L.reachable(L.Z, L.Y)

    results = list(L.query(L.reachable(L.X, L.e)))
    assert len(results) == 4
