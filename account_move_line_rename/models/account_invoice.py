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
      def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if not inv.invoice_number:
                sequence = inv.journal_id.invoice_sequence_id
                if inv.type in {'out_refund', 'in_refund'} and \
                        inv.journal_id.refund_inv_sequence_id:
                    sequence = inv.journal_id.refund_inv_sequence_id
                if sequence:
                    sequence = sequence.with_context(
                        ir_sequence_date=inv.date or inv.date_invoice,
                        ir_sequence_date_range=inv.date or inv.date_invoice,
                    )
                    number = sequence.next_by_id()
                else:  # pragma: no cover
                    # Other localizations or not configured journals
                    number = inv.move_id.name
                inv.write({
                    'number': number,
                    'invoice_number': number,
                })
            else:  # pragma: no cover
                inv.number = inv.invoice_number
        for inv in self:
            # Include the invoice reference on the created journal item
            # This is done for displaying the number on the conciliation
            inv.move_id.ref = (
                "{0} - {1}" if inv.move_id.ref else "{1}"
            ).format(inv.move_id.ref, inv.invoice_number)
            for lmov in inv.move_id.line_ids:
                if inv.type in ['out_invoice', 'out_refund']:
                   lmov.write({'name': 'Factura ' + inv.invoice_number})
                else:
                   lmov.write({'name': inv.reference})
        return res



      @api.multi
      def finalize_invoice_move_lines(self, move_lines):
        res = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        for move in move_lines:
            #raise Warning(move[2])
            invoice = self.env['account.invoice'].search([('id', '=', move[2]['invoice_id'])])
            if invoice:
               if invoice.type in ['out_invoice', 'out_refund'] and invoice.state not in ['draft']:
                  #raise Warning(invoice[0].invoice_number)
                  move[2]['name'] = 'Factura ' + invoice[0].invoice_number
               else:
                  move[2]['name'] = invoice[0].reference
            #move_lines2 = move
        #raise Warning(move_lines2)
        #raise Warning(move[2]['invoice_id'])
        #raise Warning(move_lines)
        #self.env['account.move.line'].write(move_lines,{})
        return move_lines



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

