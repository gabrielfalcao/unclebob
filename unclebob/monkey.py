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
from functools import wraps
from unclebob.options import basic
from django.core import management
from django.utils.importlib import import_module

TEST_COMMAND_NAME = 'test'

def patch():
    "monkey patches the django test command"
    def patch_get_commands(get_commands):
        @wraps(get_commands)
        def the_patched(*args, **kw):
            res = get_commands(*args, **kw)
            test_command = res.get('test', None)
            if test_command is None:
                return res
            new_options = basic[:]
            module_location = '{0}.management.commands.{1}'.format(
                                            test_command, TEST_COMMAND_NAME)
            module = import_module(module_location)
            test_command_class = module.Command
            ignored_opts = ('--unit', '--functional', '--integration')
            for opt in test_command_class.option_list:
                if opt.get_opt_string() not in ignored_opts:
                    new_options.insert(0, opt)

            test_command_class.option_list = tuple(new_options)
            return res

        return the_patched

    management.get_commands = patch_get_commands(management.get_commands)

