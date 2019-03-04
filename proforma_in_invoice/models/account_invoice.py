# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from werkzeug.urls import url_encode
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.addons import decimal_precision as dp

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    state = fields.Selection([
            ('draft','Draft'),
            ('proforma','Proforma'),
            ('open', 'Open'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    #montaje infobit
    @api.multi
    def action_proforma(self):
        #SEARCH JOURNAL IS PROFORMA
        jproforma = self.env['account.journal'].search([('is_proforma', '=', True)])
        if jproforma:
           self.write({'state': 'proforma', 'journal_id': jproforma[0].id})
        else:
           raise Warning('No exite diario para Proforma')
        return True

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    _order = "invoice_id,origin,sequence,id" #,layout_category_id"

