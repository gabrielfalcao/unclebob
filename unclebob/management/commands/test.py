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

import sys
from optparse import make_option
from django.conf import settings
from django.core.management.commands import test
from django.core.management import call_command


try:
    from south.management.commands import patch_for_test_db_setup
    USE_SOUTH = getattr(settings, "SOUTH_TESTS_MIGRATE", True)
except:
    USE_SOUTH = False


def add_option(kind):
    msg = 'Look for {0} tests on appname/tests/{0}/*test*.py'
    return make_option(
        '--%s' % kind, action='store_true',
        dest='is_%s' % kind, default=True,
        help=msg.format(kind))


class Command(test.Command):
    option_list = test.Command.option_list + (
        add_option('unit'),
        add_option('functional'),
        add_option('integration'),
    )

    def handle(self, *test_labels, **options):
        from django.conf import settings
        from django.test.utils import get_runner

        verbosity = int(options.get('verbosity', 1))
        interactive = options.get('interactive', True)
        failfast = options.get('failfast', False)

        TestRunner = get_runner(settings)

        if USE_SOUTH:
            patch_for_test_db_setup()
            call_command('migrate', interactive=False, verbosity=0)

        test_runner = TestRunner(
            verbosity=verbosity,
            interactive=interactive,
            failfast=failfast,
        )

        failures = test_runner.run_tests(test_labels, **options)
        if failures:
            sys.exit(bool(failures))
