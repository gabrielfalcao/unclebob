# #!/usr/bin/env python
# -*- coding: utf-8 -*-
# <unclebob - django tool for running tests organized between unit, functional and integration>
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
import sys
import nose
from os.path import dirname, abspath, join, split, exists

from unclebob.version import version

def get_module_dirname(module_name, *paths_to_join):
    module = __import__(module_name)
    return join(abspath(dirname(module.__file__)), *paths_to_join)
try:

    from django.conf import settings
    from django.test.simple import DjangoTestSuiteRunner
    from django.core.management import call_command

    class NoseTestRunner(DjangoTestSuiteRunner):
        def run_tests(self, test_labels, extra_tests=None, **kwargs):
            # Pretend it's a production environment.
            settings.DEBUG = False

            IGNORED_APPS = ['unclebob', 'south']
            IGNORED_APPS.extend(getattr(settings, 'UNCLEBOB_IGNORED_APPS', []))

            nose_argv = [
                'nosetests', '-s', '--verbosity=%d' % self.verbosity, '--exe',
                '--cover-inclusive', '--cover-erase',
            ]
            nose_argv.extend(getattr(settings, 'UNCLEBOB_EXTRA_NOSE_ARGS', []))
            package = split(dirname(__file__))[-1]
            app_names = test_labels or [app for app in settings.INSTALLED_APPS \
                         if not app.startswith("django.") and app not in IGNORED_APPS]

            nose_argv.extend(map(lambda name: "--cover-package=%s" % name, app_names))
            nose_argv.extend(map(lambda name: "--cover-package=%s.%s" % (package, name), app_names))

            # no logging, please
            nose_argv.append('--nologcapture')

            old_config = None

            # not unitary by default, which means, let's use the test
            # database and stuff...
            not_unitary = '--unit' not in sys.argv
            specific_kind = False

            for kind in ('--unit', '--functional', '--integration'):
                if kind in sys.argv:
                    apps = map(lambda app: get_module_dirname(app, "tests", kind), app_names)
                    specific_kind = True
                    break

            if not specific_kind:
                apps = map(lambda app: get_module_dirname(app, "tests"), app_names)

            apps = filter(exists, apps)
            nose_argv.extend(apps)

            if not_unitary:
                self.setup_test_environment()
                old_config = self.setup_databases()
                migrate = getattr(settings, 'SOUTH_TESTS_MIGRATE', False)
                if 'south' in settings.INSTALLED_APPS and migrate:
                    call_command('migrate')
            passed = nose.run(argv=nose_argv)

            if not_unitary:
                self.teardown_databases(old_config)
                self.teardown_test_environment()

            if passed:
                return 0
            else:
                return 1
except ImportError, e:
    # not in django
    pass
