# positionnal only arguments/parameters

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

```
@positionalonly
def diff(left, right, context=3):
...
```

Usingit like will raise a TypeError, and the function
signature will use the positional only argument syntax
with the `/` of pep 497.

```
>>> diff(right="bar", left="foo")
TypeError: The following parameters of `diff` are positional only.
They were used as keywords arguments:
- 'right' ('bar') should be in 2nd position
- 'left' ('foo') should be in 1st position

>>> help(diff)
Help on function diff in module __main__:

diff(left, right, /, context=3)
```



# Advanced usage

By default `positionalonly` will make the limit between positional-only and the
rest of the arguments just before the first argument with default. You can
tweek this behavior by passing an integer as parameter indicating the number of
argument to make positional-only:

```
>>> @positionalonly(3)
... def diff(old, new, context=3)
... pass

>>> signature(diff)
diff(left, right, context=3, /)


>>> @positionalonly(1)
... def diff(old, new, context=3)
... pass

>>> signature(diff)
diff(left, /, right, context=3)
```

If you are too lazy to count, or are afraid of misscounting, `positionalonly`
will also decide to put the limit to the first argument which default value is
`positionalonly` itself.

```
>>> @positionalonly
... def diff(old, new, end=positionalonly, context=3)
... pass

>>> signature(diff)
diff(left, right, /, context=3)

>>> pos_or_kw
>>> @positionalonly
... def diff(old, start=pos_or_kw, context=3)
... pass

>>> signature(diff)
diff(left, /, right, context=3)
```



# Reasons to use positional only

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
