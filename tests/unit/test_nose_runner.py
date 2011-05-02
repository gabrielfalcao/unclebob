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
import os
import sys
import imp
import mock
import nose

from StringIO import StringIO
from django.conf import settings
from django.core import management
from sure import that, that_with_context

from unclebob.runners import Nose


def get_settings(obj):
    attrtuple = lambda x: (x, getattr(obj, x))
    normalattrs = lambda x: not x.startswith("_")
    return dict(map(attrtuple, filter(normalattrs, dir(obj))))


def prepare_stuff(context):
    context.runner = Nose()
    context.old_settings = get_settings(settings)
    context.options = {
        'is_unit': False,
        'is_functional': False,
        'is_integration': False,
    }
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    context.runner.get_argv_options = lambda: context.options


def and_cleanup_the_mess(context):
    del context.runner
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    original_settings = get_settings(context.old_settings)
    for attr in get_settings(settings):
        if attr not in original_settings:
            delattr(settings, attr)

    for attr, value in original_settings.items():
        setattr(settings, attr, value)


@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_nosetestrunner_should_have_some_basic_ignored_apps(context):
    u"Nose should have some basic ignored apps"
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
    u"Nose.get_nose_argv have a bases to start from"

    assert that(context.runner.get_nose_argv()).equals([
        'nosetests', '-s', '--verbosity=1', '--exe',
        '--nologcapture',
        '--cover-inclusive', '--cover-erase',
    ])


@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_should_allow_extending_base_argv_thru_settings(context):
    u"Nose.get_nose_argv support extending base args thru settings"

    settings.UNCLEBOB_EXTRA_NOSE_ARGS = [
        '--cover-package="some_module"',
    ]
    assert that(context.runner.get_nose_argv()).equals([
        'nosetests', '-s', '--verbosity=1', '--exe',
        '--nologcapture',
        '--cover-inclusive', '--cover-erase',
        '--cover-package="some_module"',
    ])


@mock.patch.object(imp, 'find_module')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_should_allow_extending_covered_packages(context, find_module):
    u"Nose.get_nose_argv easily support extending covered packages"

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
    assert that(find_module.call_args_list).equals([
        (('one_app',), {}),
        (('otherapp',), {}),
    ])

    find_module.assert_called_with('otherapp')


@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_should_fetch_the_apps_names_thru_get_apps_method(context):
    u"Nose.get_apps filters django builtin apps"
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


@mock.patch.object(os.path, 'exists')
@mock.patch.object(imp, 'load_module')
@mock.patch.object(imp, 'find_module')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_get_paths_for_imports_the_module_and_returns_its_path(context,
                                                               find_module,
                                                               load_module,
                                                               exists):
    u"get_paths_for retrieves the module dirname"

    module_mock = mock.Mock()
    module_mock.__file__ = '/path/to/file.py'

    find_module.return_value = ('file', 'pathname', 'description')
    load_module.return_value = module_mock
    exists.return_value = True

    expected_path = context.runner.get_paths_for(['bazfoobar'])
    assert that(expected_path).equals(['/path/to'])

    find_module.assert_called_once_with('bazfoobar')
    load_module.assert_called_once_with(
        'bazfoobar', 'file', 'pathname', 'description',
    )


@mock.patch.object(os.path, 'exists')
@mock.patch.object(imp, 'load_module')
@mock.patch.object(imp, 'find_module')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_get_paths_appends_more_paths(context, find_module, load_module,
                                      exists):
    u"get_paths_for retrieves the module dirname and appends stuff"

    module_mock = mock.Mock()
    module_mock.__file__ = '/path/to/file.py'

    find_module.return_value = ('file', 'pathname', 'description')
    load_module.return_value = module_mock
    exists.return_value = True

    expected_path = context.runner.get_paths_for(
        ['bazfoobar'],
        appending=['one', 'more', 'place'],
    )
    assert that(expected_path).equals(['/path/to/one/more/place'])

    find_module.assert_called_once_with('bazfoobar')
    load_module.assert_called_once_with(
        'bazfoobar', 'file', 'pathname', 'description',
    )


