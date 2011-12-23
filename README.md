# unclebob
> Version 0.3.4

# What

UncleBob is a simple django app that allow you writting per-app tests within these paths:

* `<appname>/tests/unit/test*.py` - for unit tests
* `<appname>/tests/functional/test*.py` - for functional tests
* `<appname>/tests/integration/test*.py` - for integration tests

# installing

## first of all

    pip install unclebob

## add it to your django project

on settings.py

```python
INSTALLED_APPS = (
    ...
    'unclebob',
    ...
)

TEST_RUNNER = 'unclebob.runners.Nose
import unclebob
unclebob.take_care_of_my_tests()
```

# running

just use the regular **test** command:

    python manage.py test

## running only the unit tests

    python manage.py test --unit

## running only the functional tests

    python manage.py test --functional

## running only the integration tests

    python manage.py test --integration


## running only a specific path

    python manage.py test path/to/app/tests

or

    python manage.py test path/to/app/tests/unit

# warning:

if you run only the `unit` tests, then unclebob is NOT going to setup
the test database. Since
[unit tests](http://en.wikipedia.org/wiki/Unit_testing) are supposed
to be "unwired", what I mean is that unit tests MUST NOT make use of
actual database, filesystem or network at all.

Instead, they must test isolated parts of your code.

For that reason, sir, Uncle Bob is gonna break your neck in case you
decide to use those, so called, "external resources" in your unit
tests.

# although you can tell unclebob to never touch the database at all

in your `settings.py`

```python
UNCLEBOB_NO_DATABASE = True
```

# other aspects

## 1. it provides an environment variable, so that you'll know when unclebob is running

When unclebob is running tests, it sets the environment variable
 `UNCLEBOB_RUNNING` to the current working directory.

You can use it, for example, in your codebase fr avoiding logging
during the tests.

# Motivation

[nose](http://code.google.com/p/python-nose/) is such a really nice
tool for writting tests on python.

Instead of using the unittest framework, which is builtin python thou
is less fun to use.

And you know, the most joyable is the writting/running test
experience, more developers will write tests for the project. And as
much tests, better.

# Naming

This project was named after [Uncle Bob Martin](http://en.wikipedia.org/wiki/Robert_Cecil_Martin),
one of the [agile manifesto](http://agilemanifesto.org/) chaps that
brought code cleaness techniques and advices to the rest of us.
