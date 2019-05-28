# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.addons import decimal_precision as dp

class AccountStatementLineCreate(models.TransientModel):
    _inherit ="account.statement.line.create"

    paymentorder_id = fields.Many2one(
        'account.payment.order', string='Remesa')

    @api.multi
    def _prepare_move_line_domain(self):
        res = super(AccountStatementLineCreate, self)._prepare_move_line_domain()
        domain = res
        if self.paymentorder_id:
            lpayment = self.env['account.payment.line'].search([('order_id', '=', self.paymentorder_id.id)])
            lpnum = []
            for lp in lpayment:
                if lp.move_line_id:
                   lpnum.append(lp.move_line_id.id)
            if lpnum:
               #raise Warning(lpnum)
               domain += [('id', 'in', lpnum)]
        #raise Warning(res)
        return domain

    """@api.multi
    def populate(self):
        res = super(AccountStatementLineCreate, self).populate()
        domain = self._prepare_move_line_domain()
        lines = self.env['account.move.line'].search(domain)
        line = lines[0].payment_line_ids
        raise Warning(domain)
        return res"""
