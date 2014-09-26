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

import inspect

from openerp import api, fields, models, SUPERUSER_ID, tools

from action_rule_decorator import action_rule_decorator


class ActionRule(models.Model):
    _inherit = 'base.action.rule'

    @api.model
    def _get_kinds(self):
        return [
            ('on_create', 'On Creation'),
            ('on_write', 'On Update'),
            ('on_create_or_write', 'On Creation & Update'),
            ('on_unlink', 'On Deletion'),
            ('on_other_method', 'On Other Method'),
            ('on_time', 'Based on Timed Condition'),
        ]

    kind = fields.Selection('_get_kinds', 'When to Run'),
    method_id = fields.Many2one('ir.model.methods', 'Method')

    @api.multi
    def _store_model_methods(self, model_id):
        obj = self.env[self.env['ir.model'].browse(model_id).model]
        method_names = [attr for attr in dir(obj) if inspect.ismethod(getattr(obj, attr))]
        method_obj = self.env['ir.model.methods']
        existing_method_names = ['create', 'write', 'unlink']
        existing_method_names += [m['name'] for m in method_obj.search_read([('model_id', '=', model_id),
                                                                             ('name', 'in', method_names)], ['name'])]
        for method_name in method_names:
            if method_name in existing_method_names or method_name.startswith('__'):
                continue
            method = getattr(obj, method_name)
            if hasattr(method, '_api') and '_id' not in str(method._api):
                continue
            method_args = inspect.getargspec(method)[0]
            if not hasattr(method, '_api') and 'ids' not in method_args and 'id' not in method_args:
                continue
            method_obj.create({'name': method_name, 'model_id': model_id})

    def onchange_model_id(self, cr, uid, ids, model_id, context=None):
        res = super(ActionRule, self).onchange_model_id(cr, uid, ids, model_id, context)
        if model_id:
            self.browse(cr, uid, ids, context)._store_model_methods(model_id)
        return res

    def onchange_kind(self, cr, uid, ids, kind, context=None):
        clear_fields = []
        if kind in ['on_create', 'on_create_or_write']:
            clear_fields = ['filter_pre_id', 'trg_date_id', 'trg_date_range', 'trg_date_range_type']
        elif kind in ['on_write', 'on_other_method']:
            clear_fields = ['trg_date_id', 'trg_date_range', 'trg_date_range_type']
        elif kind == 'on_time':
            clear_fields = ['filter_pre_id']
        elif kind == 'on_unlink':
            clear_fields = ['filter_id', 'trg_date_id', 'trg_date_range', 'trg_date_range_type']
        return {'value': dict.fromkeys(clear_fields, False)}

    def _filter(self, cr, uid, rule, filter, record_ids, context=None):
        # Allow to compare with other fields of object (in third item of a condition)
        if record_ids and filter and filter.action_rule:
            assert rule.model == filter.model_id, "Filter model different from action rule model"
            model = self.pool[filter.model_id]
            domain = filter._eval_domain(record_ids)
            domain.insert(0, ('id', 'in', record_ids))
            ctx = dict(context or {})
            ctx.update(eval(filter.context))
            return model.search(cr, uid, domain, context=ctx)
        return super(ActionRule, self)._filter(cr, uid, rule, filter, record_ids, context)

    def _process(self, cr, uid, rule, record_ids, context=None):
        # Force action execution even if records list is empty
        if not record_ids and rule.server_action_ids:
            action_server_obj = self.pool.get('ir.actions.server')
            ctx = dict(context, active_model=rule.model_id._name, active_ids=[], active_id=False)
            action_server_obj.run(cr, uid, server_action_ids, context=ctx)
            return True
        return super(ActionRule, self)._process(cr, uid, rule, record_ids, context)

    @api.multi
    def _get_method_names(self):
        assert len(ids) == 1, 'ids must be a list with only one item!'
        if self.kind == 'on_time':
            return []
        if self.kind == 'on_other_method' and self.method_id:
            return (self.method_id.name,)
        elif self.kind == 'on_create_or_write':
            return ('create', 'write')
        return (self.kind.replace('on_', ''),)

    def _register_hook(self, cr, ids=None):
        # Trigger on any method
        updated = False
        if not ids:
            ids = self.search(cr, SUPERUSER_ID, [])
        for rule in self.browse(cr, SUPERUSER_ID, ids):
            method_names = rule._get_method_names()
            model_obj = self.pool[rule.model_id.model]
            for method_name in method_names:
                method = getattr(model_obj, method_name)
                check = True
                while check:
                    if method.__name__ == 'action_rule_wrapper':
                        break
                    if not hasattr(method, 'origin'):
                        check = False
                    method = method.origin
                else:
                    decorated_method = action_rule_decorator(getattr(model_obj, method_name))
                    model_obj._patch_method(method_name, decorated_method)
                    updated = True
        if updated:
            self.clear_caches()
        return updated

    @staticmethod
    def _get_method_name(method):
        while True:
            if not hasattr(method, 'origin'):
                break
            method = method.origin
        return method.__name__

    @tools.cache(skiparg=3)
    @api.cr_uid
    def _get_action_rules_by_method(self):
        res = {}
        for rule in self.sudo().search([]):
            if rule.kind == 'on_time':
                continue
            if rule.kind in ('on_create', 'on_create_or_write'):
                res.setdefault('create', []).append(rule)
            if rule.kind in ('on_write', 'on_create_or_write'):
                res.setdefault('write', []).append(rule)
            elif rule.kind == 'on_unlink':
                res.setdefault('unlink', []).append(rule)
            elif rule.kind == 'on_other_method':
                res.setdefault(rule.method_id.name, []).append(rule)
        return res

    @api.model
    def _get_action_rules(self, method):
        method_name = ActionRule._get_method_name(method)
        return self._get_action_rules_by_method().get(method_name, [])
