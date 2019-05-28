# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _prepare_payment_line_vals(self, payment_order):
        res = super(AccountMoveLine, self)._prepare_payment_line_vals(payment_order)
        if self.invoice_id.type in ('in_invoice', 'in_refund'):
           if self.invoice_id.reference:
              res['communication'] = 'Factura ' + self.invoice_id.reference
           else:
              res['communication'] = 'Factura ' + self.invoice_id.number
        else:
           res['communication'] = 'Factura ' + self.invoice_id.number
        return res