@mock.patch.object(os.path, 'exists')
@mock.patch.object(imp, 'load_module')
@mock.patch.object(imp, 'find_module')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_get_paths_ignore_paths_that_doesnt_exist(context,
                                                  find_module,
                                                  load_module,
                                                  exists):
    u"get_paths_for ignore paths that doesn't exist"

    module_mock = mock.Mock()
    module_mock.__file__ = '/path/to/file.py'

    find_module.return_value = ('file', 'pathname', 'description')
    load_module.return_value = module_mock
    exists.return_value = False

    expected_path = context.runner.get_paths_for(
        ['bazfoobar'],
        appending=['one', 'more', 'place'],
    )
    assert that(expected_path).equals([])

    find_module.assert_called_once_with('bazfoobar')
    load_module.assert_called_once_with(
        'bazfoobar', 'file', 'pathname', 'description',
    )


@mock.patch.object(nose, 'run')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_run_tests_simple_with_labels(context, nose_run):
    u"ability to run tests just with labels"

    context.runner.get_nose_argv = mock.Mock()
    context.runner.get_nose_argv.return_value = ['i', 'am', 'the', 'argv']

    context.runner.get_paths_for = mock.Mock()
    context.runner.get_paths_for.return_value = [
        '/path/to/app',
        '/and/another/4/labels',
    ]

    context.runner.setup_test_environment = mock.Mock()
    context.runner.teardown_test_environment = mock.Mock()

    context.runner.setup_databases = mock.Mock()
    context.runner.setup_databases.return_value = 'input 4 teardown databases'
    context.runner.teardown_databases = mock.Mock()

    context.runner.migrate_to_south_if_needed = mock.Mock()

    nose_run.return_value = 0
    context.runner.run_tests(['app', 'labels'], **context.options)

    context.runner.get_nose_argv.assert_called_once_with(
        covered_package_names=['app', 'labels'],
    )
    context.runner.get_paths_for.assert_called_once_with(
        ['app', 'labels'],
        appending=['tests'],
    )
    nose_run.assert_called_once_with(argv=[
        'i', 'am', 'the', 'argv',
        '/path/to/app',
        '/and/another/4/labels',
    ])
    context.runner.teardown_databases.assert_called_once_with(
        'input 4 teardown databases',
    )
    context.runner.migrate_to_south_if_needed.assert_called_once_with()


@mock.patch.object(nose, 'run')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_run_without_labels_gets_the_installed_apps(context, nose_run):
    u"ability to run tests without labels will look for INSTALLED_APPS"

    context.runner.get_apps = mock.Mock()
    context.runner.get_apps.return_value = ['app1', 'app_two']

    context.runner.get_nose_argv = mock.Mock()
    context.runner.get_nose_argv.return_value = ['i', 'am', 'the', 'argv']

    context.runner.get_paths_for = mock.Mock()
    context.runner.get_paths_for.return_value = [
        '/path/to/app1/tests',
        '/and/another/path/to/app_two/tests',
    ]

    context.runner.setup_test_environment = mock.Mock()
    context.runner.teardown_test_environment = mock.Mock()

    context.runner.setup_databases = mock.Mock()
    context.runner.setup_databases.return_value = 'input 4 teardown databases'
    context.runner.teardown_databases = mock.Mock()

    context.runner.migrate_to_south_if_needed = mock.Mock()

    nose_run.return_value = 0
    context.runner.run_tests([], **context.options)

    context.runner.get_nose_argv.assert_called_once_with(
        covered_package_names=['app1', 'app_two'],
    )
    context.runner.get_paths_for.assert_called_once_with(
        ['app1', 'app_two'],
        appending=['tests'],
    )
    nose_run.assert_called_once_with(argv=[
        'i', 'am', 'the', 'argv',
        '/path/to/app1/tests',
        '/and/another/path/to/app_two/tests',
    ])
    context.runner.teardown_databases.assert_called_once_with(
        'input 4 teardown databases',
    )
    context.runner.migrate_to_south_if_needed.assert_called_once_with()


