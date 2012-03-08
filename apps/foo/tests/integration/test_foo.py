#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings


def test_foo_should_be_found():
    "tests under apps/foo/tests/integration/test*.py should be found"


def test_bourbon_is_loaded():
    "Making sure BOURBON is loaded"
    assert settings.BOURBON_LOADED_TIMES is 1, \
        'should be 1 but got %d' % settings.BOURBON_LOADED_TIMES
