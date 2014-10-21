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


import csv
import base64

from openerp import models, fields, api


class SmileCsv2xmlConverter(models.Model):
    _name = "smile.csv2xml.converter"

    name = fields.Char("Name", required=True)
    object_id = fields.Many2one("ir.model", "Object", required=True)
    # file = fields.Binary()
    domain = fields.Char("Domain", default="[ ]", required=True)
    model_xml = fields.Text("Modele XML", required=True, default=" a ")
    xml_file = fields.Binary("xml file")
    file_origin = fields.Binary("file origin")

    @api.multi
    def fill(self):
        self.ensure_one()
        model_xml = "<record id='##?##' model='%s'>\n" % self.object_id.model
        for field in self.object_id.field_id:
            if (field.ttype == "function" or field.ttype == "related" or field.name == "id"):
                model_xml += ""
            elif (field.ttype == "many2one"):
                model_xml += "    <field name='%s' ref='##?##'/>\n" % field.name
            elif (field.ttype == "many2many" or field.ttype == "one2many"):
                model_xml += "    <field name='%s' eval='##6##'/>\n" % field.name
            else:
                model_xml += "    <field name='%s'>##?##</field>\n" % field.name
        model_xml += "</record>\n"
        self.model_xml = model_xml

#     def _get_csvfile(self):
#         active_ids = self._context.get('active_ids', [])
#         if active_ids:
#             return active_ids[0]
#
#     wizard_upload_id = fields.Many2one('wizard.upload', default=_get_csvfile)

    @api.multi
    def createXML(self):
        self.ensure_one()
        decoded = base64.decodestring(self.file_origin)
#         print decoded
#         decosplit = decoded[0].split('\n')
#         print decosplit
        newcsv = open("newcsv.csv", "w+")
        newcsv.write(decoded)
        newcsv.close()
        csv_read = csv.reader(open("newcsv.csv", 'rb'))
        rows = (csv.DictReader(open("newcsv.csv")))
#         csv_id = self.wizard_upload_id
#         csv_read = csv.reader(open(csv_id.csv_file))
#         rows = csv.DictReader(open(csv_id.csv_file))
        nbline = len(list(rows))
        currline = 0
        line = csv_read.next()
        xmlgenerated = "<?xml version='1.0' encoding='utf-8'?>\n"
        xmlgenerated += "<openerp>\n"
        xmlgenerated += "    <data>\n"
        while currline < nbline:
            line = csv_read.next()
#             print line
            model_xml = self.model_xml
            for i in line:
                isplitted = i.split(',')
                if len(isplitted) >= 2:
                    if "##6##" in model_xml:
                        tempxml6 = "[(6,0,[ref('%s')" % isplitted[0]
                        for i in range(1, len(isplitted)):
                            tempxml6 += ",ref('%s')" % isplitted[i]
                        tempxml6 += "])]"
                        model_xml = model_xml.replace('##6##', "%s", 1) % tempxml6
                    elif '##4##' in model_xml:
                        tempxml4 = "[(4,ref('%s'))" % isplitted[0]
                        for j in range(1, len(isplitted)):
                            tempxml4 += ",(4,ref('%s'))" % isplitted[j]
                        tempxml4 += "]"
                        model_xml = model_xml.replace('##4##', "%s", 1) % tempxml4
                else:
                    model_xml = model_xml.replace('##?##', i, 1)

            xmlgenerated += model_xml
            currline += 1
        xmlgenerated += "    </data>\n"
        xmlgenerated += "</openerp>"
        print xmlgenerated
        self.xml_file = base64.encodestring(xmlgenerated)