@mock.patch.object(nose, 'run')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_when_nose_run_fails(context, nose_run):
    u"testing when the nose.run fails"

    context.runner.get_apps = mock.Mock()
    context.runner.get_apps.return_value = ['app1', 'app_two']

    context.runner.get_nose_argv = mock.Mock()
    context.runner.get_nose_argv.return_value = ['i', 'am', 'the', 'argv']

    context.runner.get_paths_for = mock.Mock()
    context.runner.get_paths_for.return_value = [
        '/path/to/app1/tests',
        '/and/another/path/to/app_two/tests',
    ]

    context.runner.setup_test_environment = mock.Mock()
    context.runner.teardown_test_environment = mock.Mock()

    context.runner.setup_databases = mock.Mock()
    context.runner.setup_databases.return_value = 'input 4 teardown databases'
    context.runner.teardown_databases = mock.Mock()

    context.runner.migrate_to_south_if_needed = mock.Mock()

    nose_run.return_value = 1
    context.runner.run_tests([], **context.options)

    context.runner.get_nose_argv.assert_called_once_with(
        covered_package_names=['app1', 'app_two'],
    )
    context.runner.get_paths_for.assert_called_once_with(
        ['app1', 'app_two'],
        appending=['tests'],
    )
    nose_run.assert_called_once_with(argv=[
        'i', 'am', 'the', 'argv',
        '/path/to/app1/tests',
        '/and/another/path/to/app_two/tests',
    ])
    context.runner.teardown_databases.assert_called_once_with(
        'input 4 teardown databases',
    )
    context.runner.migrate_to_south_if_needed.assert_called_once_with()


@mock.patch.object(nose, 'run')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_running_unit_tests_without_app_labels(context, nose_run):
    u"running with --unit without app labels won't touch the database at all"

    context.options['is_unit'] = True

    context.runner.get_apps = mock.Mock()
    context.runner.get_apps.return_value = ['john', 'doe']

    context.runner.get_nose_argv = mock.Mock()
    context.runner.get_nose_argv.return_value = ['nose', 'argv']

    context.runner.get_paths_for = mock.Mock()
    context.runner.get_paths_for.return_value = [
        '/apps/john/tests/unit',
        '/apps/doe/tests/unit',
    ]

    context.runner.setup_test_environment = mock.Mock()
    context.runner.teardown_test_environment = mock.Mock()

    context.runner.setup_databases = mock.Mock()
    context.runner.teardown_databases = mock.Mock()
    context.runner.migrate_to_south_if_needed = mock.Mock()

    nose_run.return_value = 0
    context.runner.run_tests([], **context.options)

    context.runner.get_nose_argv.assert_called_once_with(
        covered_package_names=['john', 'doe'],
    )
    context.runner.get_paths_for.assert_called_once_with(
        ['john', 'doe'],
        appending=['tests', 'unit'],
    )
    nose_run.assert_called_once_with(argv=[
        'nose', 'argv',
        '/apps/john/tests/unit',
        '/apps/doe/tests/unit',
    ])

    assert that(context.runner.setup_databases.call_count).equals(0)
    assert that(context.runner.teardown_databases.call_count).equals(0)
    assert that(context.runner.migrate_to_south_if_needed.call_count).equals(0)


@mock.patch.object(nose, 'run')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_running_unit_n_functional_without_labels(context, nose_run):
    u"if get --unit but also --functional then it should use a test database"

    context.options['is_unit'] = True
    context.options['is_functional'] = True

    context.runner.get_apps = mock.Mock()
    context.runner.get_apps.return_value = ['john', 'doe']

    context.runner.get_nose_argv = mock.Mock()
    context.runner.get_nose_argv.return_value = ['nose', 'argv']

    context.runner.get_paths_for = mock.Mock()

    expected_kinds = ['unit', 'functional']

    def mock_get_paths_for(names, appending):
        k = expected_kinds.pop(0)
        assert that(names).is_a(list)
        assert that(appending).is_a(list)
        assert that(names).equals(['john', 'doe'])
        assert that(appending).equals(['tests', k])
        return [
            '/apps/john/tests/%s' % k,
            '/apps/doe/tests/%s' % k,
        ]

    context.runner.get_paths_for.side_effect = mock_get_paths_for

    context.runner.setup_test_environment = mock.Mock()
    context.runner.teardown_test_environment = mock.Mock()

    context.runner.setup_databases = mock.Mock()
    context.runner.setup_databases.return_value = "TEST DB CONFIG"

    context.runner.teardown_databases = mock.Mock()
    context.runner.migrate_to_south_if_needed = mock.Mock()

    nose_run.return_value = 0
    context.runner.run_tests([], **context.options)

    context.runner.get_nose_argv.assert_called_once_with(
        covered_package_names=['john', 'doe'],
    )

    get_paths_for = context.runner.get_paths_for

    assert that(get_paths_for.call_count).equals(2)

    assert that(get_paths_for.call_args_list).equals([
        ((['john', 'doe'],), {'appending':['tests', 'unit']}),
        ((['john', 'doe'],), {'appending':['tests', 'functional']}),
    ])

    nose_run.assert_called_once_with(argv=[
        'nose', 'argv',
        '/apps/john/tests/unit',
        '/apps/doe/tests/unit',
        '/apps/john/tests/functional',
        '/apps/doe/tests/functional',
    ])

    context.runner.setup_databases.assert_called_once_with()
    context.runner.teardown_databases.assert_called_once_with("TEST DB CONFIG")
    context.runner.migrate_to_south_if_needed.assert_called_once_with()


