# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import csv
import base64
import cStringIO

from openerp import models, api, _, fields


class WizardUpload(models.TransientModel):
    _name = "wizard.upload"
    _description = "Wizard to upload a CSV file and fill XML model"

    def _get_csv2xml_converter(self):
        active_ids = self._context.get('active_ids', [])
        if active_ids:
            return active_ids[0]

    csv_file = fields.Binary(string='CSV File')

    csv2xml_converter_id = fields.Many2one('smile.csv2xml.converter', default=_get_csv2xml_converter)

    @api.multi
    def fillcsv(self):
        self.ensure_one()
        csv2xml_converter = self.csv2xml_converter_id
#         print self.csv_file
        listCSV = set([])
        listOBJ = set([])
#         print self.csv_file
        cr = base64.decodestring(self.csv_file)
#         print cr
        csv_input = cStringIO.StringIO(cr)
#         print csv_input
#         line1 = cr.next()
        csv_read = csv.reader(csv_input)
        print csv2xml_converter.id
        self.env['smile.csv2xml.converter'].browse(csv2xml_converter.id).write({'file_origin': self.csv_file})
        line = csv_read.next()
        for i in line:
            listCSV.add(i)
        for field in csv2xml_converter.object_id.field_id:
            listOBJ.add(field.name)
#         print listCSV
#         print listOBJ
        diff = listCSV - listOBJ
        if not diff:
            model_xml = "<record id='##?##' model='%s'>\n" % csv2xml_converter.object_id.model
            for field in csv2xml_converter.object_id.field_id:
                if (field.ttype == "function" or field.ttype == "related" or field.name == "id"):
                    model_xml += ""
                elif (field.ttype == "many2one"):
                    model_xml += "            <field name='%s' ref=\"##?##\"/>\n" % field.name
                elif (field.ttype == "many2many" or field.ttype == "one2many"):
                    model_xml += "            <field name='%s' eval=\"##6##\"/>\n" % field.name
                else:
                    model_xml += "            <field name='%s'>##?##</field>\n" % field.name
            model_xml += "</record>\n"
            csv2xml_converter.model_xml = model_xml
        else:
            raise Warning(_("Difference between CSV file and object"))
