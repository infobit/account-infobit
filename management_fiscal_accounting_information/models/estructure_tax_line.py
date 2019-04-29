# -*- coding: utf-8 -*-

from odoo import api, fields, models


class estructure_tax_line(models.Model):
    _name = 'estructure.tax.line'
    
    management_id = fields.Many2one('management.fiscal.accounting.information', 'Management')
    group_id = fields.Many2one('type.taxes.information', 'Type taxes information')
    account_group_id = fields.Many2one('account.group', 'Account Group')
    account_id = fields.Many2one('account.account', 'Account')
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
    year = fields.Integer('Year')
    month = fields.Integer('Month')
