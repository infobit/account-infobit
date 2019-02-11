# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
#from openerp.osv import orm, fields
#from openerp import models, fields, api, _
from datetime import datetime, timedelta
import time
#from openerp import SUPERUSER_ID
from openerp import fields, models, api
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import openerp.addons.decimal_precision as dp

class AccountInvoice(models.Model):
      _inherit = 'account.invoice'

      @api.multi
      def finalize_invoice_move_lines(self, move_lines):
        res = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        for move in move_lines:
            #raise Warning(move[2])
            invoice = self.env['account.invoice'].search([('id', '=', move[2]['invoice_id'])])
            if invoice:
               if invoice.type in ['out_invoice', 'out_refund']:
                  #raise Warning(move_lines)
                  move[2]['name'] = 'Factura ' + invoice[0].name
               else:
                  move[2]['name'] = invoice[0].reference
            #move_lines2 = move
        #raise Warning(move_lines2)
        #raise Warning(move[2]['invoice_id'])
        #raise Warning(move_lines)
        #self.env['account.move.line'].write(move_lines,{})
        return move_lines



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

