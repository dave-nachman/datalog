# datalog

This is a WIP implementation of [datalog](https://en.wikipedia.org/wiki/Datalog) in Python, in the form of an *embedded DSL*. The DSL is designed to provide as a syntax similar to traditional Datalog, while operating within the constraints of Python's language features:

```python
L = Engine() # L is mnemonic for "Logic"

+ L.person(L.dave) # Add the fact Dave is a person.

+ L.animal(L.X) <= L.person(L.X) # Add the rule "X is an animal if X is a person"
  
next(L.query(L.animal(L.Result))) == {"Result": L.dave} # Get the first answer for the query what X is an animal

```

Alternatively, this could be written without the DSL:

```python
L = Engine()
L.add_fact(L.person(L.dave))
L.add_rule(Rule(L.animal(L.X), [L.person(L.X)]))
next(L.query(L.animal(L.Result))) == {"Result": L.dave} 

```

This implementation of datalog uses a bottoms up (or forward chaining) "naive evaluation" strategy. Bottoms up means that it derives new facts by applying rules, as opposed to searching backwards (or downwards) from a goal, while the "naive evaluation" approach isn't applying any optimizations around preventing facts from being recomputed.

### Goals

My primary goal was to learn more about Datalog, and it's possible implementation strategries, through implementing it. 

In addition, I'm interested in the potential for embedding traditional logic programming languages within a general purpose programming language ([core.logic](https://github.com/clojure/core.logic) in Clojure is a good example of this). As part of this, I wanted to explore ways that Datalog clauses could be expressed as an embedded DSL in Python - trying to figure out how to mirror traditional Datalog syntax as much as possible.

### Status

This is an alpha WIP. There are some important missing features such as "or" clauses, negation, and support for numbers, lists, and sets. In addition I'd like to explore switching to more efficient evaluation strategies, such as "semi-naive evaluation" and further optimizations.

### Syntax overview

Atoms and variables are introduced through attribute lookup on an instance of an Engine

```python
L.X               # the variable X
L.dave            # an atom
L.person(L.dave)  # a compound term
```

A rule is formed using a `<=`
```python
L.animal(X) <= L.person(X)
```

An atom, variable is added to the engine's dataset using a plus sign as a prefix
```python
+ L.person(L.dave) # Added to the engine's dataset
L.person(L.dave)   # No effect
```

### Examples

Based on https://en.wikipedia.org/wiki/Datalog#Example

```python

L = Engine()

+ L.parent(L.bill, L.mary)
+ L.parent(L.mary, L.john)

+ L.ancestor(L.X, L.Y) <= L.parent(L.X, L.Y)
+ L.ancestor(L.X, L.Y) <= L.parent(L.X, L.Z) & L.ancestor(L.Z, L.Y) # & is used in place of traditional comma

query = list(L.query(L.ancestor(L.bill, L.X)))

assert({"X": L.mary} in query)
assert ({"X": L.john} in query)
```

### Resources

- "The Essence of Datalog", https://dodisturb.me/posts/2018-12-25-The-Essence-of-Datalog.html
- http://pages.cs.wisc.edu/~paris/cs838-s16/lecture-notes/lecture8.pdf
