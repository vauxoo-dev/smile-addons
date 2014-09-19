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

from openerp import api, fields, models, SUPERUSER_ID, tools, _
from openerp.exceptions import Warning
from openerp.modules.registry import Registry

from openerp.addons.smile_log.db_handler import SmileDBLogger

_logger = logging.getLogger(__package__)


class IrModelImpexTemplate(models.Model):
    _name = 'ir.model.impex.template'
    _description = 'Import/Export Template'

    name = fields.Char(size=64, required=True)
    type = fields.Selection([('export', 'Export'), ('import', 'Import')], required=True)
    model_id = fields.Many2one('ir.model', 'Object', required=True, ondelete='cascade')
    model = fields.Char(readonly=True, related='model_id.model', store=True)
    method = fields.Char(size=64, required=True)
    impex_ids = fields.One2many('ir.model.impex', 'impex_tmpl_id', 'Imports/Exports', readonly=True)
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'ir.model.impex.template')], readonly=True)
    cron_id = fields.Many2one('ir.cron', 'Scheduled Action')
    server_action_id = fields.Many2one('ir.actions.server', 'Server action')
    client_action_id = fields.Many2one('ir.values', 'Client Action')  # Only export

    # Only export
    filter_type = fields.Selection([('domain', 'Domain'), ('method', 'Method')], required=True, default='domain')
    filter_domain = fields.Char(size=256, default='[]')
    filter_method = fields.Char(size=64, help="signature: @api.model")
    limit = fields.Integer()
    max_offset = fields.Integer()
    order = fields.Char('Order by', size=64)
    unique = fields.Boolean(help="If unique, each instance is exported only once")
    force_execute_action = fields.Boolean('Force Action Execution', help="Even if there are no resources to export")

    @api.one
    def create_cron(self):
        if not self.cron_id:
            vals = {
                'name': self.name,
                'user_id': 1,
                'model': self._name,
                'function': 'create_impex',
                'args': '(%d, )' % self.id,
                'numbercall':-1,
            }
            cron_id = self.env['ir.cron'].create(vals)
            self.write({'cron_id': cron_id})
        return True

    @api.one
    def _get_server_action_vals(self, model_id):
        # TODO: check if 'active_ids' is not always in context
        return {
            'name': self.name,
            'user_id': SUPERUSER_ID,
            'model_id': model_id,
            'state': 'code',
            'code': "self.pool.get('ir.model.impex.template').create_impex(cr, uid, %d, context.get('active_ids'), context)" % (self.id,),
        }

    @api.one
    def create_server_action(self):
        if not self.server_action_id:
            model = self.env['ir.model'].search([('model', '=', self._name)], limit=1)
            if not model:  # Normally should not happen
                raise Warning(_('Please restart Odoo server'))
            vals = self._get_server_action_vals(model.id)
            if vals:
                self.server_action_id = self.env['ir.actions.server'].create(vals)
        return True

    @api.one
    def unlink_server_action(self):
        if self.client_action_id:
            raise Warning(_('Please remove client action before removing server action'))
        if self.server_action_id:
            self.server_action_id.unlink()
        return True

    @api.one
    def _get_client_action_vals(self):
        return {
            'name': self.name,
            'model_id': self.model_id.id,
            'model': self.model_id.model,
            'key2': 'client_action_multi',
            'value': 'ir.actions.server,%d' % self.server_action_id.id,
        }

    @api.one
    def create_client_action(self):
        if not self.client_action_id:
            if not self.server_action_id:
                self.create_server_action()
            vals = self._get_client_action_vals()
            self.client_action_id = self.env['ir.values'].create(vals)
        return True

    @api.one
    def unlink_client_action(self):
        if self.client_action_id:
            self.client_action_id.unlink()
            if self.server_action_id:
                self.server_action_id.unlink()
        return True

    @api.one
    def _get_res_ids(self, res_ids=None):
        model_obj = self.env[self.model_id.model]
        if self.filter_type == 'domain':
            domain = eval(self.domain or '[]')
            if res_ids:
                domain.append(('id', 'in', res_ids))
            res_ids = model_obj.search(domain, order=self.order or '')._ids
        else:  # elif self.filter_type == 'method':
            if not (self.filter_method and hasattr(model_obj, self.filter_method)):
                raise Warning(_("Can't find method: %s on object: %s") % (self.filter_method, self.model_id.model))
            res_ids2 = getattr(model_obj, self.filter_method)()
            res_ids = res_ids and list(set(res_ids) & set(res_ids2)) or res_ids2
        if self.unique:
            old_res_ids = sum([impex.resource_ids for impex in self.impex_id], [])
            res_ids = list(set(res_ids) - set(old_res_ids))
        return res_ids

    @api.one
    def _get_res_ids_offset(self, res_ids=None):
        """Get resources and split them in groups in function of limit and max_offset"""
        res_ids = self._get_res_ids(res_ids)
        if self.limit:
            res_ids_list = []
            i = 0
            while(res_ids[i: i + self.limit]):
                if self.max_offset and i == self.max_offset * self.limit:
                    break
                res_ids_list.append(res_ids[i: i + self.limit])
                i += self.limit
            return res_ids_list
        return [res_ids]

    @api.one
    @api.returns('self', lambda value: value.id)
    def create_impex(self, res_ids=None):
        try:
            impex_obj = self.pool.get('ir.model.impex')
            vals = {
                'impex_tmpl_id': self.id,
                'state': 'running',
                'test_mode': self._context.get('test_mode', False),
            }
            if self.type == 'export':
                impex_recs = impex_obj.browse()
                for index, res_ids_offset in enumerate(self._get_res_ids_offset(res_ids)):
                    vals['resource_ids'] = res_ids_offset
                    vals['offset'] = index + 1
                    impex_recs |= impex_obj.create(vals)
            else:
                impex_recs = impex_obj.create(vals)
            impex_recs.process()
            return impex_recs
        except Exception, e:
            tmpl_logger = SmileDBLogger(self._cr.dbname, 'ir.model.impex.template', self.id, self._uid)
            tmpl_logger.error(repr(e))
            raise


