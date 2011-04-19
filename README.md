# unclebob
> Version 0.1

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

    INSTALLED_APPS = (
        ...
        'unclebob',
        ...
    )

    TEST_RUNNER = 'unclebob.NoseTestRunner'

# running

just use the regular **test** command:

    python manage.py test

## running only the unit tests

    python manage.py unit

## running only the functional tests

    python manage.py functional

## running only the integration tests

    python manage.py integration


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

# Motivation

[nose](http://code.google.com/p/python-nose/) is such a really nice
tool for writting tests on python.

Instead of using the unittest framework, which is builtin python thou
is less fun to use.

And you know, the most joyable is the writting/running test
experience, more developers will write tests for the project. And as
much tests, better.

# Naming

This project is a tribute to
[Uncle Bob Martin](http://en.wikipedia.org/wiki/Robert_Cecil_Martin),
one of the [agile manifesto](http://agilemanifesto.org/) chaps that
brought code cleaness techniques and advices to us.


