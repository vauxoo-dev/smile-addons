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
{
    "name": "Smile Product Pack",
    "version": "1.0",
    "depends": ["product", "decimal_precision", "account", "sale"],
    "author": "Smile",
    "description": """
    What do this module:
    This module add possibility to add components to a product
    It is possible to choose if sale public price is calculated
    with sale public price of its components or not.
    Modules smile_product_variant_multi, smile_product_historical_variant
    (read dependencies for this modules), can be installed with this module or not.
    A product can add only as component, a product which is not a composed product
    or a composed product which has not price depending of its components.
    """,
    "website": "http://www.smile.fr",
    "category": "Generic Modules/Product",
    "sequence": 10,
    "data": [
            "security/product_security.xml",
            "security/ir.model.access.csv",
            "product_view.xml",
    ],
    "js": [
    ],
    "qweb": [
    ],
    "css": [
    ],
    "demo": [
    ],
    "test": [
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
