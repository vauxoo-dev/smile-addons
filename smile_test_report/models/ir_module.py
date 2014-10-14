# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import os
import types
import yaml

from openerp import addons, api, models, modules
from openerp.tests.common import BaseCase

_logger = logging.getLogger(__package__)


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    @staticmethod
    def _get_yaml_test_files(module_name):
        """Returns the list of the paths indicated in 'test' of module manifest.
        
        @return: dict
        """
        test_files_by_module_path = {}
        if hasattr(addons, module_name):
            module = getattr(addons, module_name)
            module_path = module.__path__[0]
            file_path = os.path.join(module_path, '__openerp__.py')
            if not os.path.exists(file_path):
                _logger.error("No such file: %s", file_path)
            with open(file_path) as f:
                tests = eval(f.read()).get('test')
                if tests:
                    test_files_by_module_path[module_path] = tests
        return test_files_by_module_path

    @staticmethod
    def _get_yaml_test_comments(test_files):
        """Returns a list of tuple (basename of the file, path of the file, list of comments of the file).
        
        @return: list
        """
        res = []
        for module_path in test_files:
            module = os.path.basename(module_path)
            for file_path in test_files[module_path]:
                fp = os.path.join(module_path, file_path.replace('/', os.path.sep))
                if not os.path.exists(fp):
                    _logger.error("No such file: %s", fp)
                    continue
                with open(fp) as f_obj:
                    root, ext = os.path.splitext(f_obj.name)
                    if ext == '.yml':
                        comments = []
                        for node in yaml.load(f_obj.read()):
                            if isinstance(node, types.StringTypes):
                                comments.append(node)
                        res.append((os.path.basename(root), os.path.join(module, file_path), comments))
        return res

    @staticmethod
    def _get_unit_test_comments(module_name):
        """Returns a list of tuple (basename of the file, path of the file, list of comments of the file).
        
        @return: list
        """
        res = []

#         # Search module_name in addons_path
#         test_dir = False
#         for ad_path in modules.module.ad_paths:
#             test_dir_tmp = os.path.join(ad_path, module_name, 'tests')
#             if os.path.exists(test_dir_tmp):
#                 test_dir = test_dir_tmp
#         if not test_dir:
#             return res
#
#         # Parse docstring of test files
#         test_files = [name for name in os.listdir(test_dir)
#             if not os.path.isdir(os.path.join(test_dir, name)) and name.endswith('.py') and not name.startswith('__')]
#         for test_file in test_files:
#             root, ext = os.path.splitext(test_file)
#             module_import = __import__('openerp.addons.%s.tests' % module_name, fromlist=[str(root)])
#             for module_attr in [elt for elt in dir(module_import) if not elt.startswith('__')]:
#                 # In [28]: module_import.__getattribute__('TestReconciliation')
#                 # Out[28]: test_reconciliation.TestReconciliation
#                 #
#                 # In [29]: dir(module_import.__getattribute__('TestReconciliation'))
#
#                 if module_attr == 'fast_suite':
#                     continue  # TODO: remove
#
#                 for class_attr in [elt for elt in dir(module_import.__getattribute__(module_attr)) if not elt.startswith('__')]:
#                     import pdb;pdb.set_trace()
#
#                 if isinstance(module_attr, type) and issubclass(module_attr, BaseCase):  # is a test class
#                     comments = []
#                     comments.append(module_attr.__doc__)  # class docstring
#                     for class_attr in dir(module_attr):
#                         if callable(class_attr) and class_attr.startswith('test'):  # is a test method
#                             comments.append(class_attr.__doc__)  # method docstring
#                     res.append((module_attr, os.path.join(test_dir, test_file), comments))
        return res

    @api.multi
    def get_tests(self):
        """Returns the tests documentation of each module.
        
        @return: dict 
        """
        tests_by_module = {}
        for module in self:
            tests = []
            # YAML tests
            test_files = IrModuleModule._get_yaml_test_files(module.name)
            tests.extend(IrModuleModule._get_yaml_test_comments(test_files))
            # Unit tests
            tests.extend(IrModuleModule._get_unit_test_comments(module.name))
            if tests:
                # Add tests for this module
                tests_by_module[module.name] = tests
        return tests_by_module
