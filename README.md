# ![](logo.png) A lambda calculus interpreter 

![GitHub](https://img.shields.io/github/license/smallcluster/Lcalc?logo=Github)

![](recursive.gif)

λcalc is a untyped lambda calculus interpreter written in pure Python.


# Features

- Haskell ('\\') or utf8 lambda ('λ') notation
- Leftmost-outermost Beta and/or Eta reduction
- Automatic support for recursively defined terms by using fixed point combinators (**extremely slow**)
- Built in support for Church numerals, tuples and lists encoding
- Show/hide reduction steps with statistics (number of reductions and evaluation time)
- Export a term and it's intermediate sub terms during evaluation to latex as a tree with the "forest" package

Free variables in terms have to be defined first to use them. Furthermore, they are captured by value.

# Requirements

Python 3, tested on python 3.8 .

# Launching

## Interactive mode

```
python lcalc.py
```
type ``help;`` to show the list of commands and the basic syntax.

## Execute script

```
python lcalc.py "path_to_script.lc"
```

# Libraries

To import a library just run/write:
```
import "path_to_script.lc";
```
Default libraries:
- ``combinators.lc`` : some fixed point combinators
- ``booleans.lc`` : definition of true/false and conditional structures
- ``numbers.lc`` : some functions for natural numbers (add, sub, pred, ...)
- ``tuples.lc`` : some functions for tuples
- ``lists.lc`` : some functions for lists

# ⚠️ Known issues

## Crashs

Due to the way Python implements its recursive function call stack, big terms (trees with a large depth) will provoke the Python process to panic (Ex: printing a number larger than 10000), resulting in a segmentation fault. The only solution, for now, is to use a stackless Python interpreter (Ex: Stackless Python).

## Speed

This is a *naive* lamda calculus interpreter: the parser generates the AST then evals it by beta/eta reducing its tree representation. It mimics how you would do it with a pen and paper, and to be honest, it's quite slow! Furthermore, Python isn't famous for its speed...

However, it is written in pure Python and only use a few modules from the standard Python library. Wich means it works really well with [the GraalPy interpreter](https://github.com/oracle/graalpython) (a Python 3 implementation backed by the GraalVM JVM, an optimized JVM).
There is approximately a 10x speed improvement using [GraalPy](https://github.com/oracle/graalpython) to run Lcalc.

For example, on a Ryzen 7 3700X, `print fact 5;` (recursion using Turing's fixed point combinator) took ~1h 20min with CPython versus ~7min 30s with [GraalPy](https://github.com/oracle/graalpython).

