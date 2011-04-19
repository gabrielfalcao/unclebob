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
version = '0.1'

import os
import sys
import nose
from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner

project_module = __import__(settings.ROOT_URLCONF)
curdir = os.path.abspath(os.path.dirname(project_module.__file__))

class NoseTestRunner(DjangoTestSuiteRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        # Pretend it's a production environment.
        settings.DEBUG = False

        nose_argv = [
            'nosetests', '-s', '--verbosity=2', '--exe', '--with-coverage', '--cover-inclusive'
        ]
        package = os.path.split(os.path.dirname(__file__))[-1]
        app_names = [app for app in settings.INSTALLED_APPS if not app.startswith("django") and app != 'lettuce.django']

        nose_argv.extend(map(lambda name: "--cover-package=%s" % name, app_names))
        nose_argv.extend(map(lambda name: "--cover-package=%s.%s" % (package, name), app_names))

        # no logging, please
        nose_argv.append('--nologcapture')

        old_config = None

        # not unitary by default, which means, let's use the test
        # database and stuff...
        not_unitary = True

        if sys.argv[-1] in ('unit', 'functional', 'integration'):
            kind = sys.argv[-1]
            apps = map(lambda app: "%s/tests/%s" % (app, kind), app_names)
            not_unitary = kind != 'unit'

            if not_unitary:
                self.setup_test_environment()
                old_config = self.setup_databases()
        else:
            apps = app_names

        nose_argv.extend(apps)

        try:
            # cleaning coverage report, because unit and functional
            # targets could get confused in between test runs
            os.remove(os.path.join(curdir, '.coverage'))
        except:
            pass

        passed = nose.run(argv=nose_argv)

        if not_unitary and old_config is not None:
            self.teardown_databases(old_config)
            self.teardown_test_environment()

        if passed:
            return 0
        else:
            return 1
