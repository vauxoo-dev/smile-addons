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

_logger = logging.getLogger(__package__)


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    @staticmethod
    def _get_test_files(module_name, test_directory):
        test_files_by_module_path = {}
        if hasattr(addons, module_name):
            module = getattr(addons, module_name)
            module_path = module.__path__[0]
            file_path = os.path.join(module_path, '__openerp__.py')
            if not os.path.exists(file_path):
                _logger.error("No such file: %s", file_path)
            with open(file_path) as f:
                tests = eval(f.read()).get(test_directory)
                if tests:
                    test_files_by_module_path[module_path] = tests
        return test_files_by_module_path

    @staticmethod
    def _get_yaml_test_comments(test_files):
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
    def _get_unit_test_comments(test_files, dbname):
        res = []
        for module_path in test_files:
            module = os.path.basename(module_path)
            modules.module.run_unit_tests(module, dbname)
            # TODO: get test informations
        return res

    @api.multi
    def get_yaml_tests(self):
        tests_by_module = {}
        for module in self:
            test_files = IrModuleModule._get_test_files(module.name, 'test')
            tests_by_module[module.name] = IrModuleModule._get_yaml_test_comments(test_files)
        return tests_by_module

    @api.multi
    def get_unit_tests(self):
        tests_by_module = {}
        for module in self:
            test_files = IrModuleModule._get_test_files(module.name, 'tests')
            tests_by_module[module.name] = IrModuleModule._get_unit_test_comments(test_files, self._cr.dbname)
        return tests_by_module
