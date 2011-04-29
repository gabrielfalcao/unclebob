# #!/usr/bin/env python
# -*- coding: utf-8 -*-
# <unclebob - django tool for running unit, functional and integration tests>
# Copyright (C) <2011>  Gabriel Falcão <gabriel@nacaolivre.org>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
import imp
import mock

from django.conf import settings
from django.core import management
from sure import that, that_with_context

from unclebob.runner import NoseTestRunner


def get_settings(obj):
    attrtuple = lambda x: (x, getattr(obj, x))
    normalattrs = lambda x: not x.startswith("_")
    return dict(map(attrtuple, filter(normalattrs, dir(obj))))


def prepare_stuff(context):
    context.runner = NoseTestRunner()
    context.old_settings = get_settings(settings)


def and_cleanup_the_mess(context):
    del context.runner
    original_settings = get_settings(context.old_settings)
    for attr in get_settings(settings):
        if attr not in original_settings:
            delattr(settings, attr)

    for attr, value in original_settings.items():
        setattr(settings, attr, value)


@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_nosetestrunner_should_have_some_basic_ignored_apps(context):
    u"NoseTestRunner should have some basic ignored apps"
    assert that(context.runner.get_ignored_apps()).equals([
        'unclebob',
        'south',
    ])


@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_get_ignored_apps_gets_extended_by_settings(context):
    u"should support extending the ignored apps through settings"
    settings.UNCLEBOB_IGNORED_APPS = ['foo', 'bar']
    assert that(context.runner.get_ignored_apps()).equals([
        'unclebob',
        'south',
        'foo',
        'bar',
    ])


@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_should_have_a_base_nose_argv(context):
    u"NoseTestRunner.get_nose_argv have a bases to start from"

    assert that(context.runner.get_nose_argv()).equals([
        'nosetests', '-s', '--verbosity=1', '--exe',
        '--nologcapture',
        '--cover-inclusive', '--cover-erase',
    ])


@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_should_allow_extending_base_argv_thru_settings(context):
    u"NoseTestRunner.get_nose_argv support extending base args thru settings"

    settings.UNCLEBOB_EXTRA_NOSE_ARGS = [
        '--cover-package="some_module"',
    ]
    assert that(context.runner.get_nose_argv()).equals([
        'nosetests', '-s', '--verbosity=1', '--exe',
        '--nologcapture',
        '--cover-inclusive', '--cover-erase',
        '--cover-package="some_module"',
    ])


@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_should_allow_extending_covered_packages(context):
    u"NoseTestRunner.get_nose_argv easily support extending covered packages"

    arguments = context.runner.get_nose_argv(covered_package_names=[
        'one_app',
        'otherapp',
    ])

    assert that(arguments).equals([
        'nosetests', '-s', '--verbosity=1', '--exe',
        '--nologcapture',
        '--cover-inclusive', '--cover-erase',
        '--cover-package="one_app"',
        '--cover-package="otherapp"',
    ])


@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_should_fetch_the_apps_names_thru_get_apps_method(context):
    u"NoseTestRunner.get_apps filters django builtin apps"
    settings.INSTALLED_APPS = (
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'foo',
        'bar',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
    )

    assert that(context.runner.get_apps()).equals([
        'foo',
        'bar',
    ])


@mock.patch.object(management, 'call_command')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_migrate_to_south_calls_migrate_if_properly_set(context, call_command):
    u"migrate_to_south_if_needed migrates on settings.SOUTH_TESTS_MIGRATE=True"

    settings.INSTALLED_APPS = (
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'south',
    )
    settings.SOUTH_TESTS_MIGRATE = True

    context.runner.migrate_to_south_if_needed()

    call_command.assert_called_once_with('migrate')


@mock.patch.object(management, 'call_command')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_doesnt_migrate_without_south_on_installed_apps(context, call_command):
    u"migrate_to_south_if_needed doesn't migrate is south is not installed"

    msg = "call_command('migrate') is being called even without " \
        "'south' on settings.INSTALLED_APPS"

    call_command.side_effect = AssertionError(msg)

    settings.INSTALLED_APPS = (
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
    )
    settings.SOUTH_TESTS_MIGRATE = True

    context.runner.migrate_to_south_if_needed()


@mock.patch.object(management, 'call_command')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_doesnt_migrate_without_south_tests_migrate(context, call_command):
    u"do not migrate if settings.SOUTH_TESTS_MIGRATE is False"

    msg = "call_command('migrate') is being called even with " \
        "settings.SOUTH_TESTS_MIGRATE=False"

    call_command.side_effect = AssertionError(msg)

    settings.INSTALLED_APPS = (
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'south',
    )
    settings.SOUTH_TESTS_MIGRATE = False

    context.runner.migrate_to_south_if_needed()


@mock.patch.object(imp, 'load_module')
@mock.patch.object(imp, 'find_module')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_get_paths_for_imports_the_module_and_returns_its_path(context,
                                                               find_module,
                                                               load_module):
    u"get_paths_for retrieves the module dirname"

    module_mock = mock.Mock()
    module_mock.__file__ = '/path/to/file.py'

    find_module.return_value = ('file', 'pathname', 'description')
    load_module.return_value = module_mock

    expected_path = context.runner.get_paths_for(['bazfoobar'])
    assert that(expected_path).equals(['/path/to'])

    find_module.assert_called_once_with('bazfoobar')
    load_module.assert_called_once_with(
        'bazfoobar', 'file', 'pathname', 'description',
    )


@mock.patch.object(imp, 'load_module')
@mock.patch.object(imp, 'find_module')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_get_paths_appends_more_paths(context, find_module, load_module):
    u"get_paths_for retrieves the module dirname and appends stuff"

    module_mock = mock.Mock()
    module_mock.__file__ = '/path/to/file.py'

    find_module.return_value = ('file', 'pathname', 'description')
    load_module.return_value = module_mock

    expected_path = context.runner.get_paths_for(
        ['bazfoobar'],
        appending=['one', 'more', 'place'],
    )
    assert that(expected_path).equals(['/path/to/one/more/place'])

    find_module.assert_called_once_with('bazfoobar')
    load_module.assert_called_once_with(
        'bazfoobar', 'file', 'pathname', 'description',
    )
