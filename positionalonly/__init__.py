"""
positionnal only arguments/parameters
=====================================

Module to fake positional only arguments (pep 497, Draft).

Let's take the following function as example:

```python
def diff(left, right, context=3):
    '''print the diff between `left` and `right` with `context`
    '''
    ...
    
```

`right` and `left` are now part of the API, and users
may decide to use `diff(left=str1, right=str1)`, blocking
api changes, so you can't change the names of the parameters,
to for example `def diff(old, new, context=3)` without using
the C-api.

This module provide a decorator @positionalonly to make all the
default-less parameters of your function positional only, so you
can write:

    @positionalonly
    def diff(left, right, context=3):
        ...

Usingit like will raise a TypeError, and the function
signature will use the positional only argument syntax
with the `/` of pep 497.


    >>> diff(right="bar", left="foo")
    TypeError: The following parameters of `diff` are positional only.
    They were used as keywords arguments:
     - 'right' ('bar') should be in 2nd position
     - 'left' ('foo') should be in 1st position

    >>> help(diff)
    Help on function diff in module __main__:

    diff(left, right, /, context=3)



Advance usage
=============

By default `positionalonly` will make the limit between positional-only and the
rest of the arguments just before the first argument with default. You can
tweek this behavior by passing an integer as parameter indicating the number of
argument to make positional-only:

    >>> @positionalonly(3)
    ... def diff(old, new, context=3)
    ...     pass

    >>> signature(diff)
    diff(left, right, context=3, /)


    >>> @positionalonly(1)
    ... def diff(old, new, context=3)
    ...     pass

    >>> signature(diff)
    diff(left, /, right, context=3)

If you are too lazy to count, or are afraid of misscounting, `positionalonly`
will also decide to put the limit to the first argument which default value is
`positionalonly` itself.


    >>> @positionalonly
    ... def diff(old, new, end=positionalonly, context=3)
    ...     pass

    >>> signature(diff)
    diff(left, right, /, context=3)

    >>> pos_or_kw
    >>> @positionalonly
    ... def diff(old, start=pos_or_kw, context=3)
    ...     pass

    >>> signature(diff)
    diff(left, /, right, context=3)



Reasons to use positional only
==============================

Naming of argument, and in particular the function
signature can be helfull for tab completion, and static analysis
to understand the code. While posistional only is usable using
`*args` it hides all this information both from the human and
the computer.

The default behavior of Python, is to make agument by dafult,
positional an keyword. 

This fact often prevent the developer from changing the
name without breaking the API. 

This also prevent arbitrary `**kwargs` keys as they are
be taken by "positionaly or keyword" arguments.

"""

version_info = (0, 0, 1)
__version__ = '.'.join(str(x) for x in version_info)

import inspect
import functools

from math import inf
from types import FunctionType
from inspect import Signature, Parameter
from functools import wraps
from collections import defaultdict

POSITIONAL_OR_KEYWORD = inspect._ParameterKind.POSITIONAL_OR_KEYWORD
POSITIONAL_ONLY = inspect._ParameterKind.POSITIONAL_ONLY
_empty = inspect._empty


def positionalonly(*args):
    """
    Make arguments of a function positional only and raise if they are passed
    as keyword arguments.

    """
    if len(args) != 1:
        raise TypeError('posonly takes at most 1 positional only argument')
    n_or_f = args[0]
    if n_or_f is inf or type(n_or_f) is int:
        return functools.partial(_posonly, n_or_f)
    else:
        return _posonly(inf, n_or_f)

# make positional only a positional only function !
positionalonly.__signature__ = Signature([Parameter('number_or_function',
                                                    inspect._ParameterKind.POSITIONAL_ONLY)])


def _signify(func: FunctionType, n: int=inf)->(Signature, set):
    """
    n==inf implies automatic

    return a tuple of signature and setof positional only names.
    """

    params = inspect.signature(func).parameters

    sentinel = [i for (i, p) in enumerate(params.values())
                if (p.default is positionalonly)]
    if sentinel:
        n = sentinel[0]

    if n is inf:
        n = len([p for (p) in params.values() if (
            p.kind is POSITIONAL_OR_KEYWORD) and (p.default is _empty)])

    new_params = []
    posonly_params = dict()
    insertn = None
    for i, (name, param) in enumerate(inspect.signature(func).parameters.items()):
        if (i < n):
            np = Parameter(name, POSITIONAL_ONLY,
                           default=param.default, annotation=param.annotation)
            new_params.append(np)
            posonly_params[name] = i
        else:
            if param.default is positionalonly:
                if insertn:
                    raise ValueError(
                        'Cannot use sentinal value more than once')
                insertn = i
                continue
            new_params.append(param)
    sig = Signature(new_params)
    return sig, posonly_params, insertn


_od = defaultdict(lambda: 'th')
_od.update({1: 'st', 2: 'nd', 3: 'rd'})
# wrong around 11,12,13... but does it often happen ?
_ordinal = lambda x: str(x) + _od[x]


def _posonly(n, function):
    sig, posonly_names_pos, insertn = _signify(function, n)
    posonly_names = set(posonly_names_pos.keys())

    @wraps(function)
    def fun(*args, **kwargs):
        wrong = set(kwargs.keys()).intersection(posonly_names)

        if wrong:
            lst = ' - ' + '\n - '.join([
                repr(
                    w) + ' (%r) should be in %s position' % (kwargs[w], _ordinal(posonly_names_pos[w]))
                for w in wrong
            ])
            raise TypeError("The following parameters of `{}` are positional only.\n"
                            "They were used as keywords arguments:\n{}".format(function.__qualname__, lst))
        if insertn and len(args) >= insertn:
            args = args[:insertn] + (None,) + args[insertn:]
        return function(*args, **kwargs)

    fun.__signature__ = sig

    return fun