STATES = [
    ('running', 'Running'),
    ('done', 'Done'),
    ('exception', 'Exception'),
]


def state_cleaner(method):
    def state_cleaner(self, cr, module):
        res = method(self, cr, module)
        if self.get('ir.model.impex'):
            cr.execute("select relname from pg_class where relname='ir_model_impex'")
            if cr.rowcount:
                impex_ids = self.get('ir.model.impex').search(cr, 1, [('state', '=', 'running')])
                if impex_ids:
                    self.get('ir.model.impex').write(cr, 1, impex_ids, {'state': 'exception'})
        return res
    return state_cleaner


class IrModelImpex(models.Model):
    _name = 'ir.model.impex'
    _description = 'Import/Export'
    _rec_name = 'create_date'
    _order = 'create_date desc'

    def __init__(self, pool, cr):
        super(IrModelImpex, self).__init__(pool, cr)
        setattr(Registry, 'load', state_cleaner(getattr(Registry, 'load')))

    @api.one
    def _get_resources(self):
        # TODO: check if ok
        self.resource_ids = tools.safe_eval(self.resource_ids)

    @api.one
    def _set_resources(self, value):
        self.resource_ids = repr(value)

    @api.one
    def _get_resource_count(self):
        self.resource_count = len(self.resource_ids)

    impex_tmpl_id = fields.Many2one('ir.model.impex.template', 'Template', readonly=True, required=True, ondelete='cascade')
    create_date = fields.Datetime('Creation Date', readonly=True)
    create_uid = fields.Many2one('res.users', 'Creation User', readonly=True)
    from_date = fields.Datetime('Start date', readonly=True)
    to_date = fields.Datetime('End date', readonly=True)
    test_mode = fields.Boolean('Test Mode', readonly=True)
    log_ids = fields.One2many('smile.log', 'res_id', 'Logs', domain=[('model_name', '=', 'ir.model.impex')], readonly=True)
    state = fields.Selection(STATES, "State", readonly=True, required=True)
    resource_ids = fields.Text('Resources', compute='_get_resources', inverse='_set_resources', readonly=True, default='[]')
    resource_count = fields.Integer('Resources', compute='_get_resource_count')

    # Only export
    offset = fields.Integer()
