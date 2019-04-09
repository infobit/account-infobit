# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Odoo Source Management Solution
#    Copyright (c) 2014 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

{
    'name': 'Modificación el campo status de facturas, para incorporar un nuevo estado Proforma',
    'version': '1.0',
    'category': '',
    'author': 'Infobit Informatica',
    'website': 'http://www.infobitinformatica.es',
    'depends': [
        'account', 'account_cancel'
    ],
    'description': """
Este modulo modifica el campo status, e incorpora un nuevo estado Proforma
    """,
    'data': [
      'views/invoice.xml',
      'views/journal.xml'
    ],
    "installable": True,
}
