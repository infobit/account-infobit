# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import api, fields, models


class estructure_tax_line(models.Model):
    _name = 'estructure.tax.line'
    
    management_id = fields.Many2one('management.fiscal.accounting.information', 'Management')
    ref = fields.Char('Reference')
    type = fields.Char('Type')
    comment = fields.Char('Comment')    
    line_type = fields.Selection(selection=[
        ('issued', 'Issued'),
        ('received', 'Received'),
        ('rectification_issued', 'Refund Issued'),
        ('rectification_received', 'Refund Received')],
        string='Line type')
    invoice_date = fields.Date(
        string='Invoice Date')
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Empresa')
    vat_number = fields.Char(
        string='NIF')
    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry')
    tax_id = fields.Many2one(comodel_name='account.tax', string='Tax')
    amount_untaxed = fields.Float('Amount untaxed')
    amount_tax = fields.Float('Amount tax')
    amount_refund_untaxed = fields.Float('Amount refund untaxed')
    amount_refund_tax = fields.Float('Amount refund tax')
    amount_total_untaxed = fields.Float('Amount total untaxed')
    amount_total_tax = fields.Float('Amount total tax')
    amount_total = fields.Float('Amount total')
