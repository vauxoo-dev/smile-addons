# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Script Execution",
    "version": "1.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "category": "Tools",
    "license": 'AGPL-3',
    "description": """
Features

    * Log scripts run on the database

Suggestions & Feedback to: xavier.fernandez@smile.fr, corentin.pouhet-brunerie@smile.fr
    """,
    "depends": ['smile_log'],
    "data": [
        "security/smile_script_security.xml",
        "security/ir.model.access.csv",
        "views/script_view.xml",
    ],
    "installable": True,
}