@mock.patch.object(nose, 'run')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_running_unit_n_integration_without_labels(context, nose_run):
    u"if get --unit but also --integration then it should use a test database"

    context.options['is_unit'] = True
    context.options['is_integration'] = True

    context.runner.get_apps = mock.Mock()
    context.runner.get_apps.return_value = ['john', 'doe']

    context.runner.get_nose_argv = mock.Mock()
    context.runner.get_nose_argv.return_value = ['nose', 'argv']

    context.runner.get_paths_for = mock.Mock()

    expected_kinds = ['unit', 'integration']

    def mock_get_paths_for(names, appending):
        k = expected_kinds.pop(0)
        assert that(names).is_a(list)
        assert that(appending).is_a(list)
        assert that(names).equals(['john', 'doe'])
        assert that(appending).equals(['tests', k])
        return [
            '/apps/john/tests/%s' % k,
            '/apps/doe/tests/%s' % k,
        ]

    context.runner.get_paths_for.side_effect = mock_get_paths_for

    context.runner.setup_test_environment = mock.Mock()
    context.runner.teardown_test_environment = mock.Mock()

    context.runner.setup_databases = mock.Mock()
    context.runner.setup_databases.return_value = "TEST DB CONFIG"

    context.runner.teardown_databases = mock.Mock()
    context.runner.migrate_to_south_if_needed = mock.Mock()

    nose_run.return_value = 0
    context.runner.run_tests([], **context.options)

    context.runner.get_nose_argv.assert_called_once_with(
        covered_package_names=['john', 'doe'],
    )

    get_paths_for = context.runner.get_paths_for

    assert that(get_paths_for.call_count).equals(2)

    assert that(get_paths_for.call_args_list).equals([
        ((['john', 'doe'],), {'appending':['tests', 'unit']}),
        ((['john', 'doe'],), {'appending':['tests', 'integration']}),
    ])

    nose_run.assert_called_once_with(argv=[
        'nose', 'argv',
        '/apps/john/tests/unit',
        '/apps/doe/tests/unit',
        '/apps/john/tests/integration',
        '/apps/doe/tests/integration',
    ])

    context.runner.setup_databases.assert_called_once_with()
    context.runner.teardown_databases.assert_called_once_with("TEST DB CONFIG")
    context.runner.migrate_to_south_if_needed.assert_called_once_with()


