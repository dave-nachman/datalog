
from typing import List


class Atom:
    def __init__(self, name, engine, args=None):
        self.name = name
        self.args = args
        self.engine = engine

        self.items = [self]  # match signature of "And" to allow interop between And and Atom

    # as traditional in Datalog, (unknown) variables begin with a capital letter
    def is_variable(self):
        return self.name[0].isupper()

    def is_compound(self):
        return bool(self.args)

    # form a new compound atom out of the args: e.g. atom(L.X, L.Y)
    def __call__(self, *args, **kwargs):
        return Atom(self.name, engine=self.engine, args=args)

    def __repr__(self):
        if self.args is not None:
            return "L." + self.name + "(" + ", ".join(repr(arg) for arg in self.args) + ")"
        else:
            return "L." + self.name

    def __hash__(self):
        return hash(self.name + str(self.args))

    def __eq__(self, other):
        if isinstance(other, Atom):
            return self.name == other.name and self.args == other.args
        else:
            return False

    # dsl syntax: e.g. + L.atom(L.X, L.Y)
    def __pos__(self):
        self.engine.add_fact(self)
        return self

    # dsl syntax: e.g. L.self(L.X, L.Y) & L.other(L.X, L.Y)
    def __and__(self, other):
        return And([self, other])

    # dsl syntax for defining a rule: self <= other
    def __le__(self, other):
        rule = Rule(self, other.items, engine=self.engine)

        # self has been added already as a fact potentially (via "+ " dsl syntax);
        # remove it as it should only serve as the head clause of the rule
        self.engine.facts = [fact for fact in self.engine.facts if fact is not self]

        self.engine.add_rule(rule)
        return rule


class And:
    def __init__(self, items):
        self.items = items

    # dsl syntax: e.g. L.a(L.X, L.Y) & L.b(L.X, L.Y) & L.c(L.X, L.Y)
    def __and__(self, other):
        self.items.append(other)
        return self


class Rule:
    def __init__(self, head: Atom, terms: List[Atom], engine: "Engine"=None):
        self.head = head
        self.terms = terms
        self.engine = engine

    def __repr__(self):
        return f"{repr(self.head)} <= {' & '.join([repr(term) for term in self.terms])}"


def get_unknown_variables(atom: Atom):
    results = []
    if atom.is_variable():
        results.append(atom.name)

    for arg in atom.args or []:
        results = results + get_unknown_variables(arg)

    return results


def unify(a, b):
    if a == b:
        return {a: b}

    if isinstance(a, Atom) and a.is_variable():
        return {a.name: b}

    if isinstance(b, Atom) and b.is_variable():
        return {b.name: a}

    if isinstance(a, Atom) and isinstance(b, Atom) and \
            a.args is not None and \
            b.args is not None and \
            len(a.args) == len(b.args):

        same_predicate = a.name == b.name

        mapped = list(map(lambda p: unify(p[0], p[1]), zip(a.args, b.args)))

        all_unified = all(x is not False for x in mapped)

        if same_predicate and all_unified:
            result = {}
            for x in mapped:
                result = {**result, **x}

            return result

    return False


def substitute(atom, bindings):
    if atom.is_compound():
        args = [substitute(a, bindings) for a in atom.args]
        return Atom(atom.name, args=args, engine=atom.engine)
    elif atom.is_variable():
        # look it up in bindings; if not, substitution fails - return atom name
        return bindings[atom.name] or atom.name
    else:
        return atom.name


def consistent_bindings(b1, b2):
    for key in b1.keys() & b2.keys():
        if b1[key] != b2[key]:
            return False
    return True


def get_bindings(term, engine, next_terms, bindings=None):

    bindings = bindings or {}

    query_results = engine.query(term, always_return_bindings=True)
    new_bindings = []

    for binding_x in query_results:
        if consistent_bindings(binding_x, bindings):
            if next_terms:
                # recursively build up bindings by calling get_bindings on the next term
                for binding_y in get_bindings(next_terms[0], engine, next_terms[1:], binding_x):
                    new_bindings.append({**bindings, **binding_x, **binding_y})

            else:
                new_bindings.append({**bindings, **binding_x})

    return new_bindings


def derive_facts(rule, engine):

    bindings = get_bindings(rule.terms[0], engine, rule.terms[1:])

    existing_facts_len = len(engine.facts)

    for binding in bindings:
        new_fact = substitute(rule.head, binding)
        engine.add_fact(new_fact, skip_propagate=True)

    # if there were new facts added, conduct another round in case more derivations can be made using the new facts
    if len(engine.facts) != existing_facts_len:
        derive_facts(rule, engine)


class Engine:
    def __init__(self):
        self.facts = []
        self.rules = []

    def __getattr__(self, item):
        return Atom(item, engine=self)

    def add_fact(self, fact: Atom, skip_propagate=False):
        if fact not in self.facts:
            self.facts.append(fact)

        # when adding a fact (other than as part of the propagate step), we need to re-propagate each rule
        if not skip_propagate:
            for rule in self.rules:
                derive_facts(rule, self)

    def add_rule(self, rule: Rule):
        rule.engine = self
        self.rules.append(rule)

        # Propagate the rule, adding facts to the engine
        derive_facts(rule, self)

    def query(self, query: Atom, always_return_bindings=None):
        for fact in self.facts:
            result = unify(fact, query)
            if result is not False:
                if result == {}:
                    yield {}
                else:
                    # return only string keys, which represent bound variables
                    r = {k: v for k, v in result.items() if isinstance(k, str)}

                    if not always_return_bindings and r == {}:
                        yield True
                    else:
                        yield r
