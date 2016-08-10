# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Partner hierarchy (Subsidiary)",
    "version": "1.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "license": 'AGPL-3',
    "category": "Partner",
    "description": """
        The module offers the following functionnalities:
            Define partner hierarchy and Subsidiary
            Define for each subsidiary its own contacts
            # TODO:
                Translate the module
                make the level definition dynamique and parametabel
                Add the levels columns on reports diplay partner column

Suggestions & Feedback to: samir.rachedi@smile.fr
    """,
    "depends": ['product'],
    "data": [
        # 'security/ir.model.access.csv',
        'views/res_partner_view.xml',
    ],
    "demo": [],
    "test": [],
    "installable": True,
    "certificate": '',
}