@mock.patch.object(nose, 'run')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_running_unit_func_n_integration_without_labels(context, nose_run):
    u"if get --unit --functional and --integration"

    context.options['is_unit'] = True
    context.options['is_functional'] = True
    context.options['is_integration'] = True

    context.runner.get_apps = mock.Mock()
    context.runner.get_apps.return_value = ['john', 'doe']

    context.runner.get_nose_argv = mock.Mock()
    context.runner.get_nose_argv.return_value = ['nose', 'argv']

    context.runner.get_paths_for = mock.Mock()

    expected_kinds = ['unit', 'functional', 'integration']

    def mock_get_paths_for(names, appending):
        k = expected_kinds.pop(0)
        assert that(names).is_a(list)
        assert that(appending).is_a(list)
        assert that(names).equals(['john', 'doe'])
        assert that(appending).equals(['tests', k])
        return [
            '/apps/john/tests/%s' % k,
            '/apps/doe/tests/%s' % k,
        ]

    context.runner.get_paths_for.side_effect = mock_get_paths_for

    context.runner.setup_test_environment = mock.Mock()
    context.runner.teardown_test_environment = mock.Mock()

    context.runner.setup_databases = mock.Mock()
    context.runner.setup_databases.return_value = "TEST DB CONFIG"

    context.runner.teardown_databases = mock.Mock()
    context.runner.migrate_to_south_if_needed = mock.Mock()

    nose_run.return_value = 0
    context.runner.run_tests([], **context.options)

    context.runner.get_nose_argv.assert_called_once_with(
        covered_package_names=['john', 'doe'],
    )

    get_paths_for = context.runner.get_paths_for

    assert that(get_paths_for.call_count).equals(3)

    assert that(get_paths_for.call_args_list).equals([
        ((['john', 'doe'],), {'appending':['tests', 'unit']}),
        ((['john', 'doe'],), {'appending':['tests', 'functional']}),
        ((['john', 'doe'],), {'appending':['tests', 'integration']}),
    ])

    nose_run.assert_called_once_with(argv=[
        'nose', 'argv',
        '/apps/john/tests/unit',
        '/apps/doe/tests/unit',
        '/apps/john/tests/functional',
        '/apps/doe/tests/functional',
        '/apps/john/tests/integration',
        '/apps/doe/tests/integration',
    ])

    context.runner.setup_databases.assert_called_once_with()
    context.runner.teardown_databases.assert_called_once_with("TEST DB CONFIG")
    context.runner.migrate_to_south_if_needed.assert_called_once_with()


@mock.patch.object(os.path, 'exists')
@mock.patch.object(imp, 'load_module')
@mock.patch.object(imp, 'find_module')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_get_paths_for_accept_paths_as_parameter_checking_if_exists(
    context,
    find_module,
    load_module,
    exists):
    u"get_paths_for also takes paths, and check if exists"

    find_module.side_effect = ImportError('no module named /some/path')

    exists.side_effect = lambda x: x == '/path/to/file.py'

    expected_paths = context.runner.get_paths_for(
        ['/path/to/file.py'],
        appending=['more', 'members'],
    )

    assert that(expected_paths).equals(['/path/to/file.py'])

    find_module.assert_called_once_with('/path/to/file.py')
    assert that(load_module.call_count).equals(0)


@mock.patch.object(os.path, 'exists')
@mock.patch.object(imp, 'load_module')
@mock.patch.object(imp, 'find_module')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_get_paths_for_never_return_duplicates(
    context,
    find_module,
    load_module,
    exists):
    u"get_paths_for never return duplicates"

    module_mock = mock.Mock()
    module_mock.__file__ = '/path/to/file.py'

    find_module.return_value = ('file', 'pathname', 'description')
    load_module.return_value = module_mock

    exists.return_value = True

    expected_paths = context.runner.get_paths_for(
        ['/path/to/file.py', '/path/to/file.py'],
        appending=['more', 'members'],
    )

    assert that(expected_paths).equals(['/path/to/more/members'])


@mock.patch.object(nose, 'run')
@that_with_context(prepare_stuff, and_cleanup_the_mess)
def test_nose_is_called_with_unique_args(context, nose_run):
    u"testing when the nose.run fails"

    context.runner.get_apps = mock.Mock()
    context.runner.get_apps.return_value = ['app1', 'app_two']

    context.runner.get_nose_argv = mock.Mock()
    context.runner.get_nose_argv.return_value = ['repeated', 'repeated', 'repeated']

    context.runner.get_paths_for = mock.Mock()
    context.runner.get_paths_for.return_value = []

    context.runner.setup_test_environment = mock.Mock()
    context.runner.teardown_test_environment = mock.Mock()

    context.runner.setup_databases = mock.Mock()
    context.runner.setup_databases.return_value = 'input 4 teardown databases'
    context.runner.teardown_databases = mock.Mock()

    context.runner.migrate_to_south_if_needed = mock.Mock()

    nose_run.return_value = 0
    context.runner.run_tests([], **context.options)

    context.runner.get_nose_argv.assert_called_once_with(
        covered_package_names=['app1', 'app_two'],
    )
    context.runner.get_paths_for.assert_called_once_with(
        ['app1', 'app_two'],
        appending=['tests'],
    )
    nose_run.assert_called_once_with(argv=[
        'repeated',
    ])
    context.runner.teardown_databases.assert_called_once_with(
        'input 4 teardown databases',
    )
    context.runner.migrate_to_south_if_needed.assert_called_once_with()
