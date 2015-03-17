# -*- coding: utf-8 -*-
##############################################################################
#
#    module for OpenERP, add dates for sale order
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
#                       author cyril.gaspard@smile.fr
#    Copyright (C) 2012 Zeekom ([http://www.zeekom.com/])
#              Bruno JOLIVEAU  + Cyril Gaspard <support@zeekom.com>
#    Copyright (C) 2009 Openerp (<http://www.openerp.com>) 
#    Copyright (c) 2009 Angel Alvarez - NaN  (http://www.nan-tic.com)
#
#    All Rights Reserved.
#
#    This module is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This module is is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see [http://www.gnu.org/licenses/].
#
##############################################################################
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from openerp.tools import ustr
import openerp.addons.decimal_precision as dp


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    def _get_public_price(self, cr, uid, ids, field_name, field_value,
                          arg, context=None):
        res = {}
        context = context or {}
        val = self.browse(cr, uid, ids, context=context)
        list_price = val and val[0].list_price or 0
        price_extra = val and val[0].price_extra or 0
#        price_margin = val and val[0].price_margin or 0
#        price = float(list_price) * float(price_margin) + float(price_extra)
        price = float(list_price) + float(price_extra)
        for id in ids:
            if val and price != val[0].public_price or val and not val[0].public_price:
                res[id] = price
        print "00000000000000000000000000", str(res)
        return res

    _columns = {
        'product_type_compo': fields.selection([('normal', _('Normal')), ('composed', _('Composed'))], 'Package Type'),
        'product_type_price_compo': fields.boolean('Sale Price Depends of its Components',
                                                   help="""if checked, price depends of its components"""),
        'pack_line_ids': fields.one2many('product.pack.line', 'parent_product_id', 'Pack Products',
                                         help='List of products that are part of this pack.'),
        'public_price': fields.function(_get_public_price,
                                        method=True, string='Sale Price',
                                        type='float',
                                        digits_compute=dp.get_precision('Product Price'),
                                        store=True,
                                        help="""Sale Price"""),
    }

    _defaults = {
        'product_type_compo': 'normal',
        'product_type_price_compo': True,
    }

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if vals.get('product_type_compo') == "composed" and vals.get('product_type_price_compo'):
            if not vals.get('pack_line_ids'):
                vals['list_price'] = 0
            else:
                vals['pack_line_ids'][-1][2]['calc_price'] = True
        print "1111111111111111111111111"
        return super(ProductProduct, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        print "22222222222222222222"
        context = context or {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        values = self.browse(cr, uid, ids, context=context)
        pack_obj = self.pool.get('product.pack.line')
        # if list price xor margin xor extra price are changed in a product type normal or composed and not product_type_price_compo,
        # update list price for products type "composed" and price depends of components where this product is a component
        product_type_compo = vals.get('product_type_compo') or (values and values[0].product_type_compo)
        no_price_compo = (vals.get('product_type_price_compo') is not None and
                          not vals.get('product_type_price_compo')) or (values and not values[0].product_type_price_compo) or True
        type_price = 'product_type_price_compo'
        price_compo = vals.get(type_price) or (vals.get(type_price) is None and (values and values[0].product_type_price_compo))
        if product_type_compo and price_compo and vals.get('pack_line_ids'):
            ### if write or create one or more pack line, line field calc_price is used to update list price just on time
            ### if delete one or more pack line, line context is used to update list price just one time
            i = 0
            j = None
            for pack in vals.get('pack_line_ids'):
                if pack[0] in [0, 1, 2]:
                    j = i
                i += 1
            if j is not None:
                if vals['pack_line_ids'][j][0] in [0, 1]:
                    vals['pack_line_ids'][j][2]['calc_price'] = True
                elif vals['pack_line_ids'][j][0] == 2:
                    context['calc_price'] = vals['pack_line_ids'][-1][1]
        if product_type_compo == "composed" and vals.get('product_type_price_compo'):
            line_ids = pack_obj.search(cr, uid, [('product_id', '=', ids[0])])
            if line_ids:
                val = ""
                for value in pack_obj.read(cr, uid, line_ids, ['parent_product_id'], context=context):
                    info = self.browse(cr, uid, value['parent_product_id'][0], context=context)
                    val += "[" + ustr(info.default_code) + "] " + ustr(info.name) + ", "
                raise osv.except_osv(_('Error!'), _("You can not change field\n\'Sale Price Depends of its Components\',\n"
                                                    "because this product is a component of some other products."
                                                    "\n product ids : '%s'.") % (val))
        product_normal = False
        if product_type_compo == "normal" or (product_type_compo == "composed" and no_price_compo):
            product_normal = True
#        vals_not_none = vals.get('list_price') is not None or vals.get('price_margin') is not None or vals.get('price_extra') is not None
        vals_not_none = vals.get('list_price') is not None or vals.get('price_extra') is not None
        if product_normal and vals_not_none:
            # get composed product list which have a component modified list price
            parent_list = []
            for product in sorted(set(pack_obj.search(cr, uid, [('product_id', '=', ids[0])], context=context))):
                pack_id = pack_obj.read(cr, uid, [product], ['parent_product_id'], context=context)[0]['parent_product_id'][0]
                test = self.read(cr, uid, [pack_id], ['product_type_compo', 'product_type_price_compo'],
                                 context=context)
                if pack_id and test and test[0]['product_type_compo'] == "composed" and test[0]['product_type_price_compo']:
                    parent_list.append(pack_id)
            # list price modification of composed product
            for parent_id in sorted(set(parent_list)):
                new_list_price = 0
                for line_id in pack_obj.search(cr, uid, [('parent_product_id', '=', parent_id)], context=context):
                    for product_infos in pack_obj.read(cr, uid, [line_id], ['product_id', 'quantity'], context=context):
                        product_id = product_infos.get('product_id', False)
                        # case pack line product_id = modified product
                        if product_id and product_id[0] == ids[0]:
                            price = values[0]['list_price'] or 0
#                            margin = values[0]['price_margin'] or 0
                            extra = values[0]['price_extra'] or 0
                            if vals.get('list_price') is not None:
                                price = vals.get('list_price') or 0
#                            if vals.get('price_margin') is not None:
#                                margin = vals.get('price_margin') or 0
                            if vals.get('price_extra') is not None:
                                extra = vals.get('price_extra') or 0
                        # other product_id
                        elif product_id:
#                            infos = self.read(cr, uid, [product_id[0]], ['list_price', 'price_margin', 'price_extra'], context=context)
                            infos = self.read(cr, uid, [product_id[0]], ['list_price', 'price_extra'], context=context)
                            price = infos[0].get('list_price') or 0
#                            margin = infos[0].get('price_margin') or 0
                            extra = infos[0].get('price_extra') or 0
                        if product_id:
                            quantity = product_infos.get('quantity') or 0
#                            new_list_price += (float(price) *
#                                               float(margin) +
#                                               float(extra)) * float(quantity)
                            new_list_price += (float(price) + float(extra)) * float(quantity)
                super(ProductProduct, self).write(cr, uid, [parent_id], {'list_price': new_list_price}, context=context)
        # exit if not a composed product after update list_price done or not done
        if vals and vals.get('product_type_compo', False) == "normal":
            return super(ProductProduct, self).write(cr, uid, ids, vals, context=context)
        # calc list_price when type pass from normal to composed and price depend of components or
        # product is type composed and pass from depend not of its components to depend of components
        # without creating or writting a new line
        type_compo = 'product_type_compo'
        type_price = 'product_type_price_compo'
        case_1 = vals.get(type_compo) == "composed" and vals.get(type_price) and vals.get(type_price) is not None
        case_2 = vals.get(type_compo) is None and values and values[0].product_type_compo == "composed" and vals.get(type_price)
        case_3 = vals.get(type_compo) == "composed" and vals.get(type_price) is None and values[0].product_type_price_compo
        if not vals.get('pack_line_ids') and (case_1 or case_2 or case_3):
            list_price = 0
            for pack_line in values[0].pack_line_ids:
                product_id = pack_line.product_id and pack_line.product_id.id or False
                quantity = pack_line.quantity or 0
                if product_id:
#                    infos = self.read(cr, uid, [product_id], ['list_price', 'price_margin', 'price_extra'], context=context)
#                    list_price += (float(infos and infos[0].get('list_price') or 0) *
#                                   float(infos and infos[0].get('price_margin') or 0) +
#                                   float(infos and infos[0].get('price_extra') or 0)) * float(quantity)
                    infos = self.read(cr, uid, [product_id], ['list_price', 'price_extra'], context=context)
                    list_price += (float(infos and infos[0].get('list_price') or 0) +
                                   float(infos and infos[0].get('price_extra') or 0)) * float(quantity)
            vals['list_price'] = list_price
        return super(ProductProduct, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        context = context or {}
        pack_obj = self.pool.get('product.pack.line')
        line_ids = pack_obj.search(cr, uid, [('product_id', '=', ids[0])], context=context)
        if line_ids:
            val = ""
            for value in pack_obj.read(cr, uid, line_ids, ['parent_product_id'], context=context):
                values = self.browse(cr, uid, value['parent_product_id'][0], context=context)
                val += "[" + ustr(values.default_code) + "] " + ustr(values.name) + ", "
            raise osv.except_osv(_('Error!'), _("You can not delete a product which is a component of one or more products."
                                                "\n product ids : '%s'.") % (val))
        res = super(ProductProduct, self).unlink(cr, uid, ids, context=context)
        return res


class ProductPackLine(orm.Model):
    _name = 'product.pack.line'
    _rec_name = 'product_id'
    _order = "product_id asc"

    _columns = {
        'parent_product_id': fields.many2one('product.product', 'Parent Product', required=True, ondelete='cascade'),
        'quantity': fields.float('Quantity', required=True),
        'product_id': fields.many2one('product.product', 'Product Composant Name', required=True, ondelete='cascade'),
        'list_price_compo': fields.related('product_id', 'public_price', type="float", string="Sale Price",
                                           digits_compute=dp.get_precision('Product Price')),
        'calc_price': fields.boolean('TO Write', help="if true, list price will be calculated (just one time)"),
        'sequence': fields.integer('Sequence', help="Gives the sequence order to display in sale order lines."),
    }

    _defaults = {
        'calc_price': False,
    }

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        # get price line unit
        prod_obj = self.pool.get('product.product')
        if vals.get('product_id', False):
#            product = prod_obj.read(cr, uid, [vals['product_id']], ['name', 'list_price', 'price_margin', 'price_extra',
#                                    'product_type_compo', 'product_type_price_compo'], context=context)
            product = prod_obj.read(cr, uid, [vals['product_id']], ['name', 'list_price', 'price_extra',
                                    'product_type_compo', 'product_type_price_compo'], context=context)
            if product and product[0].get('product_type_compo') == "composed" and product[0].get('product_type_price_compo'):
                raise osv.except_osv(_('Error!'), _("You can not add a component which is a composed product "
                                                    "which price depends of its components, named : '%s'."
                                                    ) % (ustr(product[0].get('name'))))
#            list_price_compo = (float((product and product[0].get('list_price'))
#                                or 0) * float((product and product[0].get('price_margin'))
#                                or 0)) + float((product and product[0].get('price_extra')) or 0)
            list_price_compo = float(product and product[0].get('list_price') or 0) + float(product and product[0].get('price_extra') or 0)
        if vals.get('parent_product_id', False) and vals.get('calc_price'):
            parent = prod_obj.read(cr, uid, [vals['parent_product_id']], ['product_type_compo',
                                   'product_type_price_compo'], context=context)
            # if True calc new parent product list_price
            if parent and parent[0]['product_type_compo'] == "composed" and parent[0]['product_type_price_compo']:
                parent_list_price = float(list_price_compo) * float(vals['quantity'] or 0)
                for line_ids in self.search(cr, uid, [('parent_product_id', '=', vals['parent_product_id'])]):
                    values = self.read(cr, uid, [line_ids], ['product_id', 'quantity'], context=context)
                    if 'product_id' in values[0]:
#                        infos = prod_obj.read(cr, uid, [values[0]['product_id'][0]], ['list_price', 'price_margin', 'price_extra'],
#                                              context=context)
#                        price_list = (float(infos and infos[0].get('list_price') or 0) *
#                                      float(infos and infos[0].get('price_margin') or 0) +
#                                      float(infos and infos[0].get('price_extra') or 0))
                        infos = prod_obj.read(cr, uid, [values[0]['product_id'][0]], ['list_price', 'price_extra'],
                                              context=context)
                        price_list = float(infos and infos[0].get('list_price') or 0) + \
                                     float(infos and infos[0].get('price_extra') or 0)
                        parent_list_price += float(price_list) * float(values[0].get('quantity') or 0)
                prod_obj.write(cr, uid, [vals['parent_product_id']], {'list_price': parent_list_price}, context=context)
            vals['calc_price'] = False
        return super(ProductPackLine, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        # get price line unit
        line = self.browse(cr, uid, ids, context=context)
        product_id = vals.get('product_id', False) or (line and line[0].product_id.id) or False
        if product_id:
            prod_obj = self.pool.get('product.product')
#            product = prod_obj.read(cr, uid, [product_id], ['name', 'list_price', 'price_margin', 'price_extra',
#                                    'product_type_price_compo'], context=context)
            product = prod_obj.read(cr, uid, [product_id], ['name', 'list_price', 'price_extra',
                                                            'product_type_price_compo'], context=context)
            if product and product[0].get('product_type_compo') == "composed" and product[0].get('product_type_price_compo'):
                raise osv.except_osv(_('Error!'), _("You can not add a component which is a composed product "
                                                    "which price depends of its components, named : '%s'."
                                                    ) % (ustr(product[0].get('name'))))
#            list_price_compo = (float(product[0].get('list_price') or 0) * float(product[0].get('price_margin') or 0)
#                                ) + float(product[0].get('price_extra') or 0)
            list_price_compo = float(product[0].get('list_price') or 0) + float(product[0].get('price_extra') or 0)
        parent_id = vals.get('parent_product_id', False) or (line and line[0].parent_product_id.id) or False
        # if True calc new parent product list_price
        if parent_id and vals.get('calc_price'):
            # we can't have a product composed by itself ...
            if parent_id == product_id:
                raise osv.except_osv(_('Error!'), _("You can not add a component which is the product itself, named : '%s'."
                                                    ) % (ustr(product[0].get('name'))))
            parent = prod_obj.read(cr, uid, [parent_id], ['product_type_compo', 'product_type_price_compo'], context=context)
            if parent and parent[0]['product_type_compo'] == "composed" and parent[0]['product_type_price_compo']:
                quantity = (line and line[0].quantity) or 0
                if vals.get('quantity') is not None:
                    quantity = vals.get('quantity') or 0
                parent_list_price = float(list_price_compo) * float(quantity)
                line_ids = self.search(cr, uid, [('parent_product_id', '=', parent_id)])
                if line_ids:
                    # get lines without current id (already calculated with new price)
                    line_other_ids = []
                    for line_id in line_ids:
                        if line_id != ids[0]:
                            line_other_ids.append(line_id)
                    for values in self.read(cr, uid, line_other_ids, ['product_id', 'quantity'], context=context):
                        if 'product_id' in values:
#                            infos = prod_obj.read(cr, uid, [values['product_id'][0]], ['list_price', 'price_margin', 'price_extra'],
#                                                  context=context)
#                            price_list = (float(infos and infos[0].get('list_price') or 0) *
#                                          float(infos and infos[0].get('price_margin') or 0) +
#                                          float(infos and infos[0].get('price_extra') or 0))
                            infos = prod_obj.read(cr, uid, [values['product_id'][0]], ['list_price', 'price_extra'],
                                                  context=context)
                            price_list = float(infos and infos[0].get('list_price') or 0) + \
                                         float(infos and infos[0].get('price_extra') or 0)
                            parent_list_price += float(price_list) * float(values.get('quantity') or 0)
                self.pool.get('product.product').write(cr, uid, [parent_id], {'list_price': parent_list_price}, context=context)
            vals['calc_price'] = False
        return super(ProductPackLine, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        context = context or {}
        line = self.read(cr, uid, [ids[0]], ['parent_product_id', 'product_id', 'quantity'], context=context)
        prod_obj = self.pool.get('product.product')
        parent = prod_obj.read(cr, uid, [line[0]['parent_product_id'][0]], ['product_type_compo', 'product_type_price_compo'],
                               context=context)
        type_compo = 'product_type_compo'
        type_price = 'product_type_price_compo'
        if parent and parent[0][type_compo] == "composed" and parent[0][type_price] and context.get('calc_price') == ids[0]:
            parent_list_price = 0
            for line_ids in self.search(cr, uid, [('parent_product_id', '=', line[0]['parent_product_id'][0])]):
                values = self.read(cr, uid, [line_ids], ['product_id', 'quantity'], context=context)
                if values and ('product_id' in values[0]) and ('id' in values[0]) and values[0]['id'] != ids[0]:
#                    infos = prod_obj.read(cr, uid, [values[0]['product_id'][0]], ['list_price', 'price_margin', 'price_extra'],
#                                          context=context)
#                    price_list = (float(infos and infos[0].get('list_price') or 0) *
#                                  float(infos and infos[0].get('price_margin') or 0) +
#                                  float(infos and infos[0].get('price_extra') or 0))
                    infos = prod_obj.read(cr, uid, [values[0]['product_id'][0]], ['list_price', 'price_extra'],
                                          context=context)
                    price_list = float(infos and infos[0].get('list_price') or 0) + \
                                  float(infos and infos[0].get('price_extra') or 0)
                    parent_list_price += float(price_list) * float(values[0].get('quantity') or 0)
            if line and line[0]['parent_product_id'][0]:
                prod_obj.write(cr, uid, [line[0]['parent_product_id'][0]], {'list_price': parent_list_price}, context=context)
            context['calc_price'] = False
        return super(ProductPackLine, self).unlink(cr, uid, ids, context=context)
