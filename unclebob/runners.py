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
import imp
import nose

from os import path as os_path
from os.path import dirname, join
from optparse import OptionParser

from django.conf import settings
from django.core import management
from django.test.simple import DjangoTestSuiteRunner

from unclebob.options import basic


def unique(lst):
    l = []
    for item in lst:
        if item not in l:
            l.append(item)
    return l


class Nose(DjangoTestSuiteRunner):
    IGNORED_APPS = ['unclebob', 'south']

    def get_setting_or_list(self, name):
        return getattr(settings, name, [])

    def get_ignored_apps(self):
        apps = self.IGNORED_APPS[:]
        apps.extend(self.get_setting_or_list('UNCLEBOB_IGNORED_APPS'))
        return apps

    def get_argv_options(self):
        parser = OptionParser()
        map(parser.add_option, basic)
        command = management.get_commands()['test']

        if isinstance(command, basestring):
            command = management.load_command_class('django.core', 'test')

        for opt in command.option_list:
            if opt.get_opt_string() not in (
                '--unit',
                '--functional',
                '--integration',
            ):
                parser.add_option(opt)

        (_options, _) = parser.parse_args()

        options = dict(
            is_unit=_options.is_unit,
            is_functional=_options.is_functional,
            is_integration=_options.is_integration,
        )
        return options

    def get_nose_argv(self, covered_package_names=None):
        packages_to_cover = covered_package_names or []

        args = [
            'nosetests', '-s',
            '--verbosity=%d' % int(self.verbosity),
            '--exe',
            '--logging-clear-handlers',
            '--cover-inclusive',
            '--cover-erase',
        ]
        args.extend(self.get_setting_or_list('UNCLEBOB_EXTRA_NOSE_ARGS'))

        def cover_these(package):
            return '--cover-package="%s"' % package

        def for_packages(package):
            try:
                imp.find_module(package)
                return True
            except ImportError:
                return False

        args.extend(map(cover_these, filter(for_packages, packages_to_cover)))
        return args

    def get_apps(self):
        IGNORED_APPS = self.get_ignored_apps()

        def not_builtin(name):
            return not name.startswith('django.')

        def not_ignored(name):
            return name not in IGNORED_APPS

        return filter(not_ignored,
                      filter(not_builtin, settings.INSTALLED_APPS))

    def get_paths_for(self, appnames, appending=None):
        paths = []

        for name in appnames:
            try:
                params = imp.find_module(name)
                module = imp.load_module(name, *params)
                module_filename = module.__file__
                module_path = dirname(module_filename)
            except ImportError:
                module_path = name
                if os_path.exists(module_path):
                    paths.append(module_path)

            appendees = []
            if isinstance(appending, (list, tuple)):
                appendees = appending

            path = join(os_path.abspath(module_path), *appendees)

            if os_path.exists(path):
                paths.append(path)

        return unique(paths)

    def migrate_to_south_if_needed(self):
        should_migrate = getattr(settings, 'SOUTH_TESTS_MIGRATE', False)
        if 'south' in settings.INSTALLED_APPS and should_migrate:
            print "Uncle Bob is running the database migrations..."
            management.call_command('migrate')

    def sip_some_bourbon(self):
        try:
            import bourbon
        except Exception:
            pass

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        # Pretend it's a production environment.
        settings.DEBUG = False
        os.environ['UNCLEBOB_RUNNING'] = os.getcwdu()

        app_names = test_labels or self.get_apps()
        nose_argv = self.get_nose_argv(covered_package_names=app_names)

        old_config = None

        options = self.get_argv_options()

        is_unit = options['is_unit']
        is_functional = options['is_functional']
        is_integration = options['is_integration']

        not_unitary = not is_unit or (is_functional or is_integration)
        specific_kind = is_unit or is_functional or is_integration

        apps = []

        for kind in ('unit', 'functional', 'integration'):
            if options['is_%s' % kind] is True:
                apps.extend(self.get_paths_for(app_names,
                                               appending=['tests', kind]))

        if not specific_kind:
            apps.extend(self.get_paths_for(app_names, appending=['tests']))

        nose_argv.extend(apps)

        eligible_for_test_db = not getattr(
            settings, 'UNCLEBOB_NO_DATABASE', False)

        if eligible_for_test_db and not_unitary:
            # eligible_for_test_db means the user did not set the
            # settings.UNCLEBOB_NO_DATABASE = True

            # and

            # not unitary means that should create a test database and
            # migrate if needed (support only south now)
            old_verbosity = self.verbosity
            self.verbosity = 0
            print "Uncle Bob is preparing the test database..."
            self.setup_test_environment()
            old_config = self.setup_databases()
            self.migrate_to_south_if_needed()
            self.verbosity = old_verbosity

        print "Uncle Bob will run the tests now..."

        self.sip_some_bourbon()  # loading the "bourbon.py" file
        passed = nose.run(argv=unique(nose_argv))

        if eligible_for_test_db and not_unitary:
            self.teardown_databases(old_config)
            self.teardown_test_environment()

        if passed:
            return 0
        else:
            return 1
